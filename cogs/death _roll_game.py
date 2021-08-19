import discord, random, asyncio
from discord.ext import commands
from BB_game import Game_message, Game
from BB_utility import convert_big_number


class death_roll_game_cog(
    commands.Cog):  # Cog object Use this for discord interactions for instance user input starting game
    def __init__(self, client):
        self.client = client
        self.game = None
        self.host = None
        self.host_name = None

    @commands.command()
    async def death_roll_game(self, ctx, rolls=1000):  # Initial command used for Signing up
        if self.game is None:
            embed = discord.Embed(color=0x00ff59, title="BB Game | Death Death Roll Game", description="Click ✅ to sign up and 👌 to start the game!")
            msg = await ctx.send(embed=embed)
            self.game = death_roll_game(cog=self, g_message=roll_message(msg), starting_roll=rolls)
            user = await self.client.fetch_user(ctx.author.id)
            self.host = user.id
            self.host_name = user.name
            await msg.add_reaction("✅")
            await msg.add_reaction("👌")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):  # Player input command
        if self.game is not None and not payload.member.bot:
            if not self.game.started and str(payload.emoji) == "✅":
                user = await self.client.fetch_user(payload.user_id)
                await self.game.signup_player(payload.user_id, start_state={f'name': user.name})

        if self.game is not None and not payload.member.bot:
            if not self.game.started and str(payload.emoji) == "👌" and payload.member.id == self.host:
                if self.game.sign_up_count() < 2:
                    return
                await self.game.start_game()

            elif self.game.started and str(payload.emoji) == "🎲" and payload.user_id in self.game.players:
                await self.game.player_input(payload.user_id)

            elif not self.game.started and str(payload.emoji) == "✖" and payload.user_id in self.game.players:
                await self.game.message.clear_reactions()
                await self.game.message.delete()
                self.game = None


class death_roll_game(Game):
    def __init__(self, max_players=10, loop_interval=4, g_message=None,
                 payer_state={"name": "", "roll": 0}, time_out=500, cog=None, starting_roll=1000):
        super().__init__(max_players, loop_interval, g_message, payer_state, time_out, cog)
        self.starting_roll = starting_roll
        self.last_roll = starting_roll
        self.current_player = 0
        self.roll_happened = False

    async def start_game(self):
        self.started = True
        await self.g_message.message.clear_reactions()
        await self.g_message.message.add_reaction("🎲")
        await self.game_loop()

    async def player_input(self, discord_ID, input={}):
        if self.get_current_player_id() == discord_ID and not self.roll_happened:
            self.players[discord_ID]["roll"] = random.randint(1, self.last_roll)
            self.last_roll = self.players[discord_ID]["roll"]
            self.roll_happened = True


    def sign_up_count(self):
        return len(self.players)

    def get_current_player_id(self):
        return list(self.players.keys())[self.current_player]

    async def check_end(self):
        if self.roll_happened:
            if self.last_roll == 1:
                self.round_msg = f"{self.players[self.get_current_player_id()]['name']} Rolled 1 and was eliminated"
                del self.players[self.get_current_player_id()]
                self.roll_happened = False
                self.last_roll = self.starting_roll
                self.current_player = 0
            else:
                self.round_msg = f"{self.players[self.get_current_player_id()]['name']} Is safe :O"
                self.roll_happened = False

            self.current_player += 1

            if len(self.players) < 2:
                return True

            if len(self.players) == self.current_player:
                self.current_player = 0

            await self.g_message.message.clear_reactions()
            await self.g_message.message.add_reaction("🎲")

        return False



class roll_message(Game_message):
    def __init__(self, discord_message=None, discord_client=None):
        super().__init__(discord_message, discord_client)

    async def on_signup_player(self, game, response):
        embed = discord.Embed(color=0x00ff59, title="BB Game | Death Roll Game", description="Click ✅ to sign up and 👌 to start the game!")
        for player in game.players:
            embed.add_field(name=game.players[player]['name'], value="Signed up")
        await self.message.edit(embed=embed)

    async def on_game_loop(self, game):
        embed = discord.Embed(title=f"BB Game | Death Roll Game | Now Rolling 1-{convert_big_number(game.last_roll)}", description=f'First one to 1 loses \n{game.round_msg}')

        for player in game.players:
            if game.get_current_player_id() == player:
                embed.add_field(name=game.players[player]['name'], value=">> 🎲 <<")
            else:
                embed.add_field(name=game.players[player]['name'], value=f'Rolled {convert_big_number(game.players[player]["roll"])}')
        await self.message.edit(embed=embed)

    async def on_end_game(self, game):
        player_id = list(game.players)[0]
        embed = discord.Embed(title="BB Game | Death Roll Game",
                              description=f"{game.round_msg} {game.players[player_id]['name']}  wins!")
        await self.message.clear_reactions()
        await self.message.edit(embed=embed)


def setup(client):  # Cog stuff will be called From main
    client.add_cog(death_roll_game_cog(client))
