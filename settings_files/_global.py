import os

SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SETTINGS_DIR)
DATA_DIR = os.path.join(ROOT_DIR, 'data')
COGS_DIR = os.path.join(ROOT_DIR, 'cogs')

#Per-guild config DB. Defaults to a local SQLite file; set DATABASE_URL to any
#SQLAlchemy URL (e.g. a Postgres DSN) to swap backends without code changes.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(DATA_DIR, 'zerobot.db')}")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN", False)

#Fallback command prefix for DMs and guilds with no prefix set via .changeprefix
DEFAULT_PREFIX = '.'

#Dev guild for instant slash-command sync (set in .env.debug); leave unset for global sync
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID", False)

#Web dashboard (dashboard/app.py) — separate process, Discord OAuth2 login
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", False)
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", False)
DASHBOARD_REDIRECT_URI = os.getenv("DASHBOARD_REDIRECT_URI", "http://localhost:8443/callback")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", False)
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8443"))