# -*- coding: utf-8 -*-

import re
import asyncio
from typing import Optional, List
import discord
from .config import FFMPEG_BEFORE_OPTS, FFMPEG_OPTS, AUTO_DISCONNECT_SECONDS


def fmt_duration(seconds: Optional[int]) -> str:
    try:
        if seconds is None:
            return "??:??"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    except Exception:
        return "??:??"


def is_url(s: str) -> bool:
    return bool(re.match(r"^https?://", s.strip(), re.IGNORECASE))


class Track:
    def __init__(
        self,
        *,
        title: str,
        url: str,
        webpage_url: str,
        duration: Optional[int],
        requester: discord.User,
        uploader: str = "Desconhecido",
        thumbnail: str = "",
        source: str = "youtube",
    ):
        self.title = title
        self.url = url                  # direct audio stream URL
        self.webpage_url = webpage_url  # YouTube watch page
        self.duration = duration
        self.requester = requester
        self.uploader = uploader
        self.thumbnail = thumbnail
        self.source = source

    def display_title(self) -> str:
        return f"{self.title} [{fmt_duration(self.duration)}]"


class MusicPlayer:
    """Per-guild music player with auto-disconnect after queue ends."""
    def __init__(self, bot: discord.Client, guild: discord.Guild):
        self.bot = bot
        self.guild = guild
        self.queue: asyncio.Queue[Track] = asyncio.Queue()
        self.current: Optional[Track] = None
        self.next_track_event = asyncio.Event()
        self.player_task: Optional[asyncio.Task] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.lock = asyncio.Lock()

        # Auto-disconnect state
        self._auto_disconnect_task: Optional[asyncio.Task] = None
        self._auto_disconnect_seconds = max(0, int(AUTO_DISCONNECT_SECONDS))

    async def ensure_connected(self, channel: discord.VoiceChannel):
        async with self.lock:
            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.channel != channel:
                    await self.voice_client.move_to(channel)
                return
            self.voice_client = await channel.connect(self_deaf=True)

    def _after_playback(self, error: Optional[Exception]):
        if error:
            print(f"[AUDIO ERROR] {error}")
        # signal the player loop to continue
        self.bot.loop.call_soon_threadsafe(self.next_track_event.set)

    async def start(self):
        if self.player_task is None or self.player_task.done():
            self.player_task = self.bot.loop.create_task(self.player_loop())

    async def stop(self):
        # cancel any pending auto-leave first
        await self._cancel_auto_disconnect()

        async with self.lock:
            if self.voice_client and self.voice_client.is_connected():
                try:
                    await self.voice_client.disconnect(force=True)
                except Exception:
                    pass
            self.voice_client = None

        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break

        self.current = None
        if self.player_task and not self.player_task.done():
            self.player_task.cancel()
            self.player_task = None

    async def player_loop(self):
        """
        Plays queued tracks sequentially.
        - Cancels any pending auto-disconnect when a new track starts.
        - Schedules an auto-disconnect when the queue becomes empty.
        - Emits helpful logs for start/finish and FFmpeg errors.
        """
        try:
            while True:
                # Wait for next track from the queue
                self.next_track_event.clear()
                self.current = await self.queue.get()

                # Any activity cancels idle auto-disconnect
                await self._cancel_auto_disconnect()

                # If voice connection dropped, consume item and exit loop
                if not self.voice_client or not self.voice_client.is_connected():
                    print("[PLAYER] Voice client not connected. Exiting loop.")
                    self.queue.task_done()
                    self.current = None
                    return

                # Start playback
                try:
                    print(f"[PLAYER] Starting: {self.current.title} ({self.current.webpage_url})")
                    source = discord.FFmpegPCMAudio(
                        self.current.url,
                        before_options=FFMPEG_BEFORE_OPTS,
                        options=FFMPEG_OPTS
                    )
                    self.voice_client.play(source, after=self._after_playback)
                except Exception as e:
                    # If FFmpeg fails, log and move on to next track
                    print(f"[PLAYER] FFmpeg play error: {e}")
                    self.queue.task_done()
                    self.current = None
                    continue

                # Wait until playback finishes (_after_playback sets the event)
                await self.next_track_event.wait()

                # Mark the queue item as processed
                self.queue.task_done()

                # Log finish and clear current
                if self.current:
                    print(f"[PLAYER] Finished: {self.current.title}")
                self.current = None

                # If queue is empty, schedule auto-disconnect timer
                if self.queue.empty() and self._auto_disconnect_seconds > 0:
                    await self._schedule_auto_disconnect()

        except asyncio.CancelledError:
            # Normal task cancellation (e.g., when stopping the player)
            print("[PLAYER] Loop cancelled.")
        except Exception as e:
            # Catch-all to keep the task alive on unexpected errors
            print(f"[PLAYER] Unexpected error in player_loop: {e}")

    async def _schedule_auto_disconnect(self):
        """Schedules auto-leave after inactivity."""
        if self._auto_disconnect_task and not self._auto_disconnect_task.done():
            return

        async def _auto_leave():
            try:
                await asyncio.sleep(self._auto_disconnect_seconds)
                if (
                    self.voice_client
                    and self.voice_client.is_connected()
                    and not self.voice_client.is_playing()
                    and self.queue.empty()
                    and self.current is None
                ):
                    print(f"[AUTO-LEAVE] Idle for {self._auto_disconnect_seconds}s in guild {self.guild.id}. Leaving.")
                    await self.stop()
            except asyncio.CancelledError:
                pass

        self._auto_disconnect_task = self.bot.loop.create_task(_auto_leave())

    async def _cancel_auto_disconnect(self):
        """Cancels the auto-leave timer."""
        if self._auto_disconnect_task and not self._auto_disconnect_task.done():
            self._auto_disconnect_task.cancel()
            try:
                await self._auto_disconnect_task
            except asyncio.CancelledError:
                pass
        self._auto_disconnect_task = None

    def snapshot_queue(self) -> List[Track]:
        # non-destructive read (does not consume queue)
        return list(self.queue._queue)  # type: ignore[attr-defined]
