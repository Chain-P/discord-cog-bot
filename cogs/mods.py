import discord

from discord.ext import commands
from utils import mods_or_owner, notify_user

class mods(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(brief='Kick a user via mention')
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(kick_members=True), mods_or_owner())
    async def kick(self, ctx, member: discord.Member = None, reason=str("You have been Kicked")):
        if member is not None:
            await notify_user(member, reason)
            await ctx.guild.kick(member, reason=reason)
        else:
            await ctx.send("Please specify a user to with via mention")

    @commands.command(brief='Unban a user via mention')
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(ban_members=True), mods_or_owner())
    async def unban(self, ctx, member="", reason=str("You have been unbanned. Please behave.")):
        if member == "":
            await ctx.send("Please specify a username to unban")
            return

        bans = await ctx.guild.bans()
        for b in bans:
            if b.user.name == member:
                await ctx.guild.unban(b.user, reason=reason)
                await ctx.send(f"{member} was unbanned")
                return
        await ctx.send(f"{member} was not found in ban list")
        
            

    @commands.command(brief='Ban a user via mention')
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(ban_members=True), mods_or_owner())
    async def ban(self, ctx, member: discord.Member = None, reason=str("You have been baned. Enjoy your time out.")):
        if member is not None:
            await notify_user(member, reason)
            await ctx.guild.ban(member, reason=reason)
        else:
            await ctx.send("Please specify a user to with via mention")
                   
                        
def setup(client):
    client.add_cog(mods(client))