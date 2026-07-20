import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online 24h"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logado como {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency*1000)}ms')

@bot.command()
async def farmar(ctx):
    await ctx.send('🌪️ +25 aura')

bot.run(os.getenv("TOKEN"))
