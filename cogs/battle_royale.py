from discord.ext import commands
import discord, asyncio
from BB_game import Game, Game_message
import random, BB_db
from BB_utility import simp_num, clamp, convert_time, convert_big_number


class br_game(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.game = None
        self.db = BB_db.db
        self.api = BB_db.api
        self.host = None
        self.host_name = None

    async def start_loop(self, msg):
        while self.game is not None:
            if not self.game.started:
                embed = discord.Embed(title=f"BB GAME | osu! Battle Royale | Host: {self.host_name}\nUse `☠` to sign up, host use`👌` to start the game!",
                                      description="Players will fight on osu maps until there is only one remaining",
                                      color=0x00ff59)

                for player in self.game.players:
                    embed.add_field(name=f"{self.game.players[player]['name']}", value="Signed up", inline=True)
                await msg.edit(embed=embed)

                await asyncio.sleep(3)
            else:
                return

    @commands.command()
    async def play_br(self, ctx, star=4, step=0.4):
        if self.game is None:
            embed = discord.Embed(title="BB GAME | osu! Battle Royale \nUse `☠` to sign up and `👌` to start the game!",
                                  description="Players will fight on osu maps until there is only one remaining",
                                  color=0x00ff59)
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("☠")
            await msg.add_reaction("👌")
            await msg.add_reaction("✖")
            self.game = game_br(g_message=br_message(discord_client=self.client, discord_message=msg), cog=self, max_players=100, star_start=star, step=step)
            user = await self.client.fetch_user(ctx.author.id)
            self.host = user.id
            self.host_name = user.name
            await self.start_loop(msg)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.game is not None and not payload.member.bot:
            if not self.game.started and str(payload.emoji) == "☠":
                if await self.db.get_player(payload.member.id) is not None:
                    user = await self.client.fetch_user(payload.member.id)
                    await self.game.signup_player(payload.member.id, start_state={'name': user.name})
                else:
                    pass

            if self.game.started and str(payload.emoji) == "🔄":
                if await self.db.get_player(payload.member.id) is not None:
                    await self.game.player_input(discord_ID=payload.member.id)
                else:
                    pass
                  
            if self.game.started and str(payload.emoji) == "✅":
                if payload.member.id in self.game.players:
                    self.game.players[payload.member.id]["skip"] = True
                    print("hype")
                else:
                    pass
                    
            if not self.game.started and str(payload.emoji) == "👌" and payload.member.id == self.host:
                if len(self.game.players) < 2:
                    return
                await self.game.start_game()
            
            if not self.game.started and str(payload.emoji) == "✖" and payload.member.id == self.host:
                await self.game.clear_reactions()
                self.game = None


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
        self.time_out = 2 * self.active_map.length + max(45, self.active_map.length * 0.15)
        self.round_over = False
        self.round = self.active_map.star_rating
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
                    self.round_message = f"{self.players[player]['name']} did not submit and got eliminated!"
                    self.round_results.append(f"{self.players[player]['name']} eliminated on {self.active_map.title}")

                else:
                    # Check and compare players scores
                    lowest = 10000000000000000000

                    for player in self.players:
                        if self.players[player]["score"] == lowest:
                            self.round_message = f"A tie was detected! No one is eliminated!"
                            await self.new_round()
                            return False

                        if self.players[player]["score"] < lowest:
                            eliminated = [player]
                            lowest = self.players[player]["score"]
                            self.round_results.append(f"{self.players[player]['name']} eliminated on {self.active_map.title}")
                            self.round_message = f'{self.players[player]["name"]} was eliminated!'


                for player in eliminated:
                    del self.players[player]

                await self.new_round()
                return False
                
    async def clear_reactions(self):
        await self.g_message.message.clear_reactions()


class br_message(Game_message):
    def __init__(self, discord_message=None, discord_client=None):
        super().__init__(discord_message, discord_client)

    async def on_game_loop(self, game):
        b_map = game.active_map
        embed = discord.Embed(title=f"{b_map.artist} - {b_map.title} [{b_map.version}]",
                              url=f"https://osu.ppy.sh/b/{b_map.beatmap_id}/",
                              description=f"Refresh play `🔄` | Finished Playing  `✅`\n"
                                          f"[beatconnect](https://beatconnect.io/b/{b_map.beatmapset_id}/)\n"
                                          f"{round(b_map.star_rating, 2)}★ | Length: {convert_time(b_map.length)} | BPM: {b_map.bpm}"
                                          f" | CS{b_map.cs} AR{b_map.ar} OD{b_map.od} HP{b_map.hp}\n{game.round_message}")
        embed.set_author(name=f"osu! Battle Royale! | Time remaining: {convert_time(game.time_out)}")
        embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{b_map.beatmapset_id}/covers/cover.jpg")
        embed.set_footer(text=f"Beatmap ID: {b_map.beatmap_id} | Set ID: {b_map.beatmapset_id}")
        
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
                embed.add_field(name=f"{game.players[player]['name']}", value=f"Score: {convert_big_number(game.players[player]['score'])}", inline=True)
        await self.message.edit(embed=embed)

    async def on_end_game(self, game):
        b_map = game.active_map
        player_id = list(game.players)[0]
        embed = discord.Embed(title=f"osu! Battle Royale! | Game Over", description="Placements")
        for i, place in enumerate(game.round_results):
            embed.add_field(name=f"#{i+1}.", value=f"{place}")
            
        embed.set_author(name=f"Congratulations to {game.players[player_id]['name']} for winning!")

        await self.message.edit(embed=embed)

def setup(client):
    client.add_cog(br_game(client))
