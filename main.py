import discord
from discord.ext import commands
import os, json, random
from flask import Flask
from threading import Thread

# KEEP ALIVE PRA RENDER NÃO DORMIR
app = Flask('')
@app.route('/')
def home(): return "Bot Online"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ BOT ONLINE: {bot.user}')

DONO_ID = 1438010935783460954
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"aura":{}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

def is_staff():
    def predicate(ctx):
        if ctx.author.id == DONO_ID: return True
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

# COMANDOS BÁSICOS QUE NÃO QUEBRAM
@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 Pong! {round(bot.latency*1000)}ms')

@bot.command()
@is_staff()
async def ban(ctx, membro: discord.Member):
    await membro.ban()
    await ctx.send(f'🔨 {membro} foi banido')

@bot.command()
@is_staff()
async def kick(ctx, membro: discord.Member):
    await membro.kick()
    await ctx.send(f'👢 {membro} foi kickado')

@bot.command()
async def farmar(ctx):
    ganho = random.randint(10,50)
    db["aura"][str(ctx.author.id)] = db["aura"].get(str(ctx.author.id),0) + ganho
    save()
    await ctx.send(f'🌪️ +{ganho} aura | Total: {db["aura"][str(ctx.author.id)]}')

@bot.command()
@is_dono()
async def setup(ctx, fac):
    await ctx.send(f'✅ Comando setup recebido: {fac}')

bot.run(os.getenv("TOKEN"))
