from discord.ext import commands
import discord, random
from BB_game import Game, Game_message
from BB_utility import clamp, try_int


class game_roll(Game):
    def __init__(self, max_players=10, loop_interval=5, g_message=Game_message(),
                 game_vars={"roll": 0, 'can_roll': False, "name":''}, time_out=300, cog=None):
        super().__init__(max_players, loop_interval, g_message, game_vars, time_out, cog)

        self.state_message = "Game started!"
        self.round = 1
        self.showed_all_rolls = False

    async def start_game(self):
        self.started = True
        self.refresh_players()
        await self.game_loop()

    def did_players_roll(self):
        for player in self.players:
            if self.players[player]['can_roll']:
                return False
        return True

    async def eliminate_lowest_player(self):
        tie = False
        lowest = {"Player": '',
                  "roll": 100}

        for player in self.players:
            if self.players[player]['roll'] < lowest["roll"]:
                lowest['roll'] = self.players[player]['roll']
                lowest['Player'] = player
                tie = False
            elif self.players[player]['roll'] == lowest["roll"]:
                tie = True

        if not tie:
            user = await self.g_message.client.fetch_user(lowest['Player'])
            self.state_message = f"`{user.name}` Was eliminated better luck next time buddy!"
            del self.players[lowest['Player']]
            self.round += 1

        else:
            self.state_message = "The lowest is a tie.... WOW no players eliminated"

    def refresh_players(self):
        for player in self.players:
            self.players[player]['can_roll'] = True

    async def check_end(self):
        if len(self.players) < 2:
            return True

        elif self.did_players_roll():
            if self.showed_all_rolls:
                await self.eliminate_lowest_player()
                self.refresh_players()
                await self.g_message.message.clear_reactions()
                await self.g_message.message.add_reaction("🎲")
                self.showed_all_rolls = False
                self.time_out = 300
            else:
                self.showed_all_rolls = True

        elif self.time_out < 0:
            return True

        return False

    async def player_input(self, discord_ID, input={}):
        if discord_ID in self.players and self.players[discord_ID]['can_roll']:
            self.players[discord_ID]['can_roll'] = False
            self.players[discord_ID]['roll'] = random.randint(0, 100)
        return


class roll_message(Game_message):
    def __init__(self, discord_message, discord_client):
        super().__init__(discord_message, discord_client)

    async def on_signup_player(self, game, response):
        if response == "Signed up":
            embed = discord.Embed(
                title=f"BB GAME | Roll Game \nPlayers {len(game.players)}/{game.max_players}\n`Use 👍️ sign up`",
                description="Every round everyone rolls out of 100 whoever roles the lowest is eliminated",
                color=0x00ff59)
            for player in game.players:
                if game.players[player]["name"] == "":
                    user = await self.client.fetch_user(player)
                    game.players[player]["name"] = user.name

                embed.add_field(name=f"{game.players[player]['name']}", value=f"Signed up", inline=True)
            await self.message.edit(embed=embed)

        elif response == "Game starting":
            await self.message.clear_reactions()
            await self.message.add_reaction("🎲")
            await game.start_game()

    async def on_game_loop(self, game):
        embed = discord.Embed(
            title=f"BB GAME | Roll Game \nPlayers {len(game.players)}/{game.max_players}\nRound: {game.round}",
            description=f"{game.state_message}\n Timeout in {game.time_out}",
            color=0x00ff59)

        for player in game.players:
            if game.players[player]['can_roll']:
                embed.add_field(name=f"{game.players[player]['name']}", value=f"USE 🎲 to Roll!", inline=False)
            else:
                embed.add_field(name=f"{game.players[player]['name']}", value=f"Rolled `{game.players[player]['roll']}`", inline=True)

        await self.message.edit(embed=embed)

    async def on_end_game(self, game):
        await self.message.clear_reactions()
        for player in game.players:
            user = await self.client.fetch_user(player)
            embed = discord.Embed(
                title=f"BB GAME | Roll Game",
                description=f"Game ended!\nRounds: {game.round}\nWinning roll `{game.players[player]['roll']}`",
                color=0x00ff59)
            embed.set_author(name=f"{user.name} WINS!")

        await self.message.edit(embed=embed)


class roll_game(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.game = None

    @commands.command()
    async def play_roll_game(self, ctx, players=3):
        if try_int(players) == 0:
            return
        elif self.game is None:
            players = clamp(2, 20, players)
            embed = discord.Embed(title=f"BB GAME | Roll Game \nPlayers 0/{players}\n`Use 👍️ sign up`",
                                  description="Every round everyone rolls out of 100 whoever roles the lowest is eliminated",
                                  color=0x00ff59)
            msg = await ctx.send(embed=embed)
            self.game = game_roll(g_message=roll_message(discord_message=msg, discord_client=self.client),
                                  max_players=players, cog=self)
            await msg.add_reaction("👍")
            #await ctx.message.delete()

    @commands.command()
    async def start_roll_game(self, ctx):
        if self.game is not None:
            if ctx.author.id in self.game.players and len(self.game.players) > 1:
                await self.game.g_message.message.clear_reactions()
                await self.game.g_message.message.add_reaction("🎲")
                await self.game.start_game()


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.game is not None and not payload.member.bot:
            if not self.game.started and str(payload.emoji) == "👍":
                await self.game.signup_player(payload.member.id)

        if self.game is not None and not payload.member.bot:
            if self.game.started and str(payload.emoji) == "🎲" and payload.member.id in self.game.players:
                await self.game.player_input(discord_ID=payload.member.id)


def setup(client):
    client.add_cog(roll_game(client))
