import asyncio


class Game_message:
    def __init__(self, discord_message=None, discord_client=None):
        self.message = discord_message
        self.client = discord_client

    async def on_signup_player(self, game, response):
        pass

    async def on_game_loop(self, game):
        pass

    async def on_end_game(self, game):
        pass


class Game:
    def __init__(self, max_players=10, loop_interval=3, g_message=None, payer_state={"name": ""}, time_out=500, cog=None):
        self.max_players = max_players
        self.g_message = g_message
        self.loop_interval = loop_interval
        self.default_player_state = payer_state
        self.players = {}  # Discord_ID : {game_state}
        self.time_out = time_out
        self.cog = cog
        self.started = False
        self.round_msg = ''

    async def game_loop(self):
        while not await self.check_end():
            await self.g_message.on_game_loop(game=self)
            await asyncio.sleep(self.loop_interval)
            self.time_out -= self.loop_interval

        await self.g_message.on_end_game(game=self)
        await self.end_game()

    async def signup_player(self, player_id, start_state=None, remove=False, ignore_started=False):
        if self.started and not ignore_started:
            return

        elif remove and player_id in self.players:
            del self.players[player_id]
            await self.g_message.on_signup_player(game=self, response="Player left")
            return "Player left"

        elif player_id not in self.players:
            self.players[player_id] = self.default_player_state.copy()
            if start_state is not None:
                for k in start_state:
                    self.players[player_id][k] = start_state[k]
            if len(self.players) >= self.max_players:
                await self.g_message.on_signup_player(game=self, response="Game starting")
                return "Game starting"

            else:
                await self.g_message.on_signup_player(game=self, response="Signed up")
                return "Signed up"

    async def start_game(self):
        self.started = True
        await self.game_loop()


    async def check_end(self):
        return False  # Overwrite for your custom game logic

    async def end_game(self):
        await self.g_message.on_end_game(game=self)
        self.ended = True
        self.cog.game = None

    async def player_input(self, discord_ID, input={}):
        if discord_ID in self.players:
            pass
        pass


