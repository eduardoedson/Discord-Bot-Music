# -*- coding: utf-8 -*-

import asyncio
from typing import List
import discord
from discord import app_commands
from discord.utils import utcnow
from .player import MusicPlayer, Track, fmt_duration
from .extractor import extract_track


def register_commands(bot: discord.Client):
    # Helper to get/create a per-guild MusicPlayer
    def get_player(guild: discord.Guild) -> MusicPlayer:
        if not hasattr(bot, "_players"):
            setattr(bot, "_players", {})
        players = getattr(bot, "_players")
        if guild.id not in players:
            players[guild.id] = MusicPlayer(bot, guild)
        return players[guild.id]

    def build_now_playing_embed(track: Track) -> discord.Embed:
        """
        Build a 'Now playing' embed (visual style requested):
        - Title (clickable to the original page)
        - Static progress line: 0:00 | 🔵──── | DURATION
        - Fields: Autor (uploader), Source, Duração
        - Image (thumbnail)
        - Footer with timestamp + who added the track
        """
        dur = fmt_duration(track.duration)
        progress_line = f"0:00  | 🔵──────────────────────── | {dur}"
        title = track.title

        emb = discord.Embed(
            title=title,
            url=track.webpage_url,
            description=progress_line,
            color=discord.Color.green(),
            timestamp=utcnow(),  # footer datetime
        )
        emb.add_field(name="Autor", value=track.uploader or "Desconhecido", inline=True)
        emb.add_field(name="Source", value=track.source or "youtube", inline=True)
        emb.add_field(name="Duração", value=dur, inline=True)

        if track.thumbnail:
            emb.set_image(url=track.thumbnail)

        # Footer: show who added it
        emb.set_footer(text=f"Adicionado por {track.requester.display_name}")
        return emb

    @bot.tree.command(name="join", description="Entrar no seu canal de voz.")
    async def join(interaction: discord.Interaction):
        member = interaction.user
        if not isinstance(member, discord.Member) or not member.voice or not member.voice.channel:
            return await interaction.response.send_message("⚠️ Você precisa estar em um canal de voz.", ephemeral=True)
        player = get_player(interaction.guild)
        await player.ensure_connected(member.voice.channel)
        await player.start()
        await interaction.response.send_message(f"✅ Entrei em **{member.voice.channel.name}**.")

    @bot.tree.command(name="play", description="Toca uma música do YouTube pelo nome ou URL.")
    @app_commands.describe(query="Nome da música ou URL do YouTube")
    async def play(interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)
        member = interaction.user
        if not isinstance(member, discord.Member) or not member.voice or not member.voice.channel:
            return await interaction.followup.send("⚠️ Você precisa estar em um canal de voz.")

        player = get_player(interaction.guild)

        # Auto-join the caller's voice channel and ensure the loop is running
        await player.ensure_connected(member.voice.channel)
        await player.start()

        try:
            track = await extract_track(query, requester=member)
        except Exception as e:
            return await interaction.followup.send(f"❌ Falha ao obter o áudio: `{e}`")

        # Cancel any pending auto-disconnect due to new activity
        await player._cancel_auto_disconnect()

        # If idle (nothing playing and no current), it will start immediately
        idle_now = not (player.voice_client and player.voice_client.is_playing()) and player.current is None

        # Enqueue the track
        await player.queue.put(track)
        posicao = player.queue.qsize()

        # Send localized (Portuguese) messages to Discord
        if idle_now:
            embed = build_now_playing_embed(track)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(
                f"🎶 **Fila:** {track.display_title()} • adicionado por {member.mention}\n"
                f"📀 Posição na fila: {posicao}"
            )

    @bot.tree.command(name="pause", description="Pausar reprodução.")
    async def pause(interaction: discord.Interaction):
        player = get_player(interaction.guild)
        if not player.voice_client or not player.voice_client.is_connected():
            return await interaction.response.send_message("⚠️ Não estou em um canal de voz.", ephemeral=True)
        if player.voice_client.is_paused():
            return await interaction.response.send_message("⏸️ Já está pausado.", ephemeral=True)
        if not player.voice_client.is_playing():
            return await interaction.response.send_message("ℹ️ Nada tocando no momento.", ephemeral=True)
        player.voice_client.pause()
        await interaction.response.send_message("⏸️ Pausado.")

    @bot.tree.command(name="resume", description="Retomar reprodução.")
    async def resume(interaction: discord.Interaction):
        player = get_player(interaction.guild)
        if not player.voice_client or not player.voice_client.is_connected():
            return await interaction.response.send_message("⚠️ Não estou em um canal de voz.", ephemeral=True)
        if not player.voice_client.is_paused():
            return await interaction.response.send_message("ℹ️ A reprodução não está pausada.", ephemeral=True)
        player.voice_client.resume()
        await interaction.response.send_message("▶️ Retomado.")

    @bot.tree.command(name="skip", description="Pular a música atual e mostrar a nova tocando.")
    async def skip(interaction: discord.Interaction):
        """
        Stop the current track and wait briefly for the next one to start,
        then send the same 'Now playing' embed used by /nowplaying.
        """
        await interaction.response.defer(thinking=True)

        player = get_player(interaction.guild)
        if not player.voice_client or not player.voice_client.is_connected():
            return await interaction.followup.send("⚠️ Não estou em um canal de voz.")
        if not (player.voice_client.is_playing() or player.current or player.queue.qsize() > 0):
            return await interaction.followup.send("ℹ️ Nada para pular.")

        # Stop current (this triggers the loop to pick the next if any)
        if player.voice_client.is_playing():
            player.voice_client.stop()

        # Wait up to ~3s for the next to actually start
        next_started = None
        for _ in range(30):  # 30 * 0.1s = 3 seconds
            await asyncio.sleep(0.1)
            if player.current and player.voice_client and player.voice_client.is_playing():
                next_started = player.current
                break

        if next_started:
            embed = build_now_playing_embed(next_started)
            return await interaction.followup.send(embed=embed)

        # If it didn't start yet (empty queue or delay), report the state
        if player.queue.qsize() == 0:
            await interaction.followup.send("⏭️ Pulada. A fila está vazia no momento.")
        else:
            # Peek the next item just for user information
            prox = player.snapshot_queue()[0]
            await interaction.followup.send(
                "⏭️ Pulada. A próxima faixa será reproduzida em instantes:\n"
                f"🎶 **Fila:** {prox.display_title()} • por {prox.requester.mention}"
            )

    @bot.tree.command(name="stop", description="Parar e limpar a fila.")
    async def stop_cmd(interaction: discord.Interaction):
        player = get_player(interaction.guild)
        cleared = 0
        if player.voice_client and player.voice_client.is_playing():
            player.voice_client.stop()
        while not player.queue.empty():
            try:
                player.queue.get_nowait()
                player.queue.task_done()
                cleared += 1
            except Exception:
                break
        # Schedule auto-leave after clearing
        await player._cancel_auto_disconnect()
        await player._schedule_auto_disconnect()
        await interaction.response.send_message(f"⏹️ Parado. Fila limpa ({cleared} itens).")

    @bot.tree.command(name="leave", description="Sair do canal e resetar o player.")
    async def leave(interaction: discord.Interaction):
        player = get_player(interaction.guild)
        await player.stop()
        await interaction.response.send_message("👋 Saí do canal e resetei o player.")

    @bot.tree.command(name="queue", description="Mostrar a fila.")
    async def show_queue(interaction: discord.Interaction):
        player = get_player(interaction.guild)
        lines: List[str] = []
        if player.current:
            lines.append(f"**Tocando agora:** {player.current.display_title()} • por {player.current.requester.mention}")
        else:
            lines.append("**Nada tocando agora.**")

        if player.queue.qsize() == 0:
            lines.append("_Fila vazia._")
        else:
            pending = player.snapshot_queue()
            lst = []
            for idx, t in enumerate(pending, start=1):
                lst.append(f"{idx}. {t.display_title()} • por {t.requester.mention}")
            lines.append("\n".join(lst[:20]))
            if len(pending) > 20:
                lines.append(f"... e mais {len(pending) - 20} itens.")
        await interaction.response.send_message("\n".join(lines))

    @bot.tree.command(name="nowplaying", description="Mostrar a música atual.")
    async def now_playing(interaction: discord.Interaction):
        player = get_player(interaction.guild)
        if player.current:
            embed = build_now_playing_embed(player.current)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("ℹ️ Nada tocando no momento.")
