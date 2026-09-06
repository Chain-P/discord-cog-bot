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
# Single-pass loudness normalization (EBU R128) so songs mastered at very
# different volumes don't jump between quiet and loud -- two-pass would be
# more accurate but requires fully analyzing each song before playback could
# start. I/LRA/TP are ffmpeg's own documented sane defaults, not tuned here.
FFMPEG_OPTIONS = '-af loudnorm=I=-16:LRA=11:TP=-1.5'

IDLE_TIMEOUT_SECONDS = 300
EMPTY_CHANNEL_TIMEOUT_SECONDS = 15
MAX_PLAYLIST_SONGS = 100
RECONNECT_DELAY_SECONDS = 3
DEFAULT_LOOP_QUEUE = True
MAX_ZERO_FRAME_RETRIES = 1

# Fast, metadata-only listing -- used first to find out whether a query is a
# real playlist or a single video/search, without paying the cost of
# resolving every entry's actual playable stream (which extract_flat skips).
PROBE_OPTS = {
    **YTDL_OPTS,
    'extract_flat': 'in_playlist',
}


def has_human_members(channel) -> bool:
    return any(not m.bot for m in channel.members)


def _extract(query: str) -> dict:
    with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info


def _probe(query: str) -> dict:
    with yt_dlp.YoutubeDL(PROBE_OPTS) as ydl:
        return ydl.extract_info(query, download=False)


async def probe(query: str, loop: asyncio.AbstractEventLoop) -> dict:
    return await loop.run_in_executor(None, _probe, query)


def is_real_playlist(info: dict) -> bool:
    # A 1-result search is *also* represented as a 1-entry "playlist" by
    # yt-dlp, so 'entries' in info isn't enough on its own -- the extractor
    # field is what actually distinguishes a search from a real playlist.
    return 'entries' in info and not (info.get('extractor') or '').endswith(':search')


async def extract_song(query: str, requester: discord.Member, loop: asyncio.AbstractEventLoop) -> Song:
    info = await loop.run_in_executor(None, _extract, query)
    return Song(
        title=info.get('title', 'Unknown title'),
        webpage_url=info.get('webpage_url', query),
        # Resolved lazily instead, right before playing (see
        # _play_next_async) -- caching it here can go stale by the time a
        # song near the back of a busy queue actually gets played.
        stream_url=None,
        duration=info.get('duration') or 0,
        requester_id=requester.id,
        requester_name=requester.display_name,
    )


def playlist_songs(info: dict, requester: discord.Member) -> list[Song]:
    songs = []
    for entry in list(info.get('entries', []))[:MAX_PLAYLIST_SONGS]:
        url = entry.get('url')
        if not url:
            continue
        songs.append(Song(
            title=entry.get('title', 'Unknown title'),
            webpage_url=url,
            stream_url=None,
            duration=entry.get('duration') or 0,
            requester_id=requester.id,
            requester_name=requester.display_name,
        ))
    return songs


async def resolve_stream(webpage_url: str, loop: asyncio.AbstractEventLoop) -> dict:
    return await loop.run_in_executor(None, _extract, webpage_url)


class _CountingFFmpegPCMAudio(discord.FFmpegPCMAudio):
    # discord.py's own ffmpeg-failure detection is racy: it only reports an
    # error if the process has already been reaped by the time a short read
    # is noticed, which a near-instant failure (e.g. a rejected stream URL)
    # often beats. Counting frames actually read gives a reliable signal
    # instead. Only ever touched from AudioPlayer's single background
    # thread, which finishes running before `after` is called from that same
    # thread -- no lock needed.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frames_read = 0

    def read(self) -> bytes:
        data = super().read()
        if data:
            self.frames_read += 1
        return data


