import discord
import random

from utils import text_to_owo, notify_user, get_momma_jokes, get_apologies
from discord.ext import commands
from discord.ext.commands import Group

class commands(commands.Cog):

    def __init__(self, client):
        self.client = client
            
    @commands.hybrid_command(brief="Pokes a mentioned user")
    async def poke(self, ctx, member: discord.Member = None):
        if member is not None:
            message = f"{ctx.author.name} poked you!!!!"
            await notify_user(member, message)
            await ctx.send(f"Poked {member.mention}!")
        else:
            await ctx.send("Please use @mention to poke someone.")

    @commands.hybrid_command(brief="Says hello")
    async def hello(self, ctx):
        async with ctx.typing():
            await ctx.send(f'Hello! {ctx.author.mention}')

    @commands.hybrid_command(brief="A simple coin flip. Heads or Tails?")
    async def flip(self, ctx):
        n = random.randint(0, 1)
        await ctx.send("Heads" if n ==1 else "Tails")
        print('Flipped')

    @commands.hybrid_command(brief="Owo's your message")
    async def owo(self, ctx, *, text: str):
        await ctx.send(text_to_owo(text))

    @commands.hybrid_command(brief="Dm's you")
    async def dm(self, ctx):
        await ctx.author.send("Depression")

    @commands.hybrid_command(brief="Insults the mentioned user")
    async def insult(self, ctx, member: discord.Member = None):
        if member != None:
            insult = await get_momma_jokes()
            await ctx.send(f'{member.mention} ha ha {insult}')
        else:
            insult = await get_momma_jokes()
            await ctx.send(insult)

    @commands.hybrid_command(brief="Someone feeling butthurt?")
    async def cry(self, ctx, user: discord.Member = None):
        apology = await get_apologies()
        if user != None:
            await ctx.send(f"{user.mention} {apology}")
        else:
            await ctx.send(apology)

    @commands.hybrid_command(name='help', brief="Shows this help message")
    async def help_command(self, ctx, command: str = None):
        prefix = ctx.prefix or '/'

        if command:
            cmd = self.client.get_command(command)
            if cmd is None or cmd.hidden:
                await ctx.send(f"No command called `{command}` found.")
                return
            embed = discord.Embed(title=cmd.qualified_name, description=cmd.brief or "No description available.")
            if isinstance(cmd, Group):
                subcommands = ", ".join(sub.name for sub in cmd.commands if not sub.hidden)
                if subcommands:
                    embed.add_field(name="Subcommands", value=subcommands, inline=False)
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="Zero-Bot Commands",
            description=f"Use `{prefix}help <command>` for details on a specific command.",
        )
        by_cog = {}
        for cmd in self.client.commands:
            if cmd.hidden:
                continue
            by_cog.setdefault(cmd.cog_name or "Other", []).append(cmd)

        for cog_name in sorted(by_cog):
            lines = []
            for cmd in sorted(by_cog[cog_name], key=lambda c: c.name):
                lines.append(f"**{cmd.name}** — {cmd.brief or 'No description'}")
                if isinstance(cmd, Group):
                    for sub in sorted(cmd.commands, key=lambda c: c.name):
                        if not sub.hidden:
                            lines.append(f"　**{cmd.name} {sub.name}** — {sub.brief or 'No description'}")
            embed.add_field(name=cog_name, value="\n".join(lines)[:1024], inline=False)

        await ctx.send(embed=embed)

async def setup(client):
    await client.add_cog(commands(client))
    
    
    
    