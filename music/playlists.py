from __future__ import annotations

from db import Session, Playlist, PlaylistSong
from music.controller import MAX_PLAYLIST_SONGS
from music.model import Song


def save_playlist(owner_id, name, songs: list[Song]):
    owner_id = str(owner_id)
    songs = songs[:MAX_PLAYLIST_SONGS]

    with Session() as session:
        playlist = session.query(Playlist).filter_by(owner_id=owner_id, name=name).first()
        if playlist is None:
            playlist = Playlist(owner_id=owner_id, name=name)
            session.add(playlist)
            session.flush()
        else:
            session.query(PlaylistSong).filter_by(playlist_id=playlist.id).delete()

        for i, song in enumerate(songs):
            session.add(PlaylistSong(
                playlist_id=playlist.id,
                position=i,
                title=song.title,
                webpage_url=song.webpage_url,
            ))
        session.commit()


def load_playlist(owner_id, name, requester) -> list[Song] | None:
    owner_id = str(owner_id)

    with Session() as session:
        playlist = session.query(Playlist).filter_by(owner_id=owner_id, name=name).first()
        if playlist is None:
            return None

        rows = (
            session.query(PlaylistSong)
            .filter_by(playlist_id=playlist.id)
            .order_by(PlaylistSong.position)
            .all()
        )
        return [
            Song(
                title=row.title,
                webpage_url=row.webpage_url,
                stream_url=None,
                duration=0,
                requester_id=requester.id,
                requester_name=requester.display_name,
            )
            for row in rows
        ]


def list_playlists(owner_id) -> list[tuple[str, int]]:
    owner_id = str(owner_id)

    with Session() as session:
        playlists = session.query(Playlist).filter_by(owner_id=owner_id).all()
        return [
            (p.name, session.query(PlaylistSong).filter_by(playlist_id=p.id).count())
            for p in playlists
        ]


def delete_playlist(owner_id, name) -> bool:
    owner_id = str(owner_id)

    with Session() as session:
        playlist = session.query(Playlist).filter_by(owner_id=owner_id, name=name).first()
        if playlist is None:
            return False
        session.query(PlaylistSong).filter_by(playlist_id=playlist.id).delete()
        session.delete(playlist)
        session.commit()
        return True
