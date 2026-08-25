# Zero-Bot

A modular Discord bot built with `discord.py`, organized around a cog-per-feature
architecture with a few features (RPS, Hangman, Guess-a-Word, Birthdays) split
into their own model/controller modules.

## Features

- **Moderation** — kick/ban/unban, role add/remove, invite generation, prefix
  changes, permission checks that allow either the server owner or a
  configurable moderator role (`cogs/mods.py`, `cogs/admin.py`, `utils.py`)
- **Games** — Rock Paper Scissors, Hangman, and Guess-a-Word, each implemented
  as its own model/controller pair (`rps/`, `hangman/`, `gaw/`, `cogs/games.py`)
- **Birthdays** — per-server birthday tracking with a daily background task
  that checks for birthdays and posts a greeting to a configured channel
  (`birthday/`, `cogs/birthday.py`, `cogs/listeners.py`)
- **Hot-reloadable cogs** — load/unload/reload extensions at runtime without
  restarting the bot (`cogs/admin.py`)
- **Misc commands** — OwO-text conversion, "yo mama" insults, apologies, and
  other small fun commands (`cogs/commands.py`)
- **Background tasks** — rotating bot status and the birthday check loop, both
  built on `discord.ext.tasks` (`cogs/listeners.py`)

## Architecture

Cogs are auto-discovered and loaded from the `cogs/` directory on startup
(`main.py`). Config is environment-driven via `python-dotenv`, with a
`DEBUG` flag switching between `settings_files/development.py` and
`settings_files/product.py` (`settings.py`). Larger features (RPS, Hangman,
Guess-a-Word, Birthday) follow a lightweight model/controller split so game
state logic is decoupled from the Discord command layer.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your bot token and moderator role ID
python main.py
```

## Tech used / practiced

Python, `discord.py`, `python-dotenv`, decorators, JSON-file persistence,
per-guild config (prefixes, birthdays), background task loops.
