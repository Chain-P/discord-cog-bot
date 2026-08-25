import os
import discord

from discord.ext.commands import Bot
from settings import DISCORD_BOT_TOKEN, COGS_DIR
from utils import get_prefix


#test

client = Bot(command_prefix= '.')

for filename in os.listdir(COGS_DIR):
    if filename.endswith('.py') and filename != "__init__.py":
        client.load_extension(f'cogs.{filename[:-3]}')

client.run(DISCORD_BOT_TOKEN)