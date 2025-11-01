# -*- coding: utf-8 -*-

import asyncio
from typing import Dict, Any
import discord
from .player import Track, is_url
from .config import YTDL_OPTS


async def extract_track(query: str, requester: discord.User) -> Track:
    """
    Resolve a YouTube URL or search query to a playable audio stream URL
    and wrap it into a Track object with metadata (uploader, thumbnail, etc.).
    """
    loop = asyncio.get_running_loop()
    import yt_dlp  # lazy import

    def _extract() -> Dict[str, Any]:
        with yt_dlp.YoutubeDL(YTDL_OPTS) as ytdl:
            q = query if is_url(query) else f"ytsearch1:{query}"
            info = ytdl.extract_info(q, download=False)
            if "entries" in info:
                info = info["entries"][0]
            if "url" not in info:
                raise RuntimeError("Failed to extract audio URL from yt-dlp.")
            return info

    info = await loop.run_in_executor(None, _extract)
    return Track(
        title=info.get("title") or "Sem título",
        url=info.get("url"),
        webpage_url=info.get("webpage_url") or info.get("original_url") or query,
        duration=info.get("duration"),
        requester=requester,
        uploader=info.get("uploader") or "Desconhecido",
        thumbnail=info.get("thumbnail") or "",
        source="youtube",
    )
