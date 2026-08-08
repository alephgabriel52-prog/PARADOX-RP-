import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, Select
import os, json, asyncio, datetime, random
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

DONO_ID = 1438010935783460954
STAFF_ROLE_ID = 1528409545439969433
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"tickets":{}, "servidores_permitidos": [], "anti_bot": False, "economia": {}, "cpf": {}, "bancos": {}, "empresas": {}, "inventario": {}, "casamento": {}, "xp": {}, "casas": {}, "carros": {}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

def is_staff():
    def predicate(ctx): return STAFF_ROLE_ID in [r.id for r in ctx.author.roles] or ctx.author.id == DONO_ID
    return commands.check(predicate)

# ============ HELP ATUALIZADO ============
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📜 LISTA DE COMANDOS - PARADOX BOT", color=0x5865F2)
    embed.add_field(name="🏠 Ticket", value="`!painel` `!painelloja` `!painelwl` `!painelanti`", inline=False)
    embed.add_field(name="🛡️ Moderação", value="`!banir` `!expulsar` `!mutar` `!desmutar` `!limpar` `!avisar`", inline=False)
    embed.add_field(name="💰 Economia", value="`!saldo` `!pix` `!depositar` `!sacar` `!trabalhar` `!loja` `!comprar` `!vender`", inline=False)
    embed.add_field(name="🎒 Inventário", value="`!inventario` `!daritem` `!usar`", inline=False)
    embed.add_field(name="💍 Social", value="`!casar @membro` `!divorciar` `!casamento`", inline=False)
    embed.add_field(name="🏠 Bens", value="`!comprarcasa` `!minhacasa` `!comprarcarro` `!meucarro`", inline=False)
    embed.add_field(name="📊 XP", value="`!rank` `!nivel`", inline=False)
    embed.add_field(name="📱 Outros", value="`!celular` `!criarcpf` `!meucpf` `!infoserver`", inline=False)
    embed.add_field(name="👑 Dev", value="`!servers` `!liberar` `!addsaldo`", inline=False)
    await ctx.send(embed=embed)

# ============ XP E NIVEL ============
@bot.event
async def on_message(message):
    if message.author.bot: return
    uid = str(message.author.id)
    db["xp"][uid] = db["xp"].get(uid, {"xp":0, "lvl":1})
    db["xp"][uid]["xp"] += random.randint(1,5)
    if db["xp"][uid]["xp"] >= db["xp"][uid]["lvl"] * 100:
        db["xp"][uid]["xp"] = 0
        db["xp"][uid]["lvl"] += 1
        await message.channel.send(f"🎉 {message.author.mention} subiu para o nível **{db['xp'][uid]['lvl']}**!")
        save()
    await bot.process_commands(message)

