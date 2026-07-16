import discord
from discord.ext import commands
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'PARADOX RP ONLINE: {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! Bot 24/7 online ✅')

bot.run(os.getenv('TOKEN'))

