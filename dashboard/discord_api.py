"""Discord REST calls made as the bot itself (Authorization: Bot ...), for data
the user's OAuth2 token can't provide: which guilds the bot is actually in, and
each guild's roles/channels for the settings-form dropdowns.
"""
import requests

API_BASE = "https://discord.com/api/v10"
GUILD_TEXT_CHANNEL = 0


def _bot_headers(bot_token):
    return {'Authorization': f'Bot {bot_token}'}


def get_bot_guilds(bot_token):
    """Returns {guild_id: guild_name} for every guild the bot is a member of."""
    resp = requests.get(f'{API_BASE}/users/@me/guilds', headers=_bot_headers(bot_token))
    resp.raise_for_status()
    return {g['id']: g['name'] for g in resp.json()}


def get_guild_roles(bot_token, guild_id):
    resp = requests.get(f'{API_BASE}/guilds/{guild_id}/roles', headers=_bot_headers(bot_token))
    resp.raise_for_status()
    return [{'id': r['id'], 'name': r['name']} for r in resp.json() if r['name'] != '@everyone']


def get_guild_text_channels(bot_token, guild_id):
    resp = requests.get(f'{API_BASE}/guilds/{guild_id}/channels', headers=_bot_headers(bot_token))
    resp.raise_for_status()
    return [{'id': c['id'], 'name': c['name']} for c in resp.json() if c['type'] == GUILD_TEXT_CHANNEL]