@bot.command()
async def nivel(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    data = db["xp"].get(str(membro.id), {"xp":0, "lvl":1})
    await ctx.send(f"📊 {membro.name} - Nível **{data['lvl']}** | XP: {data['xp']}/{data['lvl']*100}")

@bot.command()
async def rank(ctx):
    top = sorted(db["xp"].items(), key=lambda x: x[1]["lvl"], reverse=True)[:10]
    txt = "\n".join([f"{i+1}. <@{u}> - Nv {d['lvl']}" for i,(u,d) in enumerate(top)])
    await ctx.send(f"**🏆 TOP 10 NÍVEIS**\n{txt}")

# ============ TRABALHO E LOJA ============
TRABALHOS = {"policial": [200,400], "mecanico": [150,300], "medico": [250,500]}
LOJA = {"Celular": 500, "Arma": 2000, "Kit Reparos": 300}

@bot.command()
@commands.cooldown(1, 300, commands.BucketType.user)
async def trabalhar(ctx):
    ganho = random.randint(100, 500)
    db["economia"][str(ctx.author.id)] = db["economia"].get(str(ctx.author.id), 0) + ganho
    save()
    await ctx.send(f"✅ Você trabalhou e ganhou **R$ {ganho}**")

@trabalhar.error
async def erro_trabalhar(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ Aguarde {int(error.retry_after/60)} minutos para trabalhar de novo")

@bot.command()
async def loja(ctx):
    txt = "\n".join([f"**{k}** - R$ {v}" for k,v in LOJA.items()])
    await ctx.send(f"**🛒 LOJA**\n{txt}")

@bot.command()
async def comprar(ctx, item: str):
    if item not in LOJA: return await ctx.send("❌ Item não existe")
    preco = LOJA[item]
    if db["economia"].get(str(ctx.author.id), 0) < preco: return await ctx.send("❌ Saldo insuficiente")
    db["economia"][str(ctx.author.id)] -= preco
    db["inventario"][str(ctx.author.id)] = db["inventario"].get(str(ctx.author.id), [])
    db["inventario"][str(ctx.author.id)].append(item)
    save()
    await ctx.send(f"✅ Você comprou **{item}** por R$ {preco}")

@bot.command()
async def inventario(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    itens = db["inventario"].get(str(membro.id), [])
    await ctx.send(f"🎒 Inventário de {membro.name}: {', '.join(itens) if itens else 'Vazio'}")

# ============ CASAMENTO ============
@bot.command()
async def casar(ctx, membro: discord.Member):
    if str(ctx.author.id) in db["casamento"]: return await ctx.send("❌ Você já é casado")
    db["casamento"][str(ctx.author.id)] = str(membro.id)
    db["casamento"][str(membro.id)] = str(ctx.author.id)
    save()
    await ctx.send(f"💍 {ctx.author.mention} e {membro.mention} agora são casados!")

@bot.command()
async def divorciar(ctx):
    if str(ctx.author.id) not in db["casamento"]: return await ctx.send("❌ Você não é casado")
    parceiro = db["casamento"][str(ctx.author.id)]
    del db["casamento"][str(ctx.author.id)]
    del db["casamento"][parceiro]
    save()
    await ctx.send("💔 Divórcio realizado")

@bot.command()
async def casamento(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    parceiro = db["casamento"].get(str(membro.id))
    if not parceiro: return await ctx.send("❌ Não é casado")
    await ctx.send(f"💍 {membro.name} é casado com <@{parceiro}>")

# ============ CASAS E CARROS ============
@bot.command()
async def comprarcasa(ctx):
    preco = 50000
    if db["economia"].get(str(ctx.author.id), 0) < preco: return await ctx.send("❌ Precisa de R$ 50000")
    db["economia"][str(ctx.author.id)] -= preco
    db["casas"][str(ctx.author.id)] = "Casa Simples"
    save()
    await ctx.send("🏠 Você comprou uma Casa Simples!")

@bot.command()
async def minhascasa(ctx):
    casa = db["casas"].get(str(ctx.author.id))
    await ctx.send(f"🏠 Sua casa: {casa if casa else 'Não tem casa'}")

@bot.command()
async def comprarcarro(ctx):
    preco = 30000
    if db["economia"].get(str(ctx.author.id), 0) < preco: return await ctx.send("❌ Precisa de R$ 30000")
    db["economia"][str(ctx.author.id)] -= preco
    db["carros"][str(ctx.author.id)] = "Fusca"
    save()
    await ctx.send("🚗 Você comprou um Fusca!")

@bot.command()
async def meucarro(ctx):
    carro = db["carros"].get(str(ctx.author.id))
    await ctx.send(f"🚗 Seu carro: {carro if carro else 'Não tem carro'}")

# ============ CELULAR ============
@bot.command()
async def celular(ctx):
    if "Celular" not in db["inventario"].get(str(ctx.author.id), []):
        return await ctx.send("❌ Você não tem um celular. Compre na `!loja`")
    embed = discord.Embed(title="📱 Celular", description="`!pix` `!saldo` `!contatos`", color=0x5865F2)
    await ctx.send(embed=embed)

# ============ MODERACAO EXTRA ============
@bot.command()
@is_staff()
async def desmutar(ctx, membro: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Mutado")
    await membro.remove_roles(role)
    await ctx.send(f"🔊 {membro.mention} foi desmutado")

@bot.command()
@is_staff()
async def avisar(ctx, membro: discord.Member, *, motivo):
    await ctx.send(f"⚠️ {membro.mention} foi avisado. Motivo: {motivo}")

# ============ O RESTO DO CODIGO TICKET, WL, ECONOMIA, ETC ============
#... AQUI COLA TODO O CODIGO V17 QUE TE MANDEI ANTES...

# ============ ON_READY ============
@bot.event
async def on_ready():
    bot.add_view(PainelTicket()); bot.add_view(PainelVIP()); bot.add_view(PainelWL())
    await bot.change_presence(activity=discord.Game(name="Use!help"))
    print('✅ BOT V18 MASTER ONLINE')

bot.run(os.getenv("TOKEN"))