class MusicPlayer:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue: deque[Song] = deque()
        self.voice_client: discord.VoiceClient | None = None
        self.current: Song | None = None
        self.loop_current = False
        self.loop_queue = DEFAULT_LOOP_QUEUE
        # Songs that have already played, kept only while loop_queue is on so
        # a finished queue can be reshuffled and replayed from the top.
        self.history: deque[Song] = deque()
        self._idle_task: asyncio.Task | None = None
        self._empty_channel_task: asyncio.Task | None = None
        # Text channel of whatever command last connected/played, so an
        # unexpected reconnect failure has somewhere to report to.
        self.last_text_channel: discord.abc.Messageable | None = None
        # One-shot flags consumed by _play_next_async, set by skip()/
        # remove_current() to force advancing past an active loop_current
        # instead of replaying it, and to control whether the departing
        # song stays in the loop_queue rotation.
        self._force_advance = False
        self._advance_keep_in_rotation = True
        self._pending_retry_task: asyncio.Task | None = None

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
        # Reconnecting immediately races Discord's gateway still tearing down
        # the old session (the just-finished disconnect sends its own "leave"
        # state change) -- observed live as a ~30s hang ending in a timeout
        # instead of a normal connect. A short delay lets that settle first.
        await asyncio.sleep(RECONNECT_DELAY_SECONDS)

        try:
            self.voice_client = await channel.connect()
        except Exception as e:
            print(f"Reconnect to voice failed: {e!r}")
            if self.last_text_channel is not None:
                try:
                    await self.last_text_channel.send(
                        f"Lost connection to voice and couldn't reconnect: {e}"
                    )
                except Exception as send_error:
                    print(f"Also failed to report the reconnect failure: {send_error!r}")
            return
        await self._play_next_async(bot_loop)

    def play_next(self, bot_loop: asyncio.AbstractEventLoop):
        bot_loop.create_task(self._play_next_async(bot_loop))

    async def _play_next_async(self, bot_loop: asyncio.AbstractEventLoop):
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
                await self._attempt_reconnect(channel, bot_loop)
            return

        # A forced advance (skip/remove_current) bypasses loop_current for
        # this one transition only -- it never touches the flag itself, so a
        # still-on loop_current applies again once the bot reaches whatever
        # song comes next.
        force_advance, self._force_advance = self._force_advance, False
        keep_in_rotation, self._advance_keep_in_rotation = self._advance_keep_in_rotation, True
        use_loop_current = self.loop_current and self.current is not None and not force_advance

        if not use_loop_current and self.current is not None and self.loop_queue and keep_in_rotation:
            self.history.append(self.current)

        # Loop past any queued songs that fail to resolve (deleted video,
        # region lock, etc.) instead of one bad playlist entry killing
        # everything behind it.
        song = None
        while True:
            if use_loop_current:
                song = self.current
            elif self.queue:
                song = self.queue.popleft()
            elif self.loop_queue and self.history:
                # The whole queue just finished -- reshuffle everything
                # that's played so far and go again from the top.
                refill = list(self.history)
                random.shuffle(refill)
                self.queue = deque(refill)
                self.history.clear()
                song = self.queue.popleft()
            else:
                self.current = None
                self._start_idle_timer(bot_loop)
                return

            if song.stream_url is not None:
                break

            try:
                info = await resolve_stream(song.webpage_url, bot_loop)
            except Exception as e:
                if self.last_text_channel is not None:
                    await self.last_text_channel.send(
                        f"Skipping **{song.title}** -- couldn't load it: {e}"
                    )
                continue

            song.stream_url = info['url']
            song.duration = info.get('duration') or song.duration
            song.title = info.get('title') or song.title
            break

        self._play_song(bot_loop, song)

    def _play_song(self, bot_loop: asyncio.AbstractEventLoop, song: Song, attempt: int = 0):
        self._cancel_idle_timer()
        self.current = song
        source = _CountingFFmpegPCMAudio(song.stream_url, before_options=FFMPEG_BEFORE_OPTIONS, options=FFMPEG_OPTIONS)

        def _after(error):
            bot_loop.call_soon_threadsafe(self._on_playback_done, bot_loop, song, source, attempt, error)

        self.voice_client.play(source, after=_after)

    def _on_playback_done(
        self,
        bot_loop: asyncio.AbstractEventLoop,
        song: Song,
        source: _CountingFFmpegPCMAudio,
        attempt: int,
        error,
    ):
        # An intentional stop (skip/remove_current) or a song that actually
        # produced audio is never a failure -- just move on normally.
        if self._force_advance or source.frames_read > 0:
            self.play_next(bot_loop)
            return

        print(f"Playback produced no audio for '{song.title}' (attempt {attempt + 1}): {error}")

        if attempt >= MAX_ZERO_FRAME_RETRIES:
            if self.last_text_channel is not None:
                bot_loop.create_task(self.last_text_channel.send(
                    f"Skipping **{song.title}** -- couldn't load it: {error or 'no audio was produced'}"
                ))
            self.play_next(bot_loop)
            return

        self._pending_retry_task = bot_loop.create_task(self._retry_song(bot_loop, song, attempt + 1))

    async def _retry_song(self, bot_loop: asyncio.AbstractEventLoop, song: Song, attempt: int):
        if not self.is_connected:
            self._pending_retry_task = None
            self.play_next(bot_loop)
            return

        try:
            info = await resolve_stream(song.webpage_url, bot_loop)
        except Exception as e:
            self._pending_retry_task = None
            if self.last_text_channel is not None:
                await self.last_text_channel.send(f"Skipping **{song.title}** -- couldn't reload it: {e}")
            self.play_next(bot_loop)
            return

        song.stream_url = info['url']
        song.duration = info.get('duration') or song.duration
        song.title = info.get('title') or song.title
        self._pending_retry_task = None
        self._play_song(bot_loop, song, attempt=attempt)

    def skip(self, bot_loop: asyncio.AbstractEventLoop) -> bool:
        if self._pending_retry_task is not None:
            self._pending_retry_task.cancel()
            self._pending_retry_task = None
            self._force_advance = True
            self._advance_keep_in_rotation = True
            self.play_next(bot_loop)
            return True
        if self.voice_client is None or not (self.voice_client.is_playing() or self.voice_client.is_paused()):
            return False
        self._force_advance = True
        self._advance_keep_in_rotation = True
        self.voice_client.stop()
        return True

    def remove_current(self, bot_loop: asyncio.AbstractEventLoop) -> Song | None:
        song = self.current
        if song is None:
            return None
        self._force_advance = True
        self._advance_keep_in_rotation = False
        if self._pending_retry_task is not None:
            self._pending_retry_task.cancel()
            self._pending_retry_task = None
            self.play_next(bot_loop)
        elif self.voice_client is not None and (self.voice_client.is_playing() or self.voice_client.is_paused()):
            self.voice_client.stop()
        else:
            self.current = None
            self.play_next(bot_loop)
        return song

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
