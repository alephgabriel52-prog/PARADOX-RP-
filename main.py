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

@bot.event
async def on_ready():
    print(f'✅ Logado como {bot.user}')
    print(f'Servidores: {len(bot.guilds)}')
    await bot.change_presence(activity=discord.Game(name="!cmds | 500+ Comandos"))

@bot.event 
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)

DONO_ID = 1438010935783460954
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"log":None,"ticket_cat":None,"painel":None,"tickets":{},"corps":{},"warns":{},"money":{},"xp":{},"aura":{}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

def is_staff():
    def predicate(ctx):
        if ctx.author.id == DONO_ID: return True
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

class TicketView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.green, emoji="🎫", custom_id="ticket")
    async def ticket(self, i, b):
        cat = bot.get_channel(db["ticket_cat"]) if db["ticket_cat"] else None
        overwrites = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True)}
        canal = await i.guild.create_text_channel(f"ticket-{i.user.name}", overwrites=overwrites, category=cat)
        db["tickets"][str(canal.id)] = i.user.id; save()
        await canal.send(f"{i.user.mention} Ticket aberto!", view=CloseView())
        await i.response.send_message(f"✅ {canal.mention}", ephemeral=True)

class CloseView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close")
    async def close(self, i, b):
        if i.user.id == DONO_ID or i.user.guild_permissions.administrator:
            await i.channel.delete(); db["tickets"].pop(str(i.channel.id), None); save()

# ==================== SETUP FAC ====================
@bot.command()
@is_dono()
async def setup(ctx, fac):
    fac = fac.upper()
    FAC_LISTA = {
        "PM": {"cor":discord.Color.blue(), "cargos":["Soldado PM","Cabo PM","3º Sargento PM","2º Sargento PM","1º Sargento PM","Subtenente PM","2º Tenente PM","1º Tenente PM","Capitão PM","Major PM","Tenente Coronel PM","Coronel PM","Comandante Geral PM"]},
        "PC": {"cor":discord.Color.dark_blue(), "cargos":["Agente de Policia","Inspetor de Policia","Delegado Adjunto","Delegado de Policia","Chefe de Policia Civil"]},
        "PRF": {"cor":discord.Color.green(), "cargos":["Policial Rodoviario Federal","PRF Inspetor","Chefe de Nucleo PRF","Coordenador PRF","Superintendente PRF"]},
        "PF": {"cor":discord.Color.dark_red(), "cargos":["Agente de Policia Federal","Escrivão PF","Delegado PF","Delegado Chefe PF","Superintendente PF","Diretor Geral PF"]},
        "SAMU": {"cor":discord.Color.red(), "cargos":["Condutor Socorrista","Técnico de Enfermagem","Enfermeiro","Médico","Coordenador Médico","Diretor SAMU"]},
        "BOPE": {"cor":discord.Color.black(), "cargos":["Soldado BOPE","Cabo BOPE","Sargento BOPE","Oficial BOPE","Comandante BOPE"]},
        "EXERCITO": {"cor":discord.Color.dark_green(), "cargos":["Soldado EB","Cabo EB","3º Sargento EB","2º Sargento EB","1º Sargento EB","Subtenente EB","2º Tenente EB","1º Tenente EB","Capitão EB","Major EB","Tenente Coronel EB","Coronel EB","General de Brigada"]}
    }
    if fac not in FAC_LISTA: return await ctx.send("❌ Facs: PM, PC, PRF, PF, SAMU, BOPE, EXERCITO")
    await ctx.send(f"⏳ Criando {fac}...")
    info = FAC_LISTA[fac]
    cargo_ids = []
    for cargo in info["cargos"]:
        c = await ctx.guild.create_role(name=cargo, color=info["cor"])
        cargo_ids.append(c.id); await asyncio.sleep(0.5)
    overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), ctx.guild.get_role(cargo_ids[0]): discord.PermissionOverwrite(view_channel=True), ctx.guild.get_role(cargo_ids[-1]): discord.PermissionOverwrite(view_channel=True, manage_channels=True)}
    cat = await ctx.guild.create_category(f"🚨 {fac}", overwrites=overwrites)
    await ctx.guild.create_text_channel(f"quartel-{fac.lower()}", category=cat)
    await ctx.guild.create_text_channel(f"ocorrencias-{fac.lower()}", category=cat)
    await ctx.guild.create_voice_channel(f"Radio {fac}", category=cat)
    db["corps"][fac] = cargo_ids; save()
    await ctx.send(f"✅ **{fac} CRIADA** com {len(info['cargos'])} cargos reais")

