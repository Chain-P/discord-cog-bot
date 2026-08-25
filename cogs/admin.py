import discord
import os
import datetime
import json

from settings import COGS_DIR, DATA_DIR
from discord.ext import commands
from utils import mods_or_owner



class admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(brief="Loads a Cog")
    @commands.is_owner()
    async def load(self, ctx, extension):
        try:
            self.client.load_extension(f'cogs.{extension}')
        except Exception as e:
            await ctx.send(f"Could not load {extension}")
        await ctx.send(f"Loading {extension}")

    @commands.command(brief="Unloads a Cog")
    @mods_or_owner()
    async def unload(self, ctx, extension):
        try:
            self.client.unload_extension(f'cogs.{extension}')
        except Exception as e:
            await ctx.send(f"Could not unload {extension}")
        await ctx.send(f"Unloading {extension}")

    @commands.command(brief="Reloads all Cogs")
    @commands.is_owner()
    async def reload(self, ctx):
        for ext in os.listdir(COGS_DIR):
            if ext.endswith(".py") and ext != '__init__.py':
                await ctx.send(f"Unloading {ext}")
                self.client.unload_extension(f'cogs.{ext[:-3]}')
                await ctx.send(f"Loading {ext}")  
                self.client.load_extension(f'cogs.{ext[:-3]}')

    @commands.command(brief='Shows discord server status')
    @commands.is_owner()
    async def status(self, ctx, *args):
        guild = ctx.guild

        no_voice_channels = len(guild.voice_channels)       
        no_text_channels = len(guild.text_channels)  

        embed = discord.Embed()

        embed.add_field(name="Server Name", value=guild.name, inline=False)
        embed.add_field(name="# Voice Channels", value=no_voice_channels)      
        embed.add_field(name="# Text Channels", value=no_text_channels)  
        embed.set_author(name=self.client.user.name)
        embed.set_footer(text=datetime.datetime.now())           
        
        await ctx.send(embed=embed)

    @commands.command(brief='Generates a server invite')
    @mods_or_owner()
    async def invite(self, ctx):
        link = await ctx.channel.create_invite(max_age=1)
        await ctx.send(link)

    @commands.command(brief="Gives role to user")
    @mods_or_owner()
    async def addrole(self, ctx, role: discord.Role, user: discord.Member):
        await user.add_roles(role)
        await ctx.send(f'Added role: {role} to {user.mention}')

    @commands.command(name='rr', brief="Takes role from user")
    @mods_or_owner()
    async def removerole(self, ctx, role: discord.Role, user: discord.Member):
        await user.remove_roles(role)
        await ctx.send(f'Removed role: {role} from {user.mention}')

    @commands.command()
    @mods_or_owner()
    async def changeprefix(self, ctx, prefix):
        with open(DATA_DIR, 'prefix.json') as f:
            prefixes = json.load(f)

        prefixes[str(ctx.guild.id)] = prefix

        with open(DATA_DIR, 'prefix.json', 'w') as f:
            json.dump(prefixes, f)

                        
def setup(client):
    client.add_cog(admin(client))