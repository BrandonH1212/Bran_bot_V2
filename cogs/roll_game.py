import discord, random, asyncio
from discord.ext import commands
from BB_game import Game_message, Game


class roll_game_cog(
    commands.Cog):  # Cog object Use this for discord interactions for instance user input starting game
    def __init__(self, client):
        self.client = client
        self.game = None

    @commands.command()
    async def roll_game(self, ctx):  # Initial command used for Signing up
        if self.game is None:
            embed = discord.Embed(color=0x00ff59, title="BB Game | Roll Game", description="Click ✅ to sign up and 👌 to start the game!")
            msg = await ctx.send(embed=embed)
            self.game = roll_game(cog=self, g_message=roll_message(msg))
            await msg.add_reaction("✅")
            await msg.add_reaction("👌")
            await msg.add_reaction("✖")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):  # Player input command
        if self.game is not None and not payload.member.bot:
            if not self.game.started and str(payload.emoji) == "✅":
                user = await self.client.fetch_user(payload.user_id)
                await self.game.signup_player(payload.user_id, start_state={f'name': user.name})

        if self.game is not None and not payload.member.bot:
            if not self.game.started and str(payload.emoji) == "👌" and payload.user_id in self.game.players:
                if self.game.sign_up_count() < 2:
                    return
                await self.game.reset_players()
                await self.game.start_game()
                
            elif self.game.started and str(payload.emoji) == "🎲" and payload.user_id in self.game.players:
                await self.game.player_input(payload.user_id)
            
            elif not self.game.started and str(payload.emoji) == "✖" and payload.user_id in self.game.players:
                print("aa")
                await self.game.clear_reactions()
                self.game = None


class roll_game(Game):
    def __init__(self, max_players=10, loop_interval=5, g_message=None,
                 payer_state={"name": "", "rolled": False, "roll": 0}, time_out=500, cog=None):
        super().__init__(max_players, loop_interval, g_message, payer_state, time_out, cog)

    async def player_input(self, discord_ID, input={}):
        if not self.players[discord_ID]["rolled"]:
            self.players[discord_ID]["rolled"] = True
            self.players[discord_ID]["roll"] = random.randint(1, 100)

    def has_players_rolled(self):
        for player in self.players:
            if not self.players[player]["rolled"]:
                return False
        return True
        
    def sign_up_count(self):
        return len(self.players)
        
    async def clear_reactions(self):
        await self.g_message.message.clear_reactions()

    async def reset_players(self):
        for player in self.players:
            self.players[player]["rolled"] = False
            self.players[player]["roll"] = 0

        await self.g_message.message.clear_reactions()
        await self.g_message.message.add_reaction("🎲")

    async def check_end(self):

        if self.has_players_rolled():
            lowest = 101
            eliminated = []
            for player in self.players:

                if self.players[player]['roll'] == lowest:
                    eliminated.append(player)

                if self.players[player]['roll'] < lowest:
                    eliminated = [player]
                    lowest = self.players[player]['roll']

            await self.g_message.on_game_loop(self)
            await asyncio.sleep(5)

            if len(eliminated) > 1:
                self.round_msg = f"{', '.join(eliminated)} tied with {lowest}!"

            else:
                self.round_msg = f"{self.players[eliminated[0]]['name']} was eliminated with {lowest}!"
                del self.players[eliminated[0]]

            if len(self.players) < 2:
                return True

            await self.reset_players()

        return False


class roll_message(Game_message):
    def __init__(self, discord_message=None, discord_client=None):
        super().__init__(discord_message, discord_client)

    async def on_signup_player(self, game, response):
        embed = discord.Embed(color=0x00ff59, title="BB Game | Roll Game", description="Click ✅ to sign up and 👌 to start the game!")
        for player in game.players:
            embed.add_field(name=game.players[player]['name'], value="Signed up")
        await self.message.edit(embed=embed)

    async def on_game_loop(self, game):
        embed = discord.Embed(title="BB Game | Roll Game", description=game.round_msg)

        for player in game.players:
            if game.players[player]["rolled"]:
                embed.add_field(name=game.players[player]['name'], value=f"Rolled a {game.players[player]['roll']}")
            else:
                embed.add_field(name=game.players[player]['name'], value=f"Waiting for roll")

        await self.message.edit(embed=embed)

    async def on_end_game(self, game):
        player_id = list(game.players)[0]
        embed = discord.Embed(title="BB Game | Roll Game",
                              description=f"{game.players[player_id]['name']} won the game with a `{game.players[player_id]['roll']}`!")
        await self.message.edit(embed=embed)


def setup(client):  # Cog stuff will be called From main
    client.add_cog(roll_game_cog(client))
