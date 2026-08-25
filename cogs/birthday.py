import discord

from discord.ext import commands
from birthday.controller import BirthdayTools
from utils import mods_or_owner

class Birthday(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.group()
    async def birthday(self, ctx):
        
        pass

    @birthday.command(name='add')
    async def add(self, ctx, bday):

        pid = str(ctx.author.id)
        gid = str(ctx.guild.id)
        await BirthdayTools.save(gid, pid, bday)
        
    @birthday.command(name='check')
    @mods_or_owner()
    async def check(self):
        check, gild= await BirthdayTools.check(self)
        if check:
            for uid in gild.keys():
                channel = self.client.get_channel(BirthdayTools.get_birthday_channel(self, gild[uid]))
                await channel.send(f"Happy Birthday <@{uid}>")
        
    @birthday.command(name='remove')
    @mods_or_owner()
    async def remove(self, ctx, member: discord.Member):
        #TODO: build remove command with pop() module
        pass

    @birthday.command()
    @mods_or_owner()
    async def set_channel(self, ctx):
        BirthdayTools.set_birthday_channel(self, ctx.guild.id, ctx.channel.id)
            

                

def setup(client):
    client.add_cog(Birthday(client))