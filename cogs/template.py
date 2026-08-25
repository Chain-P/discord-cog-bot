import discord
import os

from discord.ext import commands

class template(commands.Cog):

    def __init__(self, client):
        self.client = client

async def setup(client):
    await client.add_cog(template(client))