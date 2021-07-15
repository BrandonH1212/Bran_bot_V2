from discord.ext import commands
import discord, asyncio, random
from BB_game import Game, Game_message
import BB_db, BB_utility
from BB_utility import simp_num, get_mods


class game_pp(Game):
    def __init__(self, max_players=100, loop_interval=5, g_message=Game_message(), game_vars={"guess": 0, "name": ""},
                 osu_play=None, osu_player_name=""):
        super().__init__(max_players, loop_interval, g_message, game_vars)
        self.osu_player_name = osu_player_name
        self.osu_play = osu_play
        self.osu_map = None
        self.timer = 60
        self.pp = 0
        self.mapinfo = []

    async def start_game(self, api):
        self.osu_map = await api.get_beatmap(beatmap_id=self.osu_play.beatmap_id)
        self.pp = self.osu_play.pp
        self.started = True
        self.mapinfo = [[["Rank: "], [self.osu_play.rank]], [["300Count: "], [self.osu_play.count300]],
                        [["100Count: "], [self.osu_play.count100]], [["50Count: "], [self.osu_play.count50]],
                        [["MissCount: "], [self.osu_play.countmiss]], [["Combo: "], [self.osu_play.maxcombo]],
                        [["score"], [simp_num(self.osu_play.score)]],
                        [["mods"], [get_mods(self.osu_play.enabled_mods)]]]
        random.shuffle(self.mapinfo)
        await self.game_loop()

    async def check_end(self):
        self.timer -= self.loop_interval
        if self.timer == 0:
            return True
        else:
            return False


class guess_message(Game_message):
    def __init__(self, discord_message, client, cog):
        super().__init__(discord_message)
        self.InfoLevel = 0
        self.client = client
        self.cog = cog

    async def on_game_loop(self, game):
        shown_info = ""
        for i, info in enumerate(game.mapinfo):
            if int(self.InfoLevel) > i and i - 1 < len(game.mapinfo):
                shown_info += f"`{info[0][0]} {info[1][0]}`|"

        embed = discord.Embed(title=f"BB GAME | Guess PP\nTime left: {game.timer}",
                              description=f"New information Every 10 seconds\n Use `!g <num>` to guess")
        embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{game.osu_map.beatmapset_id}/covers/cover.jpg")
        embed.add_field(
            name=f"{game.osu_player_name}'s Play\n{game.osu_map.title} ⭐{round(game.osu_map.difficultyrating, 2)}",
            value=f"Score info Level: {int(self.InfoLevel)}!\n{shown_info}", inline=False)
        try:
            for player in game.players:
                embed.add_field(name=f"{game.players[player]['name']}", value=f"`DID Guess`", inline=True)
            await self.message.edit(embed=embed)
        except:
            pass
        self.InfoLevel += 0.5

    async def on_end_game(self, game):
        winners = get_closest(game.players, game.pp)
        guess = ''
        winning_message = ""
        if len(winners) < 1:
            winning_message = "NO ONE!"
        else:
            for win in winners:
                user = await self.client.fetch_user(win)
                winning_message += f"{user.name} "
                guess = f"Guess was {game.players[win]['guess']}"

        embed = discord.Embed(title="BB GAME | Guess PP\nGame ended!",
                              description=f"The play was worth `{game.pp}` PP!")
        for player in game.players:
            user = await self.client.fetch_user(player)
            embed.add_field(name=f"{user.name}", value=f"`Guess: {game.players[player]['guess']}`", inline=True)

        embed.set_author(name=f"{winning_message} WINS! {guess}")
        embed.add_field(
            name=f"{game.osu_player_name}'s Play on \n{game.osu_map.title} ⭐{round(game.osu_map.difficultyrating, 2)}",
            value=f"The Difficulty was {game.osu_map.version}", inline=False)
        await self.message.edit(embed=embed)
        self.cog.game = None


class Guess_pp_game(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.game = None
        self.db = BB_db.db
        self.api = BB_db.api

    @commands.command()
    async def play_guess_pp(self, ctx, time=10, input_name=''):
        time = min(20, max(2, int(time)))
        if self.game is None:
            osu_name = input_name

            if len(osu_name) >= 15:
                await ctx.send(f"Name too long")
                return

            osu_user = await self.api.get_user(osu_name)
            if osu_user is None:
                r_player = random.choice(await self.db.get_all_players())
            else:
                r_player = BB_db.Player(name=osu_user.username, osu_id=osu_user.user_id)

            embed = discord.Embed(title=f"BB GAME | Guess PP \nStarting in {int(time)} Seconds",
                                  description="gets a random top 100 score from a player in the database"
                                              "\nthen you have to guess how much PP it was"
                                              "\nwhoever guesses it or gets the closest in 1 minute wins"
                                              "\n Use `!link [osu_name]` if you're not in the database ",
                                  color=0x00ff59)

            msg = await ctx.send(embed=embed)
            play = await self.get_play(r_player)

            await asyncio.sleep(time)
            if self.game is None:
                self.game = game_pp(g_message=guess_message(discord_message=msg, client=self.client, cog=self),
                                    osu_play=play,
                                    osu_player_name=r_player.name)
                await self.game.start_game(api=self.api)

    @commands.command(aliases=["guess", "g"])
    async def guess_pp(self, ctx, guess=0):
        try:
            if self.game is not None:

                if ctx.author.id not in self.game.players:
                    await self.game.signup_player(ctx.author.id, ignore_started=True)
                    self.game.players[ctx.author.id]["guess"] = int(0)
                    user = await self.client.fetch_user(ctx.author.id)
                    self.game.players[ctx.author.id]["name"] = user.name

                self.game.players[ctx.author.id]["guess"] = int(min(2000, max(0, int(guess))))
                print(self.game.players[ctx.author.id]["guess"])
            await ctx.message.delete()
        except:
            await ctx.message.delete()

    async def get_play(self, player):
        return random.choice(await player.get_best(99))


def get_closest(dic, val):
    closest = 10000
    keys = []

    if len(dic.keys()) < 2:
        return list(dic.keys())

    for k in dic:
        distance = abs(dic[k]['guess'] - round(val))
        if distance == closest:
            keys.append(k)
        elif distance < closest:
            keys = [k]
            closest = distance

    # winner = min(dic, key=lambda k: abs(k['guess'] - val))
    # winners = [dic[k] for k, val in dic.values() if val == winner['guess']]

    return keys


def setup(client):
    client.add_cog(Guess_pp_game(client))
