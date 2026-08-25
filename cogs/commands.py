import discord
import random

from utils import text_to_owo, notify_user, get_momma_jokes, get_apologies
from discord.ext import commands

class commands(commands.Cog):

    def __init__(self, client):
        self.client = client
            
    @commands.command()
    async def poke(self, ctx, member: discord.Member = None):
        if member is not None:
            message = f"{ctx.author.name} poked you!!!!"
            await notify_user(member, message)
        else:
            ctx.send("Please use @mention to poke someone.")

    @commands.command(brief="Says hello")
    async def hello(self, ctx):
        async with ctx.typing():
            await ctx.send(f'Hello! {ctx.author.mention}')

    @commands.command(brief="A simple coin flip. Heads or Tails?")
    async def flip(self, ctx):
        n = random.randint(0, 1)
        await ctx.send("Heads" if n ==1 else "Tails")
        print('Flipped')

    @commands.command(brief="Owo's your message")
    async def owo(self, ctx):
        await ctx.send(text_to_owo(ctx.message.content))

    @commands.command(brief="Dm's you")
    async def dm(self, ctx):
        await ctx.author.send("Depression")

    @commands.command(brief="Insults the mentioned user")
    async def insult(self, ctx, member: discord.Member = None):
        if member != None:
            insult = await get_momma_jokes()
            await ctx.send(f'{member.mention} ha ha {insult}')
        else:
            insult = await get_momma_jokes()
            await ctx.send(insult)

    @commands.command(brief="Someone feeling butthurt?")
    async def cry(self, ctx, user: discord.Member = None):
        apology = await get_apologies()
        if user != None:
            await ctx.send(f"{user.mention} {apology}")
        else:
            await ctx.send(apology)

def setup(client):
    client.add_cog(commands(client))
    
    
    
    