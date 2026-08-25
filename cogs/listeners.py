import discord

from settings import DATA_DIR
from datetime import datetime

from discord.ext import commands, tasks
from itertools import cycle

from birthday.controller import BirthdayTools
from cogs.birthday import Birthday

class listener(commands.Cog):

    def __init__(self, client):
        self.client = client

    current_time = datetime.now()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in at {self.current_time.strftime("%m/%d/%Y %H:%M:%S")}')
        print("Logged in as")
        print(f"Username:  {self.client.user.name}")
        print(f"User ID:  {self.client.user.id}")
        print('---------------------------------')
        self.change_status.start()
        print('Started change_status loop')
        self.birthday_check.start()
        print('Started birthday_check loop')
 
        print('---------------------------------')

    """
    @commands.Cog.listener()
    async def on_guild_join(guild):
        with open(os.path.join(DATA_DIR, 'prefix.json')) as f:
            prefixes = json.load(f)

        prefixes[str(guild.id)] = '.'

        with open(os.path.join(DATA_DIR, 'prefix.json'), 'w') as f:
            json.dump(prefixes, f)

    @commands.Cog.listener()
    async def on_message(self, msg):
        try:
            if msg.mentions == self.client.user:

                with open(os.path.join(DATA_DIR, 'prefix.json')) as f:
                    prefixes = json.load(f)

                pre = prefixes[str(msg.guild.id)]
                await msg.channel.send(f"My prefix is {pre}")
                await self.client.process_commands(msg)
        except:
            pass
        
    """
    @tasks.loop(hours=15)
    async def change_status(self):
        await self.client.change_presence(activity=discord.Game(next(status)))
        
    
    @tasks.loop(hours=24)
    async def birthday_check(self):
            await Birthday.check(self)

status = cycle(['bot stuff', 'Runescape', 'Minecraft', 'nyan cat'])

def setup(client):
    client.add_cog(listener(client))