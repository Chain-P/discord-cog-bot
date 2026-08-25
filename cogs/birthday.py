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

        pid = str(ctx.author.id)
        gid = str(ctx.guild.id)
        await BirthdayTools.save(gid, pid, bday)
        await ctx.send(f"Saved your birthday as {bday}.")

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
        #TODO: build remove command with pop() module
        pass

    @birthday.command()
    @mods_or_owner()
    async def set_channel(self, ctx):
        BirthdayTools.set_birthday_channel(ctx.guild.id, ctx.channel.id)
        await ctx.send(f"Birthday announcements will be posted in {ctx.channel.mention}.")
            

                

async def setup(client):
    await client.add_cog(Birthday(client))