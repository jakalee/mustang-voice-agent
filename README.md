# 🐎 Mustang AI

### Local Voice-Activated AI Agent powered by Claude Code & Faster-Whisper

> Say **"머스탱 (Mustang)"** — your Mac wakes up, listens, thinks, and responds.  
> No cloud subscriptions. No wake-word API fees. Fully local.

**[한국어 README](README_KR.md)**

---

![Mustang AI Demo](docs/demo.gif)

## ✨ What it does

| Feature | Description |
|---------|-------------|
| 🎤 Wake Word | Detects "머스탱" via **faster-whisper** — 100% free, no API key |
| 🗣️ Speech-to-Text | Korean voice → text using Whisper |
| 🔊 Text-to-Speech | macOS native TTS / Windows SAPI |
| 🤖 AI Brain | Natural language processing via **Claude Code CLI** |
| 🖥️ Desktop Widget | Live p5.js waveform ring that reacts to AI state (Übersicht) |
| 📅 Calendar | Google Calendar read/write |
| 📧 Email | Gmail check & send |
| 🌐 Browser | Web automation via Playwright |
| 📁 Drive | Google Drive file search |
| 📱 Telegram | Remote control via Telegram bot |
| ⏰ Scheduler | Timed command execution |
| 🖱️ Screen Control | Screenshot, app launcher |

---

## 🎬 Demo

> **Widget reacts live to every AI state:**

| State | Color | Behavior |
|-------|-------|----------|
| Idle | 🔵 Blue | Slow, calm waveform |
| Listening | 🟢 Green | Medium speed, expanding |
| Thinking | 🟣 Purple | Fast, complex — shows your words |
| Speaking | 🟡 Gold | Pulses with voice amplitude — shows AI response |

---

## 🚀 Quick Start

### Requirements
- macOS (Intel or ARM) — *Windows supported without widget*
- Python 3.10+
- [Claude Code CLI](https://github.com/anthropics/claude-code) — `npm install -g @anthropic-ai/claude-code`

### Install

```bash
git clone https://github.com/jakalee/mustang-voice-agent.git
cd mustang-voice-agent

# Install dependencies
pip install -r requirements.txt

# Copy config
cp config/.env.example config/.env

# Run
python mustang.py
```

> First run downloads the Whisper tiny model (~75MB) automatically.

### Say the magic word

```
"머스탱"  →  AI wakes up  →  speak your command  →  AI responds
```

---

## 🖥️ Desktop Widget (macOS + Übersicht)

The widget lives on your desktop and responds in real time to every AI state change via WebSocket.

### Setup

**1. Download [Übersicht](https://tracesof.net/uebersicht/)** (free, macOS only)

**2. Copy widget files**

```bash
cp ubersicht/*.jsx ~/Library/Application\ Support/Übersicht/widgets/
```

**3. Refresh All Widgets** from the Übersicht menu bar

**4. Run mustang.py** — widget connects automatically via `ws://localhost:8765`

---

## ⚙️ Auto-Start at Login (launchd)

```bash
# Edit the plist with your username, then:
launchctl load ~/Library/LaunchAgents/com.mustang.agent.plist

# Stop
launchctl unload ~/Library/LaunchAgents/com.mustang.agent.plist

# Logs
tail -f /tmp/mustang-agent.log
```

See [README_KR.md](README_KR.md) for the full plist template.

---

## 🏗️ Architecture

```
"머스탱" (wake word)
    │
    ▼
faster-whisper tiny          ← free, offline, ~75MB
    │  detects keyword
    ▼
Whisper small                ← transcribes your command
    │
    ▼
Claude Code CLI              ← reasons + picks skill
    │
    ├─→ Google Calendar
    ├─→ Gmail
    ├─→ YouTube (via yt-dlp + Chrome cookies → no ads)
    ├─→ Playwright browser automation
    └─→ Shell commands / Screen control
    │
    ▼
macOS TTS (say + afplay)     ← speaks the response
    │
    ▼
WebSocket → Übersicht widget ← waveform ring reacts live
```

---

## 📁 Project Structure

```
mustang-voice-agent/
├── mustang.py            # Main entry point (widget server built-in)
├── requirements.txt
├── config/
│   ├── .env              # Your config (git-ignored)
│   └── .env.example
├── core/
│   ├── claude_runner.py  # Claude Code CLI wrapper
│   ├── stt.py            # Speech recognition
│   ├── tts.py            # Text-to-speech
│   ├── wakeword.py       # Wake word detection (faster-whisper)
│   ├── skill_manager.py  # Skill routing
│   └── scheduler.py      # Task scheduler
├── skills/
│   ├── youtube.py        # YouTube via yt-dlp + Chrome session
│   ├── check_calendar.py
│   ├── check_email.py
│   └── ...
├── widget/
│   ├── index.html        # Standalone HTML widget
│   └── p5.min.js
└── ubersicht/
    ├── mustang-ai.jsx    # Übersicht waveform widget
    └── mustang-starter.jsx  # Auto-start watcher
```

---

## 🌐 Platform Support

| Platform | Voice Mode | Widget | Auto-start |
|----------|-----------|--------|-----------|
| macOS ARM (M1~M4) | ✅ | ✅ Übersicht | ✅ launchd |
| macOS Intel | ✅ | ✅ Übersicht | ✅ launchd |
| Windows | ✅ | ❌ | ✅ Task Scheduler |

---

## 🔧 Wake Word Accuracy Tips

The wake word engine uses **faster-whisper tiny** — lightweight but occasionally mishears.

- Speak clearly and slightly louder than normal
- Upgrade to `"small"` model in `core/wakeword.py` for better accuracy (slower)
- Recognized variants: "머스탱", "mustang", "스탱", and common mishear patterns

---

## 📋 Requirements

```
faster-whisper
pyaudio
websockets
playwright
yt-dlp
```

> Full list in `requirements.txt`

---

## 📄 License

MIT License — use it, fork it, build on it.

---

## 🤝 Contributing

PRs welcome! Especially:
- New skills (Notion, Slack, HomeKit, etc.)
- Wake word accuracy improvements
- Windows widget support
- Multi-language wake words
