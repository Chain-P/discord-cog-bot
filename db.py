import os

from sqlalchemy import create_engine, Column, String, Date
from sqlalchemy.orm import declarative_base, sessionmaker

from settings import DATABASE_URL

Base = declarative_base()

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


class GuildConfig(Base):
    __tablename__ = 'guild_config'

    guild_id = Column(String, primary_key=True)
    prefix = Column(String, nullable=True)
    mod_role_id = Column(String, nullable=True)
    birthday_channel_id = Column(String, nullable=True)


class Birthday(Base):
    __tablename__ = 'birthdays'

    guild_id = Column(String, primary_key=True)
    user_id = Column(String, primary_key=True)
    date = Column(Date, nullable=False)


def init_db():
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL[len('sqlite:///'):]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    Base.metadata.create_all(engine)


def get_or_create_guild_config(session, gid):
    config = session.get(GuildConfig, str(gid))
    if config is None:
        config = GuildConfig(guild_id=str(gid))
        session.add(config)
    return config
