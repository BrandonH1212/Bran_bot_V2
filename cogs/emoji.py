import BB_utility, BB_db
from discord.ext import commands
import discord, asyncio
import requests
from PIL import Image

emoji_server = 523099434159177729


class Emoji_cog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = BB_db.db
        self.api = BB_db.api
        self.message = None
        self.message_content = "Look I can make emoji's out of avatars EZ\n"

    @commands.command(
        aliases=["e"])
    async def emoji(self, ctx):
        user = await self.client.fetch_user(ctx.author.id)
        self.message = await ctx.send(self.message_content)
        await self.message.add_reaction("👀")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):  # Player input command
        if self.message is not None:
            if not payload.member.bot and str(payload.message_id) == str(self.message.id):
                if str(payload.emoji) == "👀" and str(payload.user_id) not in self.message_content:
                    user = await self.client.fetch_user(payload.user_id)
                    self.message_content += f"{await self.get_user_emoji(user=user)}  "
                    await self.message.edit(content=self.message_content)

    async def get_user_emoji(self, user:discord.User):
        server = await self.client.fetch_guild(emoji_server)
        req_emojis = await server.fetch_emojis()
        e_names = {}

        for i, emojis in enumerate(req_emojis):
            e_names[str(emojis.name)] = i

        if str(user.id) not in e_names.keys():
            request = requests.get(user.avatar_url)
            emoji = await server.create_custom_emoji(name=user.id, image=request.content)
            return emoji

        return req_emojis[e_names[str(user.id)]]




def setup(client):
    client.add_cog(Emoji_cog(client))
