import BB_db
import discord, random, requests, os, time, pyosu
from discord.ext import commands, tasks
from BB_keys import liveKey, TestKey

version = "Added death rolling! 0.3"                 # Updated with major changes
client = commands.Bot(command_prefix='!')
db, api = BB_db.initialize_database()       # Initialize the database globals


@client.event
async def on_ready():
    print(f"bot Ready ", version)

def load_cogs():
    for file in os.listdir('./cogs'):
        if file.endswith(".py"):
            client.load_extension(f"cogs.{file[:-3]}")


load_cogs()
client.run(liveKey)