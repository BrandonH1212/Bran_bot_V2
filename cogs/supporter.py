import BB_utility
from discord.ext import commands


class supporter(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def sup(self, ctx, input_num):
        input_num = BB_utility.try_int(input_num)
        if input_num > 0:
            await ctx.send(content=BB_utility.supporter_amount(input_num))


def setup(client):
    client.add_cog(supporter(client))
