import discord
import os
import datetime

from settings import COGS_DIR, DATA_DIR
from discord.ext import commands
from utils import mods_or_owner, update_json, set_moderator_role



class admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(brief="Loads a Cog")
    @commands.is_owner()
    async def load(self, ctx, extension):
        try:
            await self.client.load_extension(f'cogs.{extension}')
        except Exception as e:
            await ctx.send(f"Could not load {extension}")
        await ctx.send(f"Loading {extension}")

    @commands.command(brief="Unloads a Cog")
    @mods_or_owner()
    async def unload(self, ctx, extension):
        try:
            await self.client.unload_extension(f'cogs.{extension}')
        except Exception as e:
            await ctx.send(f"Could not unload {extension}")
        await ctx.send(f"Unloading {extension}")

    @commands.command(brief="Reloads all Cogs")
    @commands.is_owner()
    async def reload(self, ctx):
        for ext in os.listdir(COGS_DIR):
            if ext.endswith(".py") and ext != '__init__.py':
                await ctx.send(f"Unloading {ext}")
                await self.client.unload_extension(f'cogs.{ext[:-3]}')
                await ctx.send(f"Loading {ext}")
                await self.client.load_extension(f'cogs.{ext[:-3]}')

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

    @commands.hybrid_command(brief='Generates a server invite')
    @mods_or_owner()
    async def invite(self, ctx):
        link = await ctx.channel.create_invite(max_age=1)
        await ctx.send(link)

    @commands.hybrid_command(brief="Gives role to user")
    @mods_or_owner()
    async def addrole(self, ctx, role: discord.Role, user: discord.Member):
        await user.add_roles(role)
        await ctx.send(f'Added role: {role} to {user.mention}')

    @commands.hybrid_command(name='rr', brief="Takes role from user")
    @mods_or_owner()
    async def removerole(self, ctx, role: discord.Role, user: discord.Member):
        await user.remove_roles(role)
        await ctx.send(f'Removed role: {role} from {user.mention}')

    @commands.command()
    @commands.guild_only()
    @mods_or_owner()
    async def changeprefix(self, ctx, prefix):
        update_json({str(ctx.guild.id): prefix}, DATA_DIR, 'prefix.json')
        await ctx.send(f"Prefix changed to `{prefix}`")

    @commands.hybrid_command(brief="Sets the moderator role for this server")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setmodrole(self, ctx, role: discord.Role):
        set_moderator_role(ctx.guild.id, role.id)
        await ctx.send(f"Moderator role set to {role.mention}")


async def setup(client):
    await client.add_cog(admin(client))