import discord
import BB_utility, BB_db
from discord.ext import commands
from BB_utility import simp_num


class osu_cog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = BB_db.db
        self.api = BB_db.api

    @commands.command(
        aliases=["OSU", "Osu"],
        help="displays Linked account information")
    async def osu(self, ctx, *input_name):
        if len(input_name) > 0:
            osu_name = "_".join(BB_utility.sanitize_list(input_name).split())
            osu_user = await self.db.get_player_form_osu(osu_name)
            if osu_user is None:
                await ctx.send(f"User {osu_name} not found on osu!")
            else:
                player = BB_db.Player(osu_name, None, osu_user.user_id)
        else:
            player = await self.db.get_player(ctx.author.id)
            osu_user = None

        if player is not None:
            if osu_user is None:
                osu_user = await player.get_osu_user()

            embed = discord.Embed(title=f"Level: {round(osu_user.level - 0.5)} PP: {osu_user.pp_raw}",
                                  description=f"Plays: {simp_num(osu_user.playcount)} Total score: {simp_num(round(osu_user.total_score))}\nRank: {simp_num(osu_user.pp_rank)} Acc: {round(osu_user.accuracy, 2)}")
            embed.set_author(name=f"{osu_user.username} on osu", url=f"https://osu.ppy.sh/users/{player.osu_id}",
                             icon_url=f"https://www.countryflags.io/{osu_user.country}/flat/64.png")
            embed.set_thumbnail(url=f"https://a.ppy.sh/{player.osu_id}?.png")

            # for best in bests:
            #    b_map = await self.api.get_beatmap(beatmap_id=best.beatmap_id)
            #    embed.add_field(name=f"{b_map.title}\n[{b_map.version}] ⭐ {round(b_map.difficultyrating, 2)}",
            #                    value=f"Score: {simp_num(round(best.score))}\n Combo: {best.maxcombo}/{b_map.max_combo}\n"
            #                          f"PP: {round(best.pp)}\n", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Use `!link [osu_name]` to link your osu account")


def setup(client):
    client.add_cog(osu_cog(client))
