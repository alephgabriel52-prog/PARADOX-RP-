import discord
from discord.ext import commands
import os, json, asyncio
from flask import Flask
from threading import Thread

# KEEP ALIVE
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
except: db = {"corps":{}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 Pong! {round(bot.latency*1000)}ms')

@bot.command()
@is_dono()
async def setup(ctx, fac):
    fac = fac.upper()
    
    FAC_LISTA = {
        "PM": ["Soldado PM","Cabo PM","Sargento PM","Tenente PM","Capitão PM","Coronel PM"],
        "PC": ["Agente","Inspetor","Delegado","Chefe PC"],
        "PRF": ["PRF","Inspetor PRF","Chefe PRF"],
        "PF": ["Agente PF","Delegado PF","Superintendente PF"],
        "SAMU": ["Condutor","Enfermeiro","Medico","Diretor SAMU"]
    }
    
    if fac not in FAC_LISTA:
        return await ctx.send("❌ Use: `!setup PM` `!setup PC` `!setup PRF` `!setup PF` `!setup SAMU`")
    
    await ctx.send(f"⏳ Criando estrutura da {fac}... Aguarda 10s")
    
    info = FAC_LISTA[fac]
    cargo_ids = []
    
    # CRIA OS CARGOS
    for nome_cargo in info:
        cargo = await ctx.guild.create_role(name=nome_cargo, color=discord.Color.blue())
        cargo_ids.append(cargo.id)
        await asyncio.sleep(0.5)
    
    # CRIA A CATEGORIA
    overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False)}
    categoria = await ctx.guild.create_category(f"🚨 {fac}", overwrites=overwrites)
    
    # CRIA OS CANAIS DENTRO
    await ctx.guild.create_text_channel(f"quartel-{fac.lower()}", category=categoria)
    await ctx.guild.create_text_channel(f"ocorrencias-{fac.lower()}", category=categoria)
    await ctx.guild.create_voice_channel(f"Rádio {fac}", category=categoria)
    
    # SALVA
    db["corps"][fac] = cargo_ids
    save()
    
    await ctx.send(f"✅ **{fac} CRIADA COM SUCESSO**\n{len(info)} cargos + 3 canais criados")

bot.run(os.getenv("TOKEN"))
