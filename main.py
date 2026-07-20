import discord
from discord.ext import commands
from discord.ui import Button, View
import os, json, asyncio, random
from datetime import timedelta
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
except: db = {"log":None,"ticket_cat":None,"painel":None,"tickets":{},"corps":{},"warns":{},"money":{},"xp":{},"casados":{},"inventario":{},"aura":{},"banidos":[]}

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

# ==================== SETUP COM CARGOS REAIS ====================
@bot.command()
@is_dono()
async def setup(ctx, fac):
    fac = fac.upper()
    FAC_LISTA = {
        "PM": {
            "cor":discord.Color.blue(),
            "cargos":["Soldado PM","Cabo PM","3º Sargento PM","2º Sargento PM","1º Sargento PM","Subtenente PM","2º Tenente PM","1º Tenente PM","Capitão PM","Major PM","Tenente Coronel PM","Coronel PM","Comandante Geral PM"]
        },
        "PC": {
            "cor":discord.Color.dark_blue(),
            "cargos":["Agente de Policia","Inspetor de Policia","Delegado Adjunto","Delegado de Policia","Chefe de Policia Civil"]
        },
        "PRF": {
            "cor":discord.Color.green(),
            "cargos":["Policial Rodoviario Federal","PRF Inspetor","Chefe de Nucleo PRF","Coordenador PRF","Superintendente PRF"]
        },
        "PF": {
            "cor":discord.Color.dark_red(),
            "cargos":["Agente de Policia Federal","Escrivão PF","Delegado PF","Delegado Chefe PF","Superintendente PF","Diretor Geral PF"]
        },
        "SAMU": {
            "cor":discord.Color.red(),
            "cargos":["Condutor Socorrista","Técnico de Enfermagem","Enfermeiro","Médico","Coordenador Médico","Diretor SAMU"]
        },
        "BOPE": {
            "cor":discord.Color.black(),
            "cargos":["Soldado BOPE","Cabo BOPE","Sargento BOPE","Oficial BOPE","Comandante BOPE"]
        },
        "EXERCITO": {
            "cor":discord.Color.dark_green(),
            "cargos":["Soldado EB","Cabo EB","3º Sargento EB","2º Sargento EB","1º Sargento EB","Subtenente EB","2º Tenente EB","1º Tenente EB","Capitão EB","Major EB","Tenente Coronel EB","Coronel EB","General de Brigada"]
        },
        "GOVERNO": {
            "cor":discord.Color.gold(),
            "cargos":["Vereador","Deputado Estadual","Deputado Federal","Senador","Prefeito","Governador","Ministro"]
        },
        "MECANICA": {
            "cor":discord.Color.orange(),
            "cargos":["Ajudante Mecânico","Mecânico","Mecânico Chefe","Gerente","Dono"]
        },
        "TAXI": {
            "cor":discord.Color.yellow(),
            "cargos":["Taxista","Coordenador","Gerente","Dono"]
        }
    }

    if fac not in FAC_LISTA:
        await ctx.send("❌ Facs: PM, PC, PRF, PF, SAMU, BOPE, EXERCITO, GOVERNO, MECANICA, TAXI")
        return

    await ctx.send(f"⏳ Criando {fac} com cargos reais...")

    info = FAC_LISTA[fac]
    cargo_ids = []

    # CRIAR CARGOS REAIS COM HIERARQUIA
    for cargo in info["cargos"]:
        c = await ctx.guild.create_role(name=cargo, color=info["cor"], permissions=discord.Permissions(send_messages=True, connect=True, speak=True))
        cargo_ids.append(c.id)
        await asyncio.sleep(0.4)

    # CRIAR CATEGORIA + CANAIS COM PERMISSÃO
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.guild.get_role(cargo_ids[0]): discord.PermissionOverwrite(view_channel=True, send_messages=True),
        ctx.guild.get_role(cargo_ids[-1]): discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_roles=True)
    }
    cat = await ctx.guild.create_category(f"🚨 {fac}", overwrites=overwrites)
    await ctx.guild.create_text_channel(f"📋 quartel-{fac.lower()}", category=cat)
    await ctx.guild.create_text_channel(f"📄 ocorrencias-{fac.lower()}", category=cat)
    await ctx.guild.create_text_channel(f"📢 avisos-{fac.lower()}", category=cat)
    await ctx.guild.create_voice_channel(f"📻 Radio {fac}", category=cat)
    await ctx.guild.create_voice_channel(f"🚓 Patrulhamento {fac}", category=cat)

    db["corps"][fac] = cargo_ids; save()
    await ctx.send(f"✅ **{fac} CRIADA**\n{len(info['cargos'])} cargos reais\n5 canais\nHierarquia 100% configurada")

@bot.command() @is_dono()
async def reset(ctx): global db; db = {"log":None,"ticket_cat":None,"painel":None,"tickets":{},"corps":{},"warns":{},"money":{},"xp":{},"casados":{},"inventario":{},"aura":{},"banidos":[]}; save(); await ctx.send("✅ Resetado")

@bot.command() @is_staff()
async def ban(ctx, membro: discord.Member, *, motivo="Nenhum"): await membro.ban(reason=motivo); await ctx.send("🔨 " + str(membro) + " banido")
@bot.command() @is_staff()
async def kick(ctx, membro: discord.Member, *, motivo="Nenhum"): await membro.kick(reason=motivo); await ctx.send("👢 " + str(membro) + " kickado")
@bot.command() @is_staff()
async def mute(ctx, membro: discord.Member): await membro.timeout(timedelta(minutes=10)); await ctx.send("🔇 " + str(membro) + " mutado")
@bot.command() @is_staff()
async def warn(ctx, membro: discord.Member, *, motivo="Nenhum"): db["warns"].setdefault(str(membro.id), []).append(motivo); save(); await ctx.send("⚠️ " + str(membro) + " warnado")
@bot.command() @is_staff()
async def painel(ctx): canal = bot.get_channel(db["painel"]); if canal: await canal.send(embed=discord.Embed(title="🎫 PAINEL DE SUPORTE"), view=TicketView()); await ctx.send("✅ Painel enviado")

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
async def cmds(ctx):
    await ctx.send("📩 Te mandei os 500 comandos na DM!")
    embed = discord.Embed(title="📜 COMANDOS", color=0x00ff00)
    embed.add_field(name="👑 DONO", value="!setup [pm/pc/prf/pf/samu/bope/exercito]!reset", inline=False)
    embed.add_field(name="🛡️ STAFF", value="!ban!kick!mute!warn!painel", inline=False)
    embed.add_field(name="👤 MEMBRO", value="!farmar!aura!ping", inline=False)
    try: await ctx.author.send(embed=embed)
    except: await ctx.send("❌ Ativa sua DM")

bot.run(os.getenv("TOKEN"))
