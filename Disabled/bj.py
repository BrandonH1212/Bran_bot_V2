import discord, random, asyncio
from discord.ext import commands
from bb_game import Game, Game_message

card_vals = {"A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "k": 10, "Q": 10}

class bj_game_cog(
    commands.Cog):  # Cog object Use this for discord interactions for instance user input starting game
    def __init__(self, client):
        self.client = client
        self.game = None

    @commands.command()
    async def bj(self, ctx):  # Initial command used for Signing up
        if self.game is None:
            embed = discord.Embed(title="BB Game | bj", description="Sub description")
            msg = await ctx.send(embed=embed)
            self.game = roll_game(cog=self, g_message=roll_message(msg))


    @commands.command()
    async def bet(self, ctx, num):
        pass

    @commands.command()
    async def hit(self, ctx):
        pass

    @commands.command()
    async def stand(self, ctx):
        pass

    @commands.command()
    async def example_start_roll_game(self, ctx):  # Force start command
        pass

    #@commands.Cog.listener()
    #async def on_raw_reaction_add(self, payload):  # Player input command
        #if self.game is not None and not payload.member.bot:
            #if not self.game.started and str(payload.emoji) == "✔":
                #user = await self.client.fetch_user(payload.user_id)
                #await self.game.signup_player(payload.user_id, start_state={f'name': user.name})

        #if self.game is not None and not payload.member.bot:
            #if not self.game.started and str(payload.emoji) == "👌" and payload.user_id in self.game.players:
               # await self.game.reset_players()
                #await self.game.start_game()

        #if self.game is not None and not payload.member.bot:
          #  if self.game.started and str(payload.emoji) == "🎲" and payload.user_id in self.game.players:
               # await self.game.player_input(payload.user_id)


class roll_game(Game):
    def __init__(self, max_players=10, loop_interval=5, g_message=None,
                 payer_state={"name": "", "played": False, "hand": [], "money": 100, "total": 0}, time_out=500, cog=None):
        super().__init__(max_players, loop_interval, g_message, payer_state, time_out, cog)
        self.self.dick = []

    # BJ STUFF
    def new_dick(self ,size=10):
        keys = list(card_vals.keys())
        for self.dicks in range(size):
            for i in keys:
                self.dick.append(i)
        random.shuffle(self.dick)

    def update_total(self, player):
        player["total"] = 0
        if len(player["hand"]) > 0:
            for cards in player["hand"]:
                player["total"] += card_vals[cards]
        return

    def draw_card(self, player):
        player["hand"].append(self.dick.pop(0))
        self.update_total(player)

    def dealer_play(self, dealer):
        if dealer["total"] < 15:
            self.player_input(dealer, 1)

        if dealer["total"] > 21:
            print("bust")

    async def player_input(self, discord_ID, input={}):
        if not self.players[discord_ID]["played"]:
            self.players[discord_ID]["played"] = True

    def has_players_played(self):
        for player in self.players:
            if not self.players[player]["played"]:
                return False
        return True

    async def reset_players(self):
        for player in self.players:
            self.players[player]["played"] = False

        await self.g_message.message.clear_reactions()
        await self.g_message.message.add_reaction("🎲")

    async def check_end(self):

        return False


class roll_message(Game_message):
    def __init__(self, discord_message=None, discord_client=None):
        super().__init__(discord_message, discord_client)

    async def on_signup_player(self, game, response):
        embed = discord.Embed(title="BB Game | Roll Game", description="Sub description")
        for player in game.players:
            embed.add_field(name=game.players[player]['name'], value="Signed up")
        await self.message.edit(embed=embed)

    async def on_game_loop(self, game):
        embed = discord.Embed(title="BB Game | Roll Game", description=game.round_msg)

        for player in game.players:
            if game.players[player]["played"]:
                embed.add_field(name=game.players[player]['name'], value=f"played a {game.players[player]['roll']}")
            else:
                embed.add_field(name=game.players[player]['name'], value=f"Waiting for roll")

        await self.message.edit(embed=embed)

    async def on_end_game(self, game):
        player_id = list(game.players)[0]
        embed = discord.Embed(title="BB Game | Roll Game",
                              description=f"{game.players[player_id]['name']} won the game with a `{game.players[player_id]['roll']}`!")
        await self.message.edit(embed=embed)


def setup(client):  # Cog stuff will be called From main
    client.add_cog(bj_game_cog(client))
