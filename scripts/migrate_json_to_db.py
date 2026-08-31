"""One-time migration of the old JSON config files into the SQLite DB.

Run this against a deployed instance's real `data/` directory (the checked-in
copies in this repo are placeholder examples, not real data):

    python scripts/migrate_json_to_db.py

Idempotent — safe to re-run; existing rows are updated in place rather than
duplicated. Leaves the original JSON files untouched.
"""
import json
import os
import sys
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from settings import DATA_DIR
from db import Session, Birthday, init_db, get_or_create_guild_config


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"skip  {filename} (not found)")
        return {}
    with open(path) as f:
        return json.load(f)


def migrate_prefixes(session, data):
    for gid, prefix in data.items():
        config = get_or_create_guild_config(session, gid)
        config.prefix = prefix
        print(f"prefix        guild={gid} -> {prefix!r}")


def migrate_mod_roles(session, data):
    for gid, role_id in data.items():
        config = get_or_create_guild_config(session, gid)
        config.mod_role_id = str(role_id)
        print(f"mod_role      guild={gid} -> {role_id}")


def migrate_birthdays(session, data):
    channels = data.get('channels', {})
    for gid, cid in channels.items():
        config = get_or_create_guild_config(session, gid)
        config.birthday_channel_id = str(cid)
        print(f"bday_channel  guild={gid} -> {cid}")

    for gid, users in data.items():
        if gid == 'channels':
            continue
        for uid, raw_date in users.items():
            date = datetime.strptime(raw_date, '%m/%d/%Y').date()
            row = session.get(Birthday, (str(gid), str(uid)))
            if row is None:
                row = Birthday(guild_id=str(gid), user_id=str(uid), date=date)
                session.add(row)
            else:
                row.date = date
            print(f"birthday      guild={gid} user={uid} -> {date}")


def main():
    init_db()
    with Session() as session:
        migrate_prefixes(session, load_json('prefix.json'))
        migrate_mod_roles(session, load_json('mod_roles.json'))
        migrate_birthdays(session, load_json('servers_birthdays.json'))
        session.commit()
    print("\nMigration complete.")


if __name__ == "__main__":
    main()
