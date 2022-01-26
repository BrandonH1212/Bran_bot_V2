import random
import discord, asyncio, time, random
from discord.ext import commands
from discord.ext.commands.core import Command
from BB_utility import get_user_emoji


# This cog is for the game "Closest guess"
# The game is a simple guessing game where the user has to guess a number
# Users type a number and that will be their guests number the bot will update the Message to show everyone's guesses

class Closest_guess(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.game_running = False
        self.game_channel = None
        self.game_gases = {} # {user_id: {avatar: emoji, guess: 0}}
        self.message = None
        self.time_limit = 60
        self.target_number = 0

    @commands.command("Closestguess")
    async def closest_guess(self, ctx, *args):
        """
        This is the main command for the game.
        This will start the game and wait for the game loop to finish before ending the game.
        This will also set target number two a random number between 1 and 100.
        """
        if self.game_running:
            await ctx.send("There is already a game running in this channel.")
            return
        self.game_running = True
        self.game_channel = ctx.channel
        self.target_number = random.randint(1, 100)

        # So everything looks good were going to use embeds to show the game

        embed = discord.Embed(title="Closest Guess", description="Guess a number between 1 and 100", color=0x00ff00)
        embed.set_footer(text="This game will end in 60 seconds")
        self.message = await ctx.send(embed=embed)
        await self.game_loop()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel != self.game_channel:
            return
        # try: # This is to make sure the message is a number
        
    
        if message.content.isdigit():
            if message.author.id in self.game_gases:
                self.game_gases[message.author.id]["guess"] = int(message.content)
                await self.update_message()
            else:
                self.game_gases[message.author.id] = {"avatar": await get_user_emoji(self.client, message.author), "guess": min(int(message.content), 100)}
                await self.update_message()

            await message.delete()

    async def game_loop(self):
        """
        This is the main loop of the game.
        This will update the game message every second and check if the game has ended.
        when someone types a number it will add them to the game_gases dict.
        """
        while self.game_running:
            await self.update_message()
            await asyncio.sleep(1)
            if self.time_limit == 0:
                await self.end_game()

        await self.end_game()

    
    async def update_message(self):
        """
        This will update the game message every second.
        This will also check if the game has ended.
        """
        self.time_limit -= 1
        embed = discord.Embed(title="Closest Guess", description="Guess a number between 1 and 100 just type a number to guess", color=0x00ff00)
        embed.set_footer(text="This game will end in {} seconds".format(self.time_limit))
        for user_id in self.game_gases:
            embed.add_field(name=self.game_gases[user_id]["avatar"], value="{}".format(self.game_gases[user_id]["guess"]), inline=False)
        await self.message.edit(embed=embed)

    async def end_game(self):
        """
        This will end the game and reset the game_running variable.
        This will show everyone's guesses and the target number. 
        and show the winner at the top in the title of the embed.
        """
        self.game_running = False
        embed = discord.Embed(title="Closest Guess Game over", description="Congratulations to the winner! \n{} ".format(self.game_gases[min(self.game_gases, key=lambda x: abs(self.game_gases[x]["guess"] - self.target_number))]["avatar"]), color=0x00ff00)
        embed.set_footer(text="The target number was {}".format(self.target_number))
        for user_id in self.game_gases:
            embed.add_field(name=self.game_gases[user_id]["avatar"], value="{}".format(self.game_gases[user_id]["guess"]), inline=False)
        await self.message.edit(embed=embed)

        self.game_gases = {}
        self.game_channel = None
        self.message = None
        self.time_limit = 60
        self.target_number = 0


def setup(client):
    client.add_cog(Closest_guess(client))