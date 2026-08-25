import discord
import os

from settings import COGS_DIR
from discord.ext import commands

class bot_tools(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, ex):
        print(ex)
        await ctx.send("Please check with .help for usage of this command or talk to your administrator.")

                                
                   
                        
async def setup(client):
    await client.add_cog(bot_tools(client))