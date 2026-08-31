"""Discord OAuth2 Authorization Code flow, on behalf of the logged-in user."""
import requests

API_BASE = "https://discord.com/api/v10"
ADMINISTRATOR = 0x8


def build_authorize_url(client_id, redirect_uri, state):
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'identify guilds',
        'state': state,
    }
    query = '&'.join(f'{k}={requests.utils.quote(str(v))}' for k, v in params.items())
    return f'{API_BASE}/oauth2/authorize?{query}'


def exchange_code(client_id, client_secret, redirect_uri, code):
    resp = requests.post(
        f'{API_BASE}/oauth2/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    resp.raise_for_status()
    return resp.json()


def get_current_user(access_token):
    resp = requests.get(f'{API_BASE}/users/@me', headers={'Authorization': f'Bearer {access_token}'})
    resp.raise_for_status()
    return resp.json()


def get_user_guilds(access_token):
    resp = requests.get(f'{API_BASE}/users/@me/guilds', headers={'Authorization': f'Bearer {access_token}'})
    resp.raise_for_status()
    return resp.json()


def is_administrator(guild):
    return (int(guild['permissions']) & ADMINISTRATOR) != 0
