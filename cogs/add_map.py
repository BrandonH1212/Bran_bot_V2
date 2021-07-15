import discord, asyncio
import BB_utility, BB_db
from discord.ext import commands
from BB_utility import parse_id


class cog_add_map(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = BB_db.db
        self.map_qe = []
        self.map_qe_message = None

    @commands.Cog.listener()
    async def on_ready(self):
        await self.qe_loop()


    @commands.command()
    async def add_map(self, ctx, *map_ids):
        added = []
        already_in_DB = []
        invalid = 0
        for maps in map_ids:
            input_name = parse_id(maps)
            if parse_id(input_name) is not None:
                if await self.db.is_set_or_map_in_db(input_name):
                    already_in_DB.append(input_name)
                elif input_name not in self.map_qe:
                    added.append(input_name)
                    self.map_qe.append(input_name)
            else:
                invalid += 1

        if self.map_qe_message is None:
            await ctx.send(f"added {added}\n"
                     f"already in DB {already_in_DB}"
                     f"invalid maps {invalid}")
            map_qe_message = await ctx.send("...")
            self.map_qe_message = map_qe_message
        else:
            await ctx.send(f"added {added}\n"
                     f"already in DB {already_in_DB}"
                     f"invalid maps {invalid}")

    async def qe_loop(self):
        while True:
            await asyncio.sleep(4)

            if len(self.map_qe) == 0:
                if self.map_qe_message is not None:
                    await self.map_qe_message.edit(content="finished processing all maps")
                    self.map_qe_message = None
            else:

                if self.map_qe_message is not None:
                    await self.map_qe_message.edit(
                        content=f"{len(self.map_qe)} maps remaining currently processing {self.map_qe[0]}")

                map = await self.db.is_set_or_map_in_db(map_id=self.map_qe[0], use_osu_api=True)
                self.map_qe.remove(self.map_qe[0])
                print(f"finished {map}")



def setup(client):
    client.add_cog(cog_add_map(client))
