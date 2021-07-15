from discord.ext import commands
import discord, asyncio
from BB_game import Game, Game_message
import random, BB_db
from BB_utility import simp_num, clamp


class br_game(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.game = None
        self.db = BB_db.db
        self.api = BB_db.api

    async def start_loop(self, time, msg):
        time = time
        while time > 0 and not self.game.started:
            await asyncio.sleep(5)
            time -= 5

            embed = discord.Embed(title=f"BB GAME | OSU Battle Royale | Starts in {int(time//60)}:{int(time%60)} \n`Use ☠ to sign up`",
                                  description="Players will fight on osu maps until there is only one remaining",
                                  color=0x00ff59)

            for player in self.game.players:
                embed.add_field(name=f"{self.game.players[player]['name']}", value="Signed up", inline=True)
            await msg.edit(embed=embed)

        if len(self.game.players) > 1:
            await self.game.start_game()
        else:
            await msg.edit(content="Not enough players....Game Canceled :(", embed=None)
            self.game = None
            await msg.clear_reactions()

    @commands.command()
    async def play_br(self, ctx, time=60, star=4, step=0.4):
        if self.game is None:
            embed = discord.Embed(title="BB GAME | OSU Battle Royale \n`Use ☠ to sign up`",
                                  description="Players will fight on osu maps until there is only one remaining",
                                  color=0x00ff59)
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("☠")
            self.game = game_br(g_message=br_message(discord_client=self.client, discord_message=msg), cog=self, max_players=100, star_start=star, step=step)
            await self.start_loop(time, msg)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.game is not None and not payload.member.bot:
            if not self.game.started and str(payload.emoji) == "☠":
                if await self.db.get_player(payload.member.id) is not None:
                    user = await self.client.fetch_user(payload.member.id)
                    await self.game.signup_player(payload.member.id, start_state={'name': user.name})
                else:
                    pass

        if self.game is not None and not payload.member.bot:
            if self.game.started and str(payload.emoji) == "🔄":
                if await self.db.get_player(payload.member.id) is not None:
                    await self.game.player_input(discord_ID=payload.member.id)
                else:
                    pass

        if self.game is not None and not payload.member.bot:
            if self.game.started and str(payload.emoji) == "✅":
                if payload.member.id in self.game.players:
                    self.game.players[payload.member.id]["skip"] = True
                    print("hype")
                else:
                    pass


class game_br(Game):
    def __init__(self, max_players=5, loop_interval=15, g_message=Game_message(),
                 game_vars={"submitted": False, "score": 0, "name": "", "last_check": 0, "sub_num": 0, "skip": False}, time_out=500, cog=None, star_start=4, step=0.4):
        super().__init__(max_players, loop_interval, g_message, game_vars, time_out, cog)
        self.round = star_start
        self.active_map = None
        self.api = self.cog.api
        self.round_message = "Round one Good luck!"
        self.round_over = False
        self.step = step
        self.round_results = []

    async def start_game(self):
        self.started = True
        await self.new_round()
        await self.game_loop()

    async def new_round(self):
        for player in self.players:
            self.players[player]["score"] = 0
            self.players[player]["submitted"] = False
            self.players[player]["last_check"] = 0
            self.players[player]["sub_num"] = 0
            self.players[player]["skip"] = False

        map_query = await self.cog.db.get_maps(star_r=[self.round + (self.step / 4), self.round + self.step],
                                               len_r=[85, 270])
        print(map_query)
        self.active_map = map_query[-1]
        self.time_out = 2 * self.active_map.total_length + max(45, self.active_map.total_length * 0.15)
        self.round_over = False
        self.round = self.active_map.difficultyrating
        await self.g_message.message.clear_reactions()
        await self.g_message.message.add_reaction("🔄")
        await self.g_message.message.add_reaction("✅")


    async def player_input(self, discord_ID, input={}):
        if discord_ID in self.players:
            if self.players[discord_ID]["last_check"] != self.time_out:
                player = await self.cog.db.get_player(discord_ID)
                recent = await player.get_recent(10)
                print(f"{self.players[discord_ID]['name']} Check")
                for play in recent:
                    self.check_recent(discord_ID, play)

    def check_recent(self, discord_ID, recent):

        self.players[discord_ID]["last_check"] = self.time_out

        if recent.beatmap_id == self.active_map.beatmap_id:
            if recent.score > self.players[discord_ID]["score"]:
                self.players[discord_ID]["score"] = recent.score
                self.players[discord_ID]["submitted"] = True
                self.players[discord_ID]["sub_num"] += 1


    async def check_end(self):
        skip = True

        for player in self.players:
            if not self.players[player]["skip"]:
                skip = False

        if skip:
            self.time_out = 0


        if len(self.players) < 2:
            self.round_message = "Game over"
            return True

        elif self.time_out < 1:
            eliminated = []

            if not self.round_over: # If this is the first time we detected the round ending show the scores
                self.round_over = True
                for player in self.players:
                    await self.player_input(player)
                return False

            else:
                for player in self.players: # Check if Players did not submit
                    if not self.players[player]["submitted"]:
                        eliminated.append(player)

                if len(eliminated) > 0:  # Eliminate players that didn't submit
                    self.round_message = f"{eliminated} Did not submit and got eliminated!"
                    self.round_results.append(f"{self.players[player]['name']} eliminated on {self.game.active_map.title}")

                else:
                    # Check and compare players scores
                    lowest = 10000000000000000000

                    for player in self.players:
                        if self.players[player]["score"] == lowest:
                            self.round_message = f"A tie was detected quick panic!"
                            await self.new_round()
                            return False

                        if self.players[player]["score"] < lowest:
                            eliminated = [player]
                            lowest = self.players[player]["score"]
                            self.round_results.append(f"{self.players[player]['name']} eliminated on {self.game.active_map.title}")
                            self.round_message = f'{self.players[player]["name"]} Was eliminated'


                for player in eliminated:
                    del self.players[player]

                await self.new_round()
                return False


class br_message(Game_message):
    def __init__(self, discord_message=None, discord_client=None):
        super().__init__(discord_message, discord_client)

    async def on_game_loop(self, game):
        b_map = game.active_map
        embed = discord.Embed(title=f"{b_map.title} [{b_map.version}]", url=f"https://osu.ppy.sh/b/{b_map.beatmap_id}/", description=f"`Check play 🔄`  | `Finished Playing  ✅` | [beatconnect](https://beatconnect.io/b/{b_map.beatmapset_id}/) \n⭐ {round(b_map.difficultyrating,2)} | Length: {int(b_map.hit_length//60)}:{int(b_map.hit_length%60)} | BPM: {int(b_map.bpm)}\n{game.round_message}")
        embed.set_author(name=f"OSU Battle Royale! | Time remaining: {int(game.time_out//60)}:{int(game.time_out%60)}")
        embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{b_map.beatmapset_id}/covers/cover.jpg")

        for player in game.players:
            if not game.round_over:
                skip_emoji = ''
                if game.players[player]['skip']:
                    skip_emoji = "`✅`"
                if game.players[player]['submitted']:
                    embed.add_field(name=f"{game.players[player]['name']} {skip_emoji}", value=f"{game.players[player]['sub_num']} plays submitted!", inline=True)
                else:
                    embed.add_field(name=f"{game.players[player]['name']} {skip_emoji}", value="Waiting for submission...", inline=True)
            else:
                embed.add_field(name=f"{game.players[player]['name']}", value=f"Score: {game.players[player]['score']}", inline=True)

        embed.set_footer(text=f"Map_id: {b_map.beatmap_id} | Set_id: {b_map.beatmapset_id}")
        await self.message.edit(embed=embed)

    async def on_end_game(self, game):
        b_map = game.active_map
        player_id = list(game.players)[0]
        description = "Placements!\n"
        for i, place in enumerate(game.round_results):
            description += f"{i+1}\n{place}"

        embed = discord.Embed(title=f"OSU Battle Royale! | Game Over",
                              description=description)
        embed.set_author(
            name=f"Congratulations to the winner!\n{game.players[player_id]['name']}")

        await self.message.edit(embed=embed)

def setup(client):
    client.add_cog(br_game(client))
