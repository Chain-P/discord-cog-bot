import random

from .model import Birthday as bday
from utils import update_json, read_json
from settings import DATA_DIR
from datetime import datetime

# Tried in order; the first one that parses wins. Year-less formats default
# to 1900 (a quirk of strptime), which is fine here since only the month/day
# are ever used for the yearly birthday check.
BIRTHDAY_FORMATS = [
    '%m/%d/%Y',
    '%m-%d-%Y',
    '%Y-%m-%d',
    '%B %d, %Y',
    '%B %d %Y',
    '%b %d, %Y',
    '%b %d %Y',
    '%m/%d',
    '%m-%d',
    '%B %d',
    '%b %d',
]


class BirthdayTools:

    @staticmethod
    def parse_birthday(raw: str) -> str:
        raw = raw.strip()
        for fmt in BIRTHDAY_FORMATS:
            try:
                parsed = datetime.strptime(raw, fmt)
            except ValueError:
                continue
            return parsed.strftime('%m/%d/%Y')
        raise ValueError(
            "Couldn't parse that date. Try formats like `MM/DD/YYYY`, `MM/DD`, "
            "`YYYY-MM-DD`, or `January 7`."
        )

    @staticmethod
    async def save(gid, pid, birthday: str):
        dic = {f'{pid}':f'{birthday}'}
        data = read_json(DATA_DIR, 'servers_birthdays.json')
        for key in data.keys():
            if key == gid:
                data[key].update(dic)
            else:
                data = {f'{gid}': dic}

        update_json(data, DATA_DIR, 'servers_birthdays.json')

    @staticmethod
    async def check():
        check = False
        gild = {}
        current_time = datetime.now()
        data = read_json(DATA_DIR, 'servers_birthdays.json')
        for gid in data:
            for uid in data[gid].keys():
                date = data[gid][uid]
                if date[:-5] == current_time.strftime('%m/%d'):
                    check = True
                    gild[f'{uid}'] = f'{gid}'

        return check, gild

    @staticmethod
    def get_birthday_channel(gid):
        data = read_json(DATA_DIR, 'servers_birthdays.json')
        for guild in data['channels']:
            if gid == guild:
                return int(data['channels'][guild])

    @staticmethod
    def set_birthday_channel(gid, cid):
        data = read_json(DATA_DIR, 'servers_birthdays.json')

        dic = {f'{gid}':f'{cid}'}
        data['channels'].update(dic)
        print(f"Changed {gid}'s bday channel to {cid}")

        update_json(data, DATA_DIR, 'servers_birthdays.json')