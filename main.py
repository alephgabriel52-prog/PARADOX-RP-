import discord
from discord.ext import commands, tasks
import os, json, asyncio, io, datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online V96"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ARQUIVO = 'botdata.json'
try: db = json.load(open(ARQUIVO,'r',encoding='utf-8'))
except: db = {"config":{}, "tickets":{}, "whitelist":{}, "warns":{}, "anuncios":[]}
def save(): json.dump(db, open(ARQUIVO,'w',encoding='utf-8'), ensure_ascii=False, indent=4)

OWNER_ID = 1438010935783460954
BANNER_FAIXA = "https://cdn.discordapp.com/attachments/1527669780364918925/1549093554960474243/file_0005a0820e8df98c1974ab6ecc.png"

def is_staff():
    async def predicate(ctx):
        return any(r.id == db["config"].get("staff_cargo") for r in ctx.author.roles) or ctx.author.id == OWNER_ID
    return commands.check(predicate)

def is_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator or ctx.author.id == OWNER_ID
    return commands.check(predicate)

@tasks.loop(minutes=1)
async def verificar_anuncios():
    agora = datetime.datetime.now().strftime("%H:%M")
    for anuncio in db["anuncios"][:]:
        if anuncio["hora"] == agora:
            canal = bot.get_channel(anuncio["canal"])
            if canal:
                embed = discord.Embed(title="📢 ANÚNCIO", description=anuncio["mensagem"], color=0xFF0000)
                embed.set_image(url=BANNER_FAIXA)
                embed.set_footer(text=f"Agendado por {anuncio['autor']} • ID: {anuncio['id']}")
                await canal.send("@everyone", embed=embed)
            db["anuncios"].remove(anuncio); save()

@verificar_anuncios.before_loop
async def before(): await bot.wait_until_ready()

# ... AQUI VAI TODO O RESTO DO CÓDIGO DO V96 QUE TE MANDEI ANTES ...
# Ticket, Whitelist, !anuncio, !anuncios, !cancelaranuncio, !adiaranuncio

@bot.event
async def on_ready():
    verificar_anuncios.start()
    print(f'✅ V96 ONLINE')

bot.run(os.getenv("TOKEN"))