# ==================== DONO ====================
@bot.command() @is_dono()
async def reset(ctx): global db; db = {"log":None,"ticket_cat":None,"painel":None,"tickets":{},"corps":{},"warns":{},"money":{},"xp":{},"aura":{}}; save(); await ctx.send("✅ Resetado")
@bot.command() @is_dono()
async def shutdown(ctx): await ctx.send("Desligando..."); await bot.close()
@bot.command() @is_dono()
async def stats(ctx): await ctx.send(f"Servidores: {len(bot.guilds)}")
@bot.command() @is_dono()
async def pingbot(ctx): await ctx.send(f"Pong: {round(bot.latency*1000)}ms")
@bot.command() @is_dono()
async def say(ctx, *, msg): await ctx.send(msg)

# ==================== STAFF ====================
@bot.command() @is_staff()
async def ban(ctx, membro: discord.Member, *, motivo="Nenhum"): await membro.ban(reason=motivo); await ctx.send(f"🔨 {membro} banido")
@bot.command() @is_staff()
async def kick(ctx, membro: discord.Member, *, motivo="Nenhum"): await membro.kick(reason=motivo); await ctx.send(f"👢 {membro} kickado")
@bot.command() @is_staff()
async def mute(ctx, membro: discord.Member): await membro.timeout(timedelta(minutes=10)); await ctx.send(f"🔇 {membro} mutado")
@bot.command() @is_staff()
async def unmute(ctx, membro: discord.Member): await membro.timeout(None); await ctx.send(f"🔊 {membro} desmutado")
@bot.command() @is_staff()
async def clear(ctx, qtd=5): await ctx.channel.purge(limit=int(qtd)+1); await ctx.send(f"🧹 {qtd} msgs apagadas")
@bot.command() @is_staff()
async def warn(ctx, membro: discord.Member, *, motivo="Nenhum"): db["warns"].setdefault(str(membro.id), []).append(motivo); save(); await ctx.send(f"⚠️ {membro} warnado")
@bot.command() @is_staff()
async def painel(ctx):
    canal = bot.get_channel(db["painel"])
    if canal:
        embed = discord.Embed(title="🎫 PAINEL DE SUPORTE", description="Clique no botão abaixo para abrir ticket", color=0x00ff00)
        await canal.send(embed=embed, view=TicketView())
        await ctx.send("✅ Painel enviado")
    else:
        await ctx.send("❌ Configure um canal e use!setpainel ID_DO_CANAL primeiro")
@bot.command() @is_staff()
async def setpainel(ctx, canal: discord.TextChannel): db["painel"] = canal.id; save(); await ctx.send(f"✅ Painel definido em {canal.mention}")

# ==================== MEMBRO ====================
@bot.command()
async def ping(ctx): await ctx.send(f"Pong: {round(bot.latency*1000)}ms")
@bot.command()
async def avatar(ctx, membro: discord.Member=None): m = membro or ctx.author; await ctx.send(m.display_avatar.url)
@bot.command()
async def farmar(ctx):
    ganho = random.randint(10,50)
    db["aura"][str(ctx.author.id)] = db["aura"].get(str(ctx.author.id),0) + ganho
    save()
    await ctx.send(f"🌪️ + {ganho} aura | Total: {db['aura'][str(ctx.author.id)]}")
@bot.command()
async def aura(ctx, membro: discord.Member=None):
    m = membro or ctx.author
    await ctx.send(f"⚡ {m.name} tem {db['aura'].get(str(m.id),0)} de aura")
@bot.command()
async def topaura(ctx):
    top = sorted(db["aura"].items(), key=lambda x:x[1], reverse=True)[:10]
    txt = "**🏆 TOP 10 AURA**\n"
    for i,x in enumerate(top): txt += f"{i+1}. <@{x[0]}> - {x[1]} aura\n"
    await ctx.send(txt if top else "Ninguém tem aura ainda")
@bot.command()
async def cmds(ctx):
    embed = discord.Embed(title="📜 COMANDOS DO BOT", color=0x00ff00)
    embed.add_field(name="👑 DONO", value="`!setup [fac]` `!reset` `!shutdown` `!stats`", inline=False)
    embed.add_field(name="🛡️ STAFF", value="`!ban` `!kick` `!mute` `!warn` `!clear` `!painel` `!setpainel`", inline=False)
    embed.add_field(name="👤 MEMBRO", value="`!ping` `!avatar` `!farmar` `!aura` `!topaura`", inline=False)
    await ctx.send(embed=embed)

bot.run(os.getenv("TOKEN"))
