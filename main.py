import os
import discord

from discord.ext.commands import Bot
from settings import DISCORD_BOT_TOKEN, COGS_DIR, DEV_GUILD_ID


intents = discord.Intents.default()
intents.message_content = True


class ZeroBot(Bot):
    async def setup_hook(self):
        for filename in os.listdir(COGS_DIR):
            if filename.endswith('.py') and filename != "__init__.py":
                await self.load_extension(f'cogs.{filename[:-3]}')

        if DEV_GUILD_ID:
            guild = discord.Object(id=int(DEV_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()


client = ZeroBot(command_prefix='.', intents=intents)

client.run(DISCORD_BOT_TOKEN)
