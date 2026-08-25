import discord

from discord.ext import commands
from birthday.controller import BirthdayTools
from utils import mods_or_owner

class Birthday(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.hybrid_group()
    async def birthday(self, ctx):

        pass

    @birthday.command(name='add')
    async def add(self, ctx, bday):
        try:
            parsed = BirthdayTools.parse_birthday(bday)
        except ValueError as e:
            await ctx.send(str(e))
            return

        pid = str(ctx.author.id)
        gid = str(ctx.guild.id)
        await BirthdayTools.save(gid, pid, parsed)
        await ctx.send(f"Saved your birthday as {parsed[:5]}.")

    @birthday.command(name='check')
    @mods_or_owner()
    async def check(self, ctx):
        check, gild = await BirthdayTools.check()
        if check:
            for uid in gild.keys():
                channel = self.client.get_channel(BirthdayTools.get_birthday_channel(gild[uid]))
                if channel is not None:
                    await channel.send(f"Happy Birthday <@{uid}>")
            await ctx.send(f"Found {len(gild)} birthday(s) today.")
        else:
            await ctx.send("No birthdays today.")

    @birthday.command(name='remove')
    @mods_or_owner()
    async def remove(self, ctx, member: discord.Member):
        removed = BirthdayTools.remove(ctx.guild.id, member.id)
        if removed:
            await ctx.send(f"Removed {member.mention}'s birthday.")
        else:
            await ctx.send(f"{member.mention} doesn't have a birthday saved.")

    @birthday.command()
    @mods_or_owner()
    async def set_channel(self, ctx):
        BirthdayTools.set_birthday_channel(ctx.guild.id, ctx.channel.id)
        await ctx.send(f"Birthday announcements will be posted in {ctx.channel.mention}.")
            

                

async def setup(client):
    await client.add_cog(Birthday(client))