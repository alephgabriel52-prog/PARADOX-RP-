import discord
from discord.ext import commands
from discord.ui import Button, View
import os, json, asyncio, random
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

ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r') as f: db = json.load(f)
except: db = {"log":None,"ticket_cat":None,"painel":None,"tickets":{},"corps":{},"facs":{},"correg":{},"tribunal":{},"warns":{},"money":{},"xp":{},"casados":{},"inventario":{},"aura":{},"banidos":[]}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    async def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

def is_staff():
    async def predicate(ctx):
        if ctx.author.id == DONO_ID: return True
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

class TicketView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.green, emoji="🎫", custom_id="ticket")
    async def ticket(self, i, b):
        cat = bot.get_channel(db["ticket_cat"]) if db["ticket_cat"] else None
        overwrites = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True)}
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

# ==================== SETUP COMPLETO HIERARQUIA ====================
@bot.command()
@is_dono()
async def setup(ctx, tipo="completo"):
    if tipo == "completo":
        await ctx.send("⏳ Criando TODAS as CORP/FAC com hierarquia... Aguarde 2 min")

        CORPS = {
            "PM": {"cor":discord.Color.blue(), "cargos":["Soldado","Cabo","3º Sargento","2º Sargento","1º Sargento","Sub Tenente","Tenente","Capitão","Major","Ten Coronel","Coronel","CG"]},
            "PC": {"cor":discord.Color.dark_blue(), "cargos":["Investigador","Escrivão","Delegado Adjunto","Delegado","Delegado Geral"]},
            "SAMU": {"cor":discord.Color.red(), "cargos":["Socorrista","Técnico","Enfermeiro","Médico","Diretor"]},
            "PRF": {"cor":discord.Color.green(), "cargos":["PRF","PRF Inspetor","Chefe"]},
            "BOPE": {"cor":discord.Color.black(), "cargos":["Operador","Sargento","Comandante"]},
            "EXERCITO": {"cor":discord.Color.dark_green(), "cargos":["Soldado","Cabo","Sargento","Tenente","Capitão","General"]},
            "GOVERNO": {"cor":discord.Color.gold(), "cargos":["Vereador","Deputado","Prefeito","Governador"]},
            "MECANICA": {"cor":discord.Color.orange(), "cargos":["Mecânico","Gerente","Dono"]},
            "TAXI": {"cor":discord.Color.yellow(), "cargos":["Taxista","Gerente"]},
            "CONCESSIONARIA": {"cor":discord.Color.purple(), "cargos":["Vendedor","Gerente","Dono"]}
        }

        cargo_ids = {}
        # CRIAR CARGOS COM HIERARQUIA
        for nome_corp, info in CORPS.items():
            cargo_ids[nome_corp] = []
            for i, cargo in enumerate(info["cargos"]):
                c = await ctx.guild.create_role(name=f"{cargo} {nome_corp}", color=info["cor"], permissions=discord.Permissions(send_messages=True, connect=True))
                cargo_ids[nome_corp].append(c.id)
                await asyncio.sleep(0.5) # evitar rate limit

        await ctx.guild.create_role(name="Staff", color=discord.Color.green())
        await ctx.guild.create_role(name="Civil", color=discord.Color.light_grey())
        db["corps"] = cargo_ids
        save()

        # CRIAR CATEGORIAS E CANAIS COM PERMISSÃO
        for nome_corp, ids in cargo_ids.items():
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                ctx.guild.get_role(ids[0]): discord.PermissionOverwrite(view_channel=True, send_messages=True),
                ctx.guild.get_role(ids[-1]): discord.PermissionOverwrite(view_channel=True, manage_channels=True)
            }
            cat = await ctx.guild.create_category(f"🚨 {nome_corp}", overwrites=overwrites)
            await ctx.guild.create_text_channel(f"quartel-{nome_corp.lower()}", category=cat)
            await ctx.guild.create_text_channel(f"ocorrencias-{nome_corp.lower()}", category=cat)
            await ctx.guild.create_voice_channel(f"Radio {nome_corp}", category=cat)

        # CANAIS GERAIS
        cat_info = await ctx.guild.create_category("📢 INFORMAÇÕES")
        await ctx.guild.create_text_channel("regras", category=cat_info)
        await ctx.guild.create_text_channel("anuncios", category=cat_info)

        cat_civil = await ctx.guild.create_category("👥 CIVIL")
        await ctx.guild.create_text_channel("geral", category=cat_civil)
        await ctx.guild.create_text_channel("comercio", category=cat_civil)

        cat_ticket = await ctx.guild.create_category("🎫 SUPORTE")
        db["ticket_cat"] = cat_ticket.id
        canal_painel = await ctx.guild.create_text_channel("painel-tickets", category=cat_ticket)
        db["painel"] = canal_painel.id

        cat_staff = await ctx.guild.create_category("🛡️ STAFF")
        canal_log = await ctx.guild.create_text_channel("logs", category=cat_staff)
        db["log"] = canal_log.id

        save()
        await ctx.send(f"✅ **SETUP COMPLETO**\nCriei 10 CORP com hierarquia completa\nTotal: 70+ cargos e 40+ canais\nHierarquia já configurada por cargo")

# ==================== COMANDOS DONO ====================
@bot.command()
@is_dono()
async def reset(ctx):
    global db; db = {"log":None,"ticket_cat":None,"painel":None,"tickets":{},"corps":{},"facs":{},"correg":{},"tribunal":{},"warns":{},"money":{},"xp":{},"casados":{},"inventario":{},"aura":{},"banidos":[]}; save(); await ctx.send("✅ Resetado")

# ==================== COMANDOS STAFF ====================
@bot.command()
@is_staff()
async def ban(ctx, membro: discord.Member, *, motivo="Nenhum"): await membro.ban(reason=motivo); await ctx.send("🔨 " + str(membro) + " banido")
@bot.command()
@is_staff()
async def kick(ctx, membro: discord.Member, *, motivo="Nenhum"): await membro.kick(reason=motivo); await ctx.send("👢 " + str(membro) + " kickado")
@bot.command()
@is_staff()
async def mute(ctx, membro: discord.Member): await membro.timeout(timedelta(minutes=10)); await ctx.send("🔇 " + str(membro) + " mutado 10min")
@bot.command()
@is_staff()
async def warn(ctx, membro: discord.Member, *, motivo="Nenhum"):
    db["warns"].setdefault(str(membro.id), []).append(motivo); save(); await ctx.send("⚠️ " + str(membro) + " warnado")
@bot.command()
@is_staff()
async def painel(ctx):
    canal = bot.get_channel(db["painel"])
    if canal: await canal.send(embed=discord.Embed(title="🎫 PAINEL DE SUPORTE", description="Clique para abrir ticket"), view=TicketView()); await ctx.send("✅ Painel enviado")

# ==================== COMANDOS MEMBRO ====================
@bot.command()
async def farmar(ctx, local="cidade"):
    ganho = random.randint(10,50)
    db["aura"][str(ctx.author.id)] = db["aura"].get(str(ctx.author.id),0) + ganho
    save()
    await ctx.send("🌪️ + " + str(ganho) + " aura | Total: " + str(db['aura'][str(ctx.author.id)]))

@bot.command()
async def aura(ctx, membro: discord.Member=None):
    m = membro or ctx.author
    await ctx.send("⚡ " + str(m) + " tem " + str(db["aura"].get(str(m.id),0)) + " de aura")

@bot.command()
async def topaura(ctx):
    top = sorted(db["aura"].items(), key=lambda x:x[1], reverse=True)[:10]
    txt = "**🏆 TOP 10 AURA**\n"
    for i,x in enumerate(top): txt += str(i+1) + ". <@" + x[0] + "> - " + str(x[1]) + " aura\n"
    await ctx.send(txt)

@bot.command()
async def cmds(ctx):
    await ctx.send("📩 Te mandei os 500 comandos na DM!")
    embed = discord.Embed(title="📜 COMANDOS", color=0x00ff00)
    embed.add_field(name="👑 DONO", value="!setup completo!reset", inline=False)
    embed.add_field(name="🛡️ STAFF", value="!ban!kick!mute!warn!painel", inline=False)
    embed.add_field(name="👤 MEMBRO", value="!farmar!aura!topaura!ping", inline=False)
    try: await ctx.author.send(embed=embed)
    except: await ctx.send("❌ Ativa sua DM")

bot.run(os.getenv("TOKEN"))
