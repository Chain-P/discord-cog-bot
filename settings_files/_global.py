import os

SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SETTINGS_DIR)
DATA_DIR = os.path.join(ROOT_DIR, 'data')
COGS_DIR = os.path.join(ROOT_DIR, 'cogs')


DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN", False)

#Permission
MODERATOR_ROLE_NAME = os.getenv("MODERATOR_ROLE_NAME", False)