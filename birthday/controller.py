
from db import Session, Birthday, GuildConfig, get_or_create_guild_config
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
        gid = str(gid)
        pid = str(pid)
        date = datetime.strptime(birthday, '%m/%d/%Y').date()
        with Session() as session:
            row = session.get(Birthday, (gid, pid))
            if row is None:
                row = Birthday(guild_id=gid, user_id=pid, date=date)
                session.add(row)
            else:
                row.date = date
            session.commit()

    @staticmethod
    def remove(gid, pid) -> bool:
        gid = str(gid)
        pid = str(pid)
        with Session() as session:
            row = session.get(Birthday, (gid, pid))
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    @staticmethod
    async def check():
        check = False
        gild = {}
        current_time = datetime.now()
        with Session() as session:
            for row in session.query(Birthday).all():
                if row.date.strftime('%m/%d') == current_time.strftime('%m/%d'):
                    check = True
                    gild[row.user_id] = row.guild_id

        return check, gild

    @staticmethod
    def get_birthday_channel(gid):
        with Session() as session:
            config = session.get(GuildConfig, str(gid))
            if config is None or config.birthday_channel_id is None:
                return None
            return int(config.birthday_channel_id)

    @staticmethod
    def set_birthday_channel(gid, cid):
        with Session() as session:
            config = get_or_create_guild_config(session, gid)
            config.birthday_channel_id = str(cid)
            session.commit()
        print(f"Changed {gid}'s bday channel to {cid}")