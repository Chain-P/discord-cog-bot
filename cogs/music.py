import discord
from discord.ext import commands

from music.controller import MusicPlayer, extract_song


class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.players: dict[int, MusicPlayer] = {}

    def get_player(self, guild_id: int) -> MusicPlayer:
        if guild_id not in self.players:
            self.players[guild_id] = MusicPlayer(guild_id)
        return self.players[guild_id]

    @commands.hybrid_command(brief="Joins your voice channel")
    @commands.guild_only()
    async def join(self, ctx):
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("You need to be in a voice channel first.")
            return

        player = self.get_player(ctx.guild.id)
        channel = ctx.author.voice.channel

        if player.is_connected:
            await player.voice_client.move_to(channel)
        else:
            player.voice_client = await channel.connect()

        await ctx.send(f"Joined {channel.mention}")

    @commands.hybrid_command(brief="Leaves the voice channel")
    @commands.guild_only()
    async def leave(self, ctx):
        player = self.get_player(ctx.guild.id)
        if player.voice_client is None:
            await ctx.send("I'm not in a voice channel.")
            return

        player._cancel_idle_timer()
        await player.voice_client.disconnect()
        player.voice_client = None
        player.queue.clear()
        player.current = None
        await ctx.send("Left the voice channel.")

    @commands.hybrid_command(name='play', aliases=['p'], brief="Plays a song (URL or search)")
    @commands.guild_only()
    async def play(self, ctx, *, query: str):
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("You need to be in a voice channel first.")
            return

        player = self.get_player(ctx.guild.id)
        channel = ctx.author.voice.channel

        if not player.is_connected:
            player.voice_client = await channel.connect()
        elif player.voice_client.channel != channel:
            await player.voice_client.move_to(channel)

        async with ctx.typing():
            try:
                song = await extract_song(query, ctx.author, self.client.loop)
            except Exception as e:
                await ctx.send(f"Couldn't find or play that: {e}")
                return

        player.add(song)
        if player.is_playing:
            await ctx.send(f"Queued: **{song.title}**")
        else:
            await ctx.send(f"Now playing: **{song.title}**")
            player.play_next(self.client.loop)

    @commands.hybrid_command(brief="Pauses playback")
    @commands.guild_only()
    async def pause(self, ctx):
        player = self.get_player(ctx.guild.id)
        if player.voice_client is not None and player.voice_client.is_playing():
            player.voice_client.pause()
            await ctx.send("Paused.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.hybrid_command(brief="Resumes playback")
    @commands.guild_only()
    async def resume(self, ctx):
        player = self.get_player(ctx.guild.id)
        if player.voice_client is not None and player.voice_client.is_paused():
            player.voice_client.resume()
            await ctx.send("Resumed.")
        else:
            await ctx.send("Nothing is paused.")

    @commands.hybrid_command(brief="Skips the current song")
    @commands.guild_only()
    async def skip(self, ctx):
        player = self.get_player(ctx.guild.id)
        if player.voice_client is not None and (player.voice_client.is_playing() or player.voice_client.is_paused()):
            player.voice_client.stop()
            await ctx.send("Skipped.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.hybrid_command(brief="Stops playback, clears the queue, and leaves")
    @commands.guild_only()
    async def stop(self, ctx):
        player = self.get_player(ctx.guild.id)
        player.queue.clear()
        player.loop_current = False
        player._cancel_idle_timer()
        if player.voice_client is not None:
            await player.voice_client.disconnect()
            player.voice_client = None
        player.current = None
        await ctx.send("Stopped and cleared the queue.")

    @commands.hybrid_command(name='queue', aliases=['q'], brief="Shows the current queue")
    @commands.guild_only()
    async def queue_(self, ctx):
        player = self.get_player(ctx.guild.id)
        if player.current is None and not player.queue:
            await ctx.send("The queue is empty.")
            return

        lines = []
        if player.current is not None:
            lines.append(f"**Now playing:** {player.current.title} (requested by {player.current.requester_name})")
        for i, song in enumerate(player.queue, start=1):
            lines.append(f"{i}. {song.title} (requested by {song.requester_name})")

        await ctx.send("\n".join(lines))

    @commands.hybrid_command(name='nowplaying', aliases=['np'], brief="Shows the current song")
    @commands.guild_only()
    async def nowplaying(self, ctx):
        player = self.get_player(ctx.guild.id)
        if player.current is None:
            await ctx.send("Nothing is playing.")
            return
        await ctx.send(f"**Now playing:** {player.current.title} (requested by {player.current.requester_name})")

    @commands.hybrid_command(brief="Removes a song from the queue by position")
    @commands.guild_only()
    async def remove(self, ctx, index: int):
        player = self.get_player(ctx.guild.id)
        song = player.remove(index - 1)
        if song is None:
            await ctx.send("No song at that position.")
        else:
            await ctx.send(f"Removed: **{song.title}**")

    @commands.hybrid_command(brief="Shuffles the queue")
    @commands.guild_only()
    async def shuffle(self, ctx):
        player = self.get_player(ctx.guild.id)
        if not player.queue:
            await ctx.send("The queue is empty.")
            return
        player.shuffle()
        await ctx.send("Queue shuffled.")

    @commands.hybrid_command(brief="Toggles looping the current song")
    @commands.guild_only()
    async def loop(self, ctx):
        player = self.get_player(ctx.guild.id)
        player.loop_current = not player.loop_current
        await ctx.send(f"Loop {'enabled' if player.loop_current else 'disabled'}.")


async def setup(client):
    await client.add_cog(Music(client))
