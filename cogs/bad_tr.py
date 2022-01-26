from googletrans import Translator

Translator = Translator()

from discord.ext import commands
import discord, asyncio, random

langs = ['af', 'ga', 'sq', 'it', 'ar', 'ja', 'az', 'kn', 'eu', 'ko', 'bn', 'la', 'be', 'lv', 'bg',
         'lt', 'ca', 'mk', 'zh-CN', 'ms', 'zh-TW', 'mt', 'hr', 'no', 'cs', 'fa', 'da', 'pl', 'nl',
         'pt', 'ro', 'eo', 'ru', 'et', 'sr', 'tl', 'sk', 'fi', 'sl', 'fr', 'es', 'gl', 'sw', 'ka',
         'sv', 'de', 'ta', 'el', 'te', 'gu', 'th', 'ht', 'tr', 'iw', 'uk', 'hi', 'ur', 'hu', 'vi',
         'is', 'cy', 'id', 'yi']


class cog_translate(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(name="badtranslate", aliases=['btr'])
    @commands.cooldown(1, 60, commands.BucketType.default)
    async def badtranslate(self, ctx, *, text: str):
        '''
        translates the text given
        ----
        text: str
            the text to be translated
        '''
        if text == "":
            await ctx.send(f"There isn't anything to translate!")
            return

        language_list = ["en "]
        message = await ctx.send(f"Translating text...")

        # Translating to 10 languages
        for i in range(10):
            await asyncio.sleep(5)
            randomlang = 'en' if i == 9 else random.choice(langs)  # get random choice, else en if 10th
            translated = Translator.translate(text, dest=randomlang)  # translate the text
            text = translated.text  # store text for next round
            language_list.append(f" 🠒 {randomlang}")  # add translator stuff to list
            await message.edit(content=f"Translated {', '.join(language_list)} ```{text}```")  # send the message


def setup(client):
    client.add_cog(cog_translate(client))