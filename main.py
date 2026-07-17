import discord
from discord.ext import commands
import os
import threading
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask('')

@app.route('/')
def index():
    return "Bot PARADOX-RP está online"

def run():
    app.run(host="0.0.0.0", port=8080)

def manter_vivo():
    t = threading.Thread(target=run)
    t.start()

manter_vivo()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'PARADOX RP ONLINE: {bot.user}')

TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
