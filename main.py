import os
import discord
from discord.ext import commands
from flask import Flask
import threading

# 1. SERVIDOR PRA NÃO DORMIR
app = Flask('')

@app.route('/')
def home():
    return "PARADOX RP ONLINE"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# 2. SEU BOT
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print(f'PARADOX RP ONLINE: {client.user}')

# 3. LIGA TUDO JUNTO
keep_alive() # liga o site primeiro
client.run(os.getenv('TOKEN')) # liga o bot depois
