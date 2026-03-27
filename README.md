<div align="center">

# 🔮 Pandora Bot

**AI-powered therapeutic assistant for Telegram**

[![CI](https://github.com/YOUR_USERNAME/pandora-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/pandora-bot/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![aiogram 3](https://img.shields.io/badge/aiogram-3.x-blue.svg)](https://docs.aiogram.dev/)

*A hybrid Telegram bot providing psychological support through pattern-matched responses and AI-generated conversations powered by Meta-Llama 3.3 70B.*

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **Hybrid AI** | Pattern-matching for simple queries + LLM for deep conversations |
| 🧘 **Guided Exercises** | Breathing, meditation, muscle relaxation, grounding techniques |
| 📊 **User Statistics** | Tracks interactions, message counts, session duration |
| ⭐ **Rating System** | In-bot 1–10 rating with persistent JSON storage |
| 📞 **Crisis Resources** | Quick access to mental health hotline numbers |
| 💬 **Conversation Memory** | Per-user chat history for contextual AI responses |

## 🏗️ Tech Stack

- **Runtime:** Python 3.11+
- **Telegram:** [aiogram 3.x](https://docs.aiogram.dev/) (async)
- **AI:** [SambaNova API](https://sambanova.ai/) — Meta-Llama 3.3 70B via OpenAI SDK (async)
- **NLP:** `difflib` fuzzy matching for intent detection
- **Container:** Docker & Docker Compose

## 📁 Project Structure

```
pandora-bot/
├── bot.py               # All bot logic (single file)
├── intents.json         # Intent patterns & responses (48 intents)
├── user_stats.json      # User statistics (auto-generated)
├── .env.example         # Environment variable template
├── requirements.txt     # Production dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A Telegram Bot token from [@BotFather](https://t.me/BotFather)
- A SambaNova API key (or any OpenAI-compatible endpoint)

### 1. Clone & Configure

```bash
git clone https://github.com/YOUR_USERNAME/pandora-bot.git
cd pandora-bot
cp .env.example .env
```

Edit `.env`:

```ini
BOT_TOKEN=your-telegram-bot-token
AI_API_KEY=your-sambanova-api-key
```

### 2a. Run Locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python bot.py
```

### 2b. Run with Docker

```bash
docker compose up -d --build
```

### 3. Talk to Your Bot

Open Telegram, find your bot, send `/start`.

## 🧪 Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=.
```

## 🔧 Configuration

All settings via environment variables (or `.env`):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ | — | Telegram bot token |
| `AI_API_KEY` | ✅ | — | SambaNova / OpenAI-compatible API key |
| `AI_BASE_URL` | ❌ | `https://api.sambanova.ai/v1` | AI endpoint URL |
| `AI_MODEL` | ❌ | `Meta-Llama-3.3-70B-Instruct` | Model identifier |
| `MAX_HISTORY` | ❌ | `8` | Max conversation pairs kept in memory |
| `SESSION_TIMEOUT` | ❌ | `1800` | Session timeout (seconds) |

## 📝 Intent System

Two-tier response strategy:

1. **Pattern Matching** — messages compared against `intents.json` (exact + fuzzy via `difflib`, cutoff 0.6)
2. **AI Fallback** — unmatched messages go to the LLM with conversation history

Add new intents by editing `intents.json`:

```json
{
  "tag": "your_tag",
  "patterns": ["сообщение 1", "сообщение 2"],
  "responses": ["ответ 1", "ответ 2"]
}
```

## ⚠️ Disclaimer

This bot is **not a substitute for professional mental health care**. It is a supportive tool only. If you or someone you know is in crisis, contact a qualified professional or emergency services.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

[MIT](LICENSE)
