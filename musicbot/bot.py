# -*- coding: utf-8 -*-

import sys
import discord
from discord.ext import commands
from .config import DISCORD_TOKEN, SYNC_GUILD_ID
from .commands import register_commands


class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        # Do NOT create another CommandTree; self.tree already exists.

    async def setup_hook(self):
        """
        Always perform a "reset & publish" before the bot starts:
          1) CLEAR remote commands (guild if SYNC_GUILD_ID set, else global)
          2) SYNC to apply the clear (removes commands in Discord)
          3) REGISTER local commands into self.tree
          4) SYNC again to publish the current commands
        """
        if SYNC_GUILD_ID:
            guild = discord.Object(id=int(SYNC_GUILD_ID))
            print(f"[SYNC] Clearing GUILD commands for {SYNC_GUILD_ID} ...")
            self.tree.clear_commands(guild=guild)
            await self.tree.sync(guild=guild)

            register_commands(self)

            self.tree.copy_global_to(guild=guild)
            updated = await self.tree.sync(guild=guild)
            print(f"[SYNC] Re-published {len(updated)} command(s) to guild {SYNC_GUILD_ID}.")
        else:
            print("[SYNC] Clearing GLOBAL commands ...")
            self.tree.clear_commands(guild=None)
            await self.tree.sync(guild=None)

            register_commands(self)

            updated = await self.tree.sync(guild=None)
            print(f"[SYNC] Re-published {len(updated)} GLOBAL command(s).")

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        activity = discord.Activity(type=discord.ActivityType.listening, name="/play")
        await self.change_presence(activity=activity)


def run():
    if not DISCORD_TOKEN:
        sys.exit("ERROR: Set DISCORD_TOKEN in your .env file.")
    bot = MusicBot()
    bot.run(DISCORD_TOKEN)
