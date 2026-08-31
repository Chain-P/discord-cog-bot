import os
import secrets
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from flask import Flask, session, redirect, request, render_template, abort, url_for
import requests

from settings import (
    DISCORD_BOT_TOKEN, DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET,
    DASHBOARD_REDIRECT_URI, FLASK_SECRET_KEY, DASHBOARD_PORT, DEFAULT_PREFIX,
)
from db import Session, GuildConfig, init_db
from utils import set_prefix, set_moderator_role
from birthday.controller import BirthdayTools
from discord_oauth import build_authorize_url, exchange_code, get_current_user, get_user_guilds, is_administrator
from discord_api import get_bot_guilds, get_guild_roles, get_guild_text_channels

# Runs as its own process from the bot's — don't assume main.py has already
# created the schema. init_db() is idempotent (CREATE TABLE IF NOT EXISTS).
init_db()

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
# Secure cookies require HTTPS; only turn this on when the redirect URI actually
# is https (i.e. not the plain-http://localhost local dry-run setup).
app.config['SESSION_COOKIE_SECURE'] = DASHBOARD_REDIRECT_URI.startswith('https')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


def logged_in_admin_guilds():
    """Guilds the logged-in user administers AND the bot is actually in."""
    user_guilds = get_user_guilds(session['access_token'])
    bot_guilds = get_bot_guilds(DISCORD_BOT_TOKEN)
    return [
        {'id': g['id'], 'name': bot_guilds[g['id']]}
        for g in user_guilds
        if is_administrator(g) and g['id'] in bot_guilds
    ]


@app.route('/')
def index():
    if 'access_token' not in session:
        return render_template('login.html')
    try:
        guilds = logged_in_admin_guilds()
    except requests.HTTPError:
        session.clear()
        return redirect(url_for('index'))
    return render_template('guilds.html', guilds=guilds, username=session.get('username'))


@app.route('/login')
def login():
    state = secrets.token_urlsafe(24)
    session['oauth_state'] = state
    return redirect(build_authorize_url(DISCORD_CLIENT_ID, DASHBOARD_REDIRECT_URI, state))


@app.route('/callback')
def callback():
    if request.args.get('state') != session.pop('oauth_state', None):
        abort(400, "Invalid OAuth state")
    code = request.args.get('code')
    if not code:
        abort(400, "Missing OAuth code")

    token_data = exchange_code(DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DASHBOARD_REDIRECT_URI, code)
    session['access_token'] = token_data['access_token']
    session['username'] = get_current_user(session['access_token'])['username']
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def require_guild_admin(gid):
    if 'access_token' not in session:
        abort(401)
    admin_guild_ids = {g['id'] for g in logged_in_admin_guilds()}
    if gid not in admin_guild_ids:
        abort(403)


@app.route('/guild/<gid>', methods=['GET'])
def guild_settings(gid):
    require_guild_admin(gid)

    with Session() as db_session:
        config = db_session.get(GuildConfig, gid)
        current_prefix = config.prefix if config and config.prefix else DEFAULT_PREFIX
        current_mod_role_id = config.mod_role_id if config else None

    return render_template(
        'guild.html',
        gid=gid,
        current_prefix=current_prefix,
        current_mod_role_id=current_mod_role_id,
        current_birthday_channel_id=BirthdayTools.get_birthday_channel(gid),
        roles=get_guild_roles(DISCORD_BOT_TOKEN, gid),
        channels=get_guild_text_channels(DISCORD_BOT_TOKEN, gid),
    )


@app.route('/guild/<gid>', methods=['POST'])
def update_guild_settings(gid):
    require_guild_admin(gid)

    prefix = request.form.get('prefix', '').strip()
    if prefix:
        set_prefix(gid, prefix)

    mod_role_id = request.form.get('mod_role_id', '')
    if mod_role_id:
        set_moderator_role(gid, mod_role_id)

    birthday_channel_id = request.form.get('birthday_channel_id', '')
    if birthday_channel_id:
        BirthdayTools.set_birthday_channel(gid, birthday_channel_id)

    return redirect(url_for('guild_settings', gid=gid))


if __name__ == '__main__':
    cert_path = os.path.join(ROOT_DIR, 'dashboard', 'certs', 'cert.pem')
    key_path = os.path.join(ROOT_DIR, 'dashboard', 'certs', 'key.pem')

    # Plain HTTP for local dry-run testing against the http://localhost redirect
    # URI; the self-signed cert (generated once on the Pi) switches this to HTTPS
    # for real use over the ZeroTier network.
    if os.path.exists(cert_path):
        app.run(host='0.0.0.0', port=DASHBOARD_PORT, ssl_context=(cert_path, key_path))
    else:
        app.run(host='0.0.0.0', port=DASHBOARD_PORT)
