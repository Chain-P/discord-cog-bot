from __future__ import annotations

import asyncio
import random
from collections import deque

import discord
import yt_dlp

from .model import Song

YTDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch1',
    'skip_download': True,
}

FFMPEG_BEFORE_OPTIONS = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'

IDLE_TIMEOUT_SECONDS = 300


def _extract(query: str) -> dict:
    with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info


async def extract_song(query: str, requester: discord.Member, loop: asyncio.AbstractEventLoop) -> Song:
    info = await loop.run_in_executor(None, _extract, query)
    return Song(
        title=info.get('title', 'Unknown title'),
        webpage_url=info.get('webpage_url', query),
        stream_url=info['url'],
        duration=info.get('duration') or 0,
        requester_id=requester.id,
        requester_name=requester.display_name,
    )


class MusicPlayer:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue: deque[Song] = deque()
        self.voice_client: discord.VoiceClient | None = None
        self.current: Song | None = None
        self.loop_current = False
        self._idle_task: asyncio.Task | None = None

    @property
    def is_playing(self) -> bool:
        return self.voice_client is not None and (
            self.voice_client.is_playing() or self.voice_client.is_paused()
        )

    def _cancel_idle_timer(self):
        if self._idle_task is not None:
            self._idle_task.cancel()
            self._idle_task = None

    def _start_idle_timer(self, bot_loop: asyncio.AbstractEventLoop):
        self._cancel_idle_timer()

        async def _idle_disconnect():
            await asyncio.sleep(IDLE_TIMEOUT_SECONDS)
            if self.voice_client is not None:
                await self.voice_client.disconnect()
                self.voice_client = None

        self._idle_task = bot_loop.create_task(_idle_disconnect())

    def play_next(self, bot_loop: asyncio.AbstractEventLoop):
        if self.voice_client is None:
            return

        if self.loop_current and self.current is not None:
            song = self.current
        elif self.queue:
            song = self.queue.popleft()
        else:
            self.current = None
            self._start_idle_timer(bot_loop)
            return

        self._cancel_idle_timer()
        self.current = song
        source = discord.FFmpegPCMAudio(song.stream_url, before_options=FFMPEG_BEFORE_OPTIONS)

        def _after(error):
            if error:
                print(f"Playback error: {error}")
            bot_loop.call_soon_threadsafe(self.play_next, bot_loop)

        self.voice_client.play(source, after=_after)

    def add(self, song: Song):
        self.queue.append(song)

    def remove(self, index: int) -> Song | None:
        if 0 <= index < len(self.queue):
            q = list(self.queue)
            song = q.pop(index)
            self.queue = deque(q)
            return song
        return None

    def shuffle(self):
        q = list(self.queue)
        random.shuffle(q)
        self.queue = deque(q)
