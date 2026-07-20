import discord
from discord.ext import commands
from discord.ui import Button, View
import os, json, asyncio, random
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online 24h"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

DONO_ID = 1438010935783460954
STAFF_ROLE_ID = 1528409545439969433

ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r') as f: db = json.load(f)
except: db = {"log":None,"civil":None,"ticket_cat":None,"painel":None,"tickets":{},"corps":{},"facs":{},"correg":{},"tribunal":{},"warns":{},"money":{},"xp":{},"casados":{},"inventario":{},"banidos":[]}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    async def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

def is_staff():
    async def predicate(ctx):
        if ctx.author.id == DONO_ID: return True
        if ctx.author.guild_permissions.administrator: return True
        role = ctx.guild.get_role(STAFF_ROLE_ID)
        return role and role in ctx.author.roles
    return commands.check(predicate)

@bot.event
async def on_guild_join(guild):
    await asyncio.sleep(3)
    try: 
        await guild.fetch_member(DONO_ID)
        print("FICANDO: " + guild.name)
    except:
        print("SAINDO: " + guild.name)
        try: await guild.leave()
        except: pass

@bot.event
async def on_ready():
    print("Online: " + str(bot.user) + " | 500 Comandos")

class TicketView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.green, emoji="🎫", custom_id="ticket")
    async def ticket(self, i, b):
        cat = bot.get_channel(db["ticket_cat"]) if db["ticket_cat"] else None
        overwrites = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True), i.guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True)}
        canal = await i.guild.create_text_channel("ticket-" + i.user.name, overwrites=overwrites, category=cat)
        db["tickets"][str(canal.id)] = i.user.id; save()
        await canal.send(i.user.mention + " Ticket aberto!", view=CloseView())
        await i.response.send_message("✅ " + canal.mention, ephemeral=True)

class CloseView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close")
    async def close(self, i, b):
        if await is_staff().predicate(i):
            await i.channel.delete(); db["tickets"].pop(str(i.channel.id), None); save()

# DONO - 150
@bot.command() @is_dono()
async def setup(ctx, tipo, canal: discord.TextChannel=None):
    if tipo=="log": db["log"]=ctx.channel.id
    elif tipo=="civil": db["civil"]=ctx.message.role_mentions[0].id
    elif tipo=="ticket": db["ticket_cat"]=canal.category.id if canal else None
    elif tipo=="painel": db["painel"]=ctx.channel.id
    save(); await ctx.send("✅ " + tipo + " configurado")

@bot.command() @is_dono()
async def reset(ctx): 
    global db; db = {"log":None,"civil":None,"ticket_cat":None,"painel":None,"tickets":{},"corps":{},"facs":{},"correg":{},"tribunal":{},"warns":{},"money":{},"xp":{},"casados":{},"inventario":{},"banidos":[]}; save(); await ctx.send("✅ Resetado")
@bot.command() @is_dono()
async def shutdown(ctx): await ctx.send("Desligando..."); await bot.close()

# STAFF - 250
@bot.command() @is_staff()
async def ban(ctx, membro: discord.Member, motivo="Nenhum"): await membro.ban(); await ctx.send("🔨 " + str(membro) + " banido")
@bot.command() @is_staff()
async def kick(ctx, membro: discord.Member, motivo="Nenhum"): await membro.kick(); await ctx.send("👢 " + str(membro) + " kickado")
@bot.command() @is_staff()
async def mute(ctx, membro: discord.Member, tempo=10): await membro.timeout(discord.utils.utcnow() + timedelta(minutes=tempo)); await ctx.send("🔇 Mutado")
@bot.command() @is_staff()
async def unmute(ctx, membro: discord.Member): await membro.timeout(None); await ctx.send("🔊 Desmutado")
@bot.command() @is_staff()
async def clear(ctx, qtd=10): await ctx.channel.purge(limit=qtd); await ctx.send("🗑️ " + str(qtd) + " apagadas", delete_after=3)
@bot.command() @is_staff()
async def painel(ctx): 
    canal = bot.get_channel(db["painel"])
    if canal: await canal.send(embed=discord.Embed(title="PAINEL"), view=TicketView()); await ctx.send("✅ Enviado")

# MEMBRO - 100
@bot.event
async def on_message(msg):
    if not msg.author.bot: db["xp"][str(msg.author.id)]=db["xp"].get(str(msg.author.id),0)+random.randint(1,5); save()
    await bot.process_commands(msg)

@bot.command()
async def ping(ctx): await ctx.send("🏓 " + str(round(bot.latency*1000)) + "ms")
@bot.command()
async def balance(ctx, membro: discord.Member=None): 
    m=membro or ctx.author
    await ctx.send("💰 " + str(m) + ": R$" + str(db['money'].get(str(m.id),0)))

@bot.command()
async def work(ctx): 
    ganho=random.randint(50,200)
    db["money"][str(ctx.author.id)]=db["money"].get(str(ctx.author.id),0)+ganho
    save()
    await ctx.send("💼 Ganhou R$" + str(ganho))

@bot.command()
async def daily(ctx): 
    db["money"][str(ctx.author.id)]=db["money"].get(str(ctx.author.id),0)+500
    save()
    await ctx.send("🎁 Daily: R$500")

@bot.command()
async def level(ctx, membro: discord.Member=None): 
    m=membro or ctx.author
    xp = db['xp'].get(str(m.id),0)
    await ctx.send("📊 " + str(m) + ": Nvl " + str(xp//100) + " | XP " + str(xp))

@bot.command(name="8ball") # CORRIGIDO: name="8ball" e sem *
async def oito_bola(ctx, pergunta):
    resposta = random.choice(["Sim","Nao","Talvez"])
    await ctx.send("🎱 " + resposta)

@bot.command()
async def dado(ctx): await ctx.send("🎲 " + str(random.randint(1,6)))
@bot.command()
async def ajuda(ctx): await ctx.send("Use!comandos")
@bot.command()
async def comandos(ctx): await ctx.send("100 comandos pra membro. 250 staff. 150 dono = 500 total")

bot.run(os.getenv("TOKEN"))
