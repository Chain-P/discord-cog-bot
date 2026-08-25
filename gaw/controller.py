import random

from .model import GuessAWord

games = {

}

class GuessAWordGame:
    
    current_game = None

    def fetch_game(self):
        return self.current_game
    
    def get_game(self, channel_id):
        self.current_game = None
        for key in games.keys():
            if channel_id == key:
                self.current_game = games[key]

    def guess(self, channel_id, guess):
        self.get_game(channel_id)
        if self.current_game is None:
            return None
        #Start the game
        return self.current_game.guess(guess)

    async def start_game(self, guild, author, players):
        """
        Starts a new game in a new channel, 
        """

        channel_name = f"gaw-game-{author.name}"
        existing_channel = self.get_channel_by_name(guild, channel_name)
        
        if existing_channel is None:
            channel = await self.create_channel(guild, channel_name)
            await self.set_permissions(guild, channel, players)

            new_game = GuessAWord(self.get_random_word())
            new_game.channel_id = channel.id
            new_game.channel_name = channel.name

            self.save(new_game)

            return channel
        
        return None

    def save(self, game):
        games[game.channel_id] = game

    def destroy(self, guild, channel_id):
        games.pop(channel_id)
        self.delete_channel(guild, channel_id)

    def delete_channel(self, guild, channel_id):
        channel = guild.get_channel(channel_id)
        channel.delete()

    async def create_channel(self, guild, channel_name):
        category =  self.get_category_by_name(guild, "Server Mods")
        await guild.create_text_channel(channel_name, category=category)
        channel = self.get_channel_by_name(guild, channel_name)

        return channel

    async def set_permissions(self, guild, channel, players):
        await channel.set_permissions(guild.default_role, view_channel=False, send_messages=False)

        for p in players:
            await channel.set_permissions(guild.default_role, view_channel=True, send_messages=True)

    def get_channel_by_name(self, guild,channel_name):
        channel = None
        for c in guild.channels:
            if c.name == channel_name.lower():
                channel = c
                break
        return channel
    
    def get_category_by_name(self, guild,category_name):
        category = None
        for c in guild.categories:
            if c.name == category_name:
                category = c
                break
        return category

    async def get_random_word(self):
        return random.choice('discord', 'python')