import typing

from discord.ext import commands
from rps.model import RPS
from rps.controller import RPSGame

from hangman.controller import HangmanGame

hangman_games = {}

word = "discord"
user_guesses = list()

class Games(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_command(usage="rock | paper | scissor", brief="Play Rock Paper Scissors against the bot")
    async def rps(self, ctx, user_choice: typing.Literal["rock", "paper", "scissor"] = RPS.ROCK):
        """
        Play a game of Rock Paper Scissors

        Either choose rock, paper or scissor and beat the bot

        You cannot challenge another user. It's vs the bot only!
        """

        game_instance = RPSGame()

        won, bot_choice = game_instance.run(user_choice)
        
        if won is None:
            message = f"It's a draw! Double {user_choice}s"
        elif won is True:
            message = f"You win: {user_choice} vs. {bot_choice}"
        elif won is False:
            message = f"You lose: {user_choice} vs. {bot_choice}"


        await ctx.send(message)

    @commands.hybrid_command(brief="Play Hangman - guess a letter of the secret word")
    async def hm(self, ctx, guess: str):
        player_id = ctx.author.id
        hangman_instance = HangmanGame()
        game_over, won = hangman_instance.run(player_id, guess)


        if game_over:
            game_over_message = "You did not won"
            if won:
                game_over_message = "Congrats you won!!!"

            game_over_message = game_over_message + f" The word was {hangman_instance.get_secret_word()}"
            await hangman_instance.reset(player_id)
            await ctx.send(game_over_message)
            
        else:
            await ctx.send(f"Progress: {hangman_instance.get_progress_string()}")
            await ctx.send(f"Guess so for: {hangman_instance.get_guess_string()}")

async def setup(client):
    await client.add_cog(Games(client))