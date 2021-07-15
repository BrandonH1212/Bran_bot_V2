import BB_utility, BB_db
from discord.ext import commands


class register_cog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = BB_db.db
        self.api = BB_db.api

    @commands.command(
        aliases=["reg", "link"],
        help="Links your osu username to discord\nUsage !reg osu_name",
        brief="Links your osu username to discord",
        usage="!reg osu_name")
    async def register(self, ctx, *input_name):
        osu_name = "_".join(BB_utility.sanitize_list(input_name).split())
        if len(osu_name) < 1:
            await ctx.send(f"Use `!link [osu_name]` to link your osu account")
            return
        elif len(osu_name) >= 15:
            await ctx.send(f"Name too long")
            return

        osu_user = await self.api.get_user(osu_name)
        if osu_user is None:
            await ctx.send(f"User {osu_name} not found on osu")
        else:
            if await self.db.register_player(ctx.author.name, ctx.author.id, osu_user.user_id):
                await ctx.send(f"Successfully Registered {ctx.author.name} on Discord with {osu_user.username} on osu")
            else:
                if await self.db.update_osu_id(ctx.author.id, osu_user.user_id):
                    await ctx.send(f"Successfully Updated {ctx.author.name} on Discord with {osu_user.username} on osu")
                else:
                    await ctx.send("Something <.< went wrong tell Brandon QUICK!")


def setup(client):
    client.add_cog(register_cog(client))
