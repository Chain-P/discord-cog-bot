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
    # YouTube's web client increasingly needs a PO token / JS challenge
    # solver that isn't set up here; the android client sidesteps that
    # and reliably returns a playable stream without one.
    'extractor_args': {'youtube': {'player_client': ['android']}},
}

FFMPEG_BEFORE_OPTIONS = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'

IDLE_TIMEOUT_SECONDS = 300
EMPTY_CHANNEL_TIMEOUT_SECONDS = 15


def has_human_members(channel) -> bool:
    return any(not m.bot for m in channel.members)


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
        self._empty_channel_task: asyncio.Task | None = None
        # Text channel of whatever command last connected/played, so an
        # unexpected reconnect failure has somewhere to report to.
        self.last_text_channel: discord.abc.Messageable | None = None

    @property
    def is_connected(self) -> bool:
        return self.voice_client is not None and self.voice_client.is_connected()

    @property
    def is_playing(self) -> bool:
        return self.is_connected and (
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
            # Clear voice_client *before* awaiting disconnect -- disconnect()
            # stops playback, which fires the after-callback, which schedules
            # play_next(). Clearing this first means play_next() sees no
            # voice_client and no channel to reconnect to, instead of racing
            # into a reconnect attempt for a disconnect we caused on purpose.
            vc, self.voice_client = self.voice_client, None
            if vc is not None:
                await vc.disconnect()

        self._idle_task = bot_loop.create_task(_idle_disconnect())

    def _cancel_empty_channel_timer(self):
        if self._empty_channel_task is not None:
            self._empty_channel_task.cancel()
            self._empty_channel_task = None

    def start_empty_channel_timer(self, bot_loop: asyncio.AbstractEventLoop):
        self._cancel_empty_channel_timer()

        async def _disconnect_if_still_empty():
            await asyncio.sleep(EMPTY_CHANNEL_TIMEOUT_SECONDS)
            vc, self.voice_client = self.voice_client, None
            if vc is not None:
                await vc.disconnect()

        self._empty_channel_task = bot_loop.create_task(_disconnect_if_still_empty())

    async def _attempt_reconnect(self, channel, bot_loop: asyncio.AbstractEventLoop):
        try:
            self.voice_client = await channel.connect()
        except Exception as e:
            if self.last_text_channel is not None:
                await self.last_text_channel.send(
                    f"Lost connection to voice and couldn't reconnect: {e}"
                )
            return
        self.play_next(bot_loop)

    def play_next(self, bot_loop: asyncio.AbstractEventLoop):
        if not self.is_connected:
            # Discord can tear down the voice session on its own (session
            # migration, timeout, etc.) without any of our commands running.
            # If voice_client is still set here, it's a dead reference --
            # if one of our own intentional-disconnect paths had already run,
            # they'd have cleared it to None before this point (see above),
            # so reaching here with a channel means this was unintentional.
            channel = self.voice_client.channel if self.voice_client is not None else None
            self.voice_client = None
            self._cancel_idle_timer()
            self._cancel_empty_channel_timer()

            if self.current is not None:
                self.queue.appendleft(self.current)
                self.current = None

            if channel is not None and has_human_members(channel):
                bot_loop.create_task(self._attempt_reconnect(channel, bot_loop))
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
