import random
import os
import json

from settings import DATA_DIR, DEFAULT_PREFIX
from discord.ext import commands

from db import Session, GuildConfig, get_or_create_guild_config



async def notify_user(member, message):
    if member is not None:
            channel = member.dm_channel
            if channel is None:
                channel = await member.create_dm()
            await channel.send(message)

async def get_apologies():
    with open(os.path.join(DATA_DIR, 'apologies.json')) as f:
        apologies = json.load(f)
    apology = random.choice(list(apologies))
    return apology

#Gets a joke from jokes.json in the data folder and returns it
async def get_momma_jokes():
    with open(os.path.join(DATA_DIR, "jokes.json")) as joke_file:
        jokes = json.load(joke_file)
    random_cat = random.choice(list(jokes.keys()))
    insult = random.choice(list(jokes[random_cat]))
    return insult

#Function to check if command invoker is a mod or the owner
def mods_or_owner():
    async def predicate(ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        if ctx.guild is None:
            return False
        if ctx.author.guild_permissions.administrator:
            return True
        mod_role_id = get_moderator_role(ctx.guild.id)
        if mod_role_id is None:
            return False
        return any(role.id == mod_role_id for role in ctx.author.roles)
    return commands.check(predicate)

#Per-guild moderator role, set via the setmodrole admin command
def get_moderator_role(gid):
    with Session() as session:
        config = session.get(GuildConfig, str(gid))
        if config is None or config.mod_role_id is None:
            return None
        return int(config.mod_role_id)

def set_moderator_role(gid, role_id):
    with Session() as session:
        config = get_or_create_guild_config(session, gid)
        config.mod_role_id = str(role_id)
        session.commit()


#OWO command backbone
vowels = ['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U']

def last_replace(s, old, new):
    li = s.rsplit(old, 1)
    return new.join(li)

def text_to_owo(text):
    """ Converts your text to OwO """
    smileys = [';;w;;', '^w^', '>w<', 'UwU', '(・`ω\´・)', '(´・ω・\`)']

    text = text.replace('L', 'W').replace('l', 'w')
    text = text.replace('R', 'W').replace('r', 'w')

    text = last_replace(text, '!', '! {}'.format(random.choice(smileys)))
    text = last_replace(text, '?', '? owo')
    text = last_replace(text, '.', '. {}'.format(random.choice(smileys)))

    for v in vowels:
        if 'n{}'.format(v) in text:
            text = text.replace('n{}'.format(v), 'ny{}'.format(v))
        if 'N{}'.format(v) in text:
            text = text.replace('N{}'.format(v), 'N{}{}'.format('Y' if v.isupper() else 'y', v))

    return text

def get_prefix(bot, message):
    if message.guild is None:
        return DEFAULT_PREFIX

    with Session() as session:
        config = session.get(GuildConfig, str(message.guild.id))
        if config is None or config.prefix is None:
            return DEFAULT_PREFIX
        return config.prefix

def set_prefix(gid, prefix):
    with Session() as session:
        config = get_or_create_guild_config(session, gid)
        config.prefix = prefix
        session.commit()

def read_json(dir, file):
    #Opens file to data
    
    with open(os.path.join(dir, file), 'r') as f:
        #Populates data with f
        return json.loads(f.read())
    #Returns data

