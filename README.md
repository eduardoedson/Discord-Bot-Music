# 🎵 BotDiscord — Discord Music Bot (Python)

A modern **Discord music bot** built in **Python 3.10+** that plays music directly from **YouTube**, supports a dynamic queue, displays rich embeds with thumbnails, and automatically disconnects after inactivity.

It uses **`discord.py`**, **`yt-dlp`**, and **FFmpeg**, following a modular and maintainable architecture.

---

## ⚡ Quick Start

```bash
# Clone the project
git clone https://github.com/YOUR_USERNAME/BotDiscord.git
cd BotDiscord

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux / macOS
# or
.venv\Scripts\activate   # Windows

# Install dependencies
pip install -U pip
pip install -r requirements.txt

# Create your .env file
echo "DISCORD_TOKEN=YOUR_BOT_TOKEN" > .env
echo "AUTO_DISCONNECT_SECONDS=180" >> .env

# Run the bot
python3 main.py
```

---

## 🧩 Features

✅ Play music from YouTube (by name or URL)  
✅ Rich "Now Playing" embed with thumbnail, author, and duration  
✅ Queue system with multiple tracks  
✅ Commands for pause, resume, skip, stop, queue, leave, nowplaying  
✅ Automatically joins your voice channel when you use `/play`  
✅ Auto-disconnects after inactivity (configurable)  
✅ Automatic command synchronization at startup  

---

## ⚙️ Project Structure

```bash
BotDiscord/
├── .env                      # Private configuration (token, settings)
├── main.py                   # Main entry point
├── README.md                 # This documentation file
├── requirements.txt          # Dependencies list
├── musicbot/
│   ├── __init__.py
│   ├── bot.py                # Initializes and syncs commands
│   ├── commands.py           # Slash command logic (play, skip, etc.)
│   ├── config.py             # Environment variables and settings
│   ├── extractor.py          # YouTube metadata & stream extraction via yt-dlp
│   └── player.py             # Playback, queue control, auto-disconnect
└── .venv/                    # Python virtual environment (optional)
```

---

## 📦 Main Dependencies

| Package | Purpose |
|----------|----------|
| **discord.py[voice]** | Discord API wrapper with voice support |
| **yt-dlp** | Extracts audio streams and metadata from YouTube |
| **ffmpeg** | Required executable for audio streaming |
| **python-dotenv** | Loads the `.env` configuration file |
| **asyncio** | Async queue and playback control |

---

## 🔧 Requirements

- **Python 3.10+**
- **FFmpeg** installed and available in your system PATH

### Install FFmpeg

**Ubuntu / Debian**
```bash
sudo apt update && sudo apt install ffmpeg -y
```

**Windows**
Download from: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)  
Add the `bin/` folder to your **PATH** environment variable.

---

## 🚀 Installation

Clone and enter the project folder:

```bash
git clone https://github.com/eduardoedson/Discord-Bot-Music BotDiscord
cd BotDiscord
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# or
.venv\Scripts\activate         # Windows
```

Install dependencies:

```bash
pip install -U pip
pip install -r requirements.txt
```

---

## 🔐 .env Configuration

Create a `.env` file in the project root:

```ini
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
AUTO_DISCONNECT_SECONDS=180
SYNC_GUILD_ID=      # optional: a single guild ID for fast command sync
```

> You can get your bot token from the [Discord Developer Portal](https://discord.com/developers/applications).

---

## ▶️ Running the Bot

```bash
python3 main.py
```

On startup, the bot will:
1. Log into Discord  
2. Automatically clear and sync slash commands (`/play`, `/skip`, etc.)  
3. Initialize a music player per guild  

---

## 🎧 Usage (Slash Commands)

| Command | Description |
|----------|-------------|
| `/play <name or URL>` | Play a YouTube song |
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/skip` | Skip the current track and show the next one |
| `/stop` | Stop and clear the queue |
| `/queue` | Show queued songs |
| `/nowplaying` | Show current track with rich embed |
| `/leave` | Leave the voice channel and reset the player |

---

## 🖼️ Example: “Now Playing” Embed

When a new song starts, the bot posts an embed like this:

```
🎵 Now Playing:
────────────────────────────
Michael Jackson – Billie Jean (Blues AI Cover)
Author: Remix Realms
Source: youtube
Duration: 06:54
────────────────────────────
Added by @Edu
```

---

## 🧠 How It Works

- `/play` → calls `extract_track()` using **yt-dlp** to get audio URL + metadata.  
- The song is added to an **`asyncio.Queue`** handled by `player_loop()`.  
- FFmpeg streams the audio directly to Discord.  
- When the queue empties, an **auto-disconnect timer** starts.  
- `/skip` simply stops the current stream — the next track automatically starts.  

---

## 🛠️ Logs & Debugging

Console logs (in English) help track player actions:

```
[PLAYER] Starting: Billie Jean (Blues AI Cover)
[PLAYER] Finished: Billie Jean (Blues AI Cover)
[AUTO-LEAVE] Idle for 180s in guild 123456789. Leaving.
```

---

## 🧩 Customization

- Adjust auto-disconnect delay in `.env`  
- Extend `extractor.py` to support other platforms (Spotify, SoundCloud, etc.)  
- Slash command responses are **in Portuguese**, while internal logs are **in English** for easier debugging.  

---

## 🧑‍💻 Credits

- Built with **Python 3.10+**  
- Powered by **discord.py** and **yt-dlp**  
- Fully modular and ready for expansion  

---

## ⚖️ License

Released under the **MIT License**.  
Free to use, modify, and distribute — please keep the original credits.

---

**Developed with 💻 by Eduardo Edson Batista Cordeiro Alves**
