# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# If set, the bot will clear+sync commands ONLY in this guild (fast).
# If not set, it will clear+sync GLOBAL commands (slower propagation).
SYNC_GUILD_ID = os.getenv("SYNC_GUILD_ID")

# Optional: cookies for yt-dlp to improve restricted/private streams
YTDLP_COOKIES = os.getenv("YTDLP_COOKIES")

def _parse_int(env_val: str | None, default: int) -> int:
    try:
        return int(env_val) if env_val is not None else default
    except Exception:
        return default

# Auto disconnect seconds after queue finishes (0 disables auto-leave)
AUTO_DISCONNECT_SECONDS = _parse_int(os.getenv("AUTO_DISCONNECT_SECONDS"), 180)

# yt-dlp options for resolving a directly playable audio stream.
# Let yt-dlp select the current supported YouTube clients automatically;
# forcing android/web clients can require a PO token and expose no audio formats.
YTDL_OPTS = {
    # Prefer m4a first, then fall back to any available audio-capable format.
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "extract_flat": False,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "cachedir": False,
    "skip_download": True,
}

if YTDLP_COOKIES and os.path.isfile(YTDLP_COOKIES):
    YTDL_OPTS["cookiefile"] = YTDLP_COOKIES

# FFmpeg options: try to reconnect on network hiccups
FFMPEG_BEFORE_OPTS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin"
FFMPEG_OPTS = "-vn"
