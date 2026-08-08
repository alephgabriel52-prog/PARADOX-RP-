import discord
from discord.ext import commands
from discord.ui import View, Button
import os, json, asyncio, random
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
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"tickets":{}, "economia": {}, "comandos_dinamicos": {}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    return commands.check(lambda ctx: ctx.author.id == DONO_ID)

# ============ TODOS OS TEMPLATES + HIERARQUIA ============
TEMPLATES = {
    "pmrj": {"nome": "PMERJ", "cor": 0x1E3A8A, "cargos": [{"nome": "👑 Cel PM", "permissoes": discord.Permissions(administrator=True)}, {"nome": "⭐ Ten Cel", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🎖️ Cap PM", "permissoes": discord.Permissions(ban_members=True)}, {"nome": "🚔 Ten PM", "permissoes": discord.Permissions(kick_members=True)}, {"nome": "🪖 Sgt PM", "permissoes": discord.Permissions(manage_messages=True)}, {"nome": "👮 Cb PM", "permissoes": discord.Permissions(mute_members=True)}, {"nome": "🚨 Sd PM", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"📢 PMERJ - INFO": ["📜regras-pm", "📣avisos-pm"], "🚓 PMERJ - HIERARQUIA": ["📡radio-oficial", "📡radio-sgt", "📡radio-sd"], "🚨 PMERJ - OP": ["🚨ocorrencias", "📋bo"], "📁 PMERJ - ADM": ["📑oficios", "🔒arsenal"]}},
    "bope": {"nome": "BOPE", "cor": 0x000, "cargos": [{"nome": "💀 Ten Cel BOPE", "permissoes": discord.Permissions(administrator=True)}, {"nome": "⚔️ Cap BOPE", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🎯 Ten BOPE", "permissoes": discord.Permissions(kick_members=True)}, {"nome": "🪖 Sgt BOPE", "permissoes": discord.Permissions()}, {"nome": "🔫 Cb BOPE", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"💀 BOPE - GERAL": ["📢avisos-bope", "📜regras-bope"], "🎯 BOPE - HIERARQUIA": ["📡radio-comando", "📡radio-tropa"], "⚔️ BOPE - OP": ["🚨operações"]}},
    "pcrj": {"nome": "PCERJ", "cor": 0x4B5563, "cargos": [{"nome": "👑 Delegado Geral", "permissoes": discord.Permissions(administrator=True)}, {"nome": "🕵️ Delegado", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🚔 Inspetor", "permissoes": discord.Permissions(kick_members=True)}, {"nome": "📝 Escrivão", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🕵️ PCERJ - INFO": ["📜regras-pc", "📢avisos-pc"], "📁 PCERJ - HIERARQUIA": ["🔍delegacia-geral"], "⚖️ PCERJ - OP": ["📂inqueritos"]}},
    "prf": {"nome": "PRF", "cor": 0x2563EB, "cargos": [{"nome": "👑 Inspetor Chefe", "permissoes": discord.Permissions(administrator=True)}, {"nome": "🚨 Inspetor", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🚔 PRF", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🛣️ PRF - GERAL": ["📢avisos-prf", "📜regras-prf"], "🚓 PRF - HIERARQUIA": ["📡radio-chefia"], "📁 PRF - OP": ["🗺️qth-prf"]}},
    "samu": {"nome": "SAMU", "cor": 0xEF4444, "cargos": [{"nome": "👑 Diretor SAMU", "permissoes": discord.Permissions(administrator=True)}, {"nome": "👨‍⚕️ Médico", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🚑 Enfermeiro", "permissoes": discord.Permissions()}, {"nome": "🚨 Socorrista", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🚑 SAMU - GERAL": ["📢avisos-samu", "📜regras-samu"], "🏥 SAMU - HIERARQUIA": ["📡radio-medico"], "📁 SAMU - OP": ["🚨ocorrencias"]}},
    "detran": {"nome": "DETRAN", "cor": 0xF59E0B, "cargos": [{"nome": "👑 Presidente", "permissoes": discord.Permissions(administrator=True)}, {"nome": "📝 Agente", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🚗 DETRAN - GERAL": ["📢avisos-detran", "📜regras-detran"], "📁 DETRAN - ADM": ["📝cnh"]}},
    "core": {"nome": "CORE", "cor": 0x374151, "cargos": [{"nome": "👑 Coord CORE", "permissoes": discord.Permissions(administrator=True)}, {"nome": "⚔️ Operador CORE", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🖤 CORE - GERAL": ["📢avisos-core", "📜regras-core"], "🎯 CORE - OP": ["🚨operações-core"]}},
    "bpf": {"nome": "BPF", "cor": 0x166534, "cargos": [{"nome": "👑 Maj BPF", "permissoes": discord.Permissions(administrator=True)}, {"nome": "🌲 Cap BPF", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🪖 Sgt BPF", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🌲 BPF - GERAL": ["📢avisos-bpf", "📜regras-bpf"], "🚓 BPF - OP": ["🚨ocorrencias-bpf"]}},
    "gat": {"nome": "GAT", "cor": 0x991B1B, "cargos": [{"nome": "👑 Coord GAT", "permissoes": discord.Permissions(administrator=True)}, {"nome": "🎯 GAT", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🔴 GAT - GERAL": ["📢avisos-gat", "📜regras-gat"], "🎯 GAT - OP": ["🚨ocorrencias-gat"]}},
    "cv": {"nome": "CV", "cor": 0xDC2626, "cargos": [{"nome": "👑 CV - Dono", "permissoes": discord.Permissions(administrator=True)}, {"nome": "💼 CV - Gerente", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🔫 CV - Soldado", "permissoes": discord.Permissions()}, {"nome": "💊 CV - Vapor", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🔴 CV - HIERARQUIA": ["📢avisos-cv", "💬chat-gerencia"], "💰 CV - BOCAS": ["🏪boca-1"], "⚔️ CV - GUERRA": ["⚔️guerra"]}},
    "tcp": {"nome": "TCP", "cor": 0x059669, "cargos": [{"nome": "👑 TCP - Dono", "permissoes": discord.Permissions(administrator=True)}, {"nome": "💼 TCP - Gerente", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🔫 TCP - Soldado", "permissoes": discord.Permissions()}, {"nome": "💊 TCP - Vapor", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🟢 TCP - HIERARQUIA": ["📢avisos-tcp", "💬chat-gerencia"], "💰 TCP - BOCAS": ["🏪boca-1"], "⚔️ TCP - GUERRA": ["⚔️guerra"]}},
    "ada": {"nome": "ADA", "cor": 0x7C3AED, "cargos": [{"nome": "👑 ADA - Dono", "permissoes": discord.Permissions(administrator=True)}, {"nome": "💼 ADA - Gerente", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🔫 ADA - Soldado", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🟣 ADA - HIERARQUIA": ["📢avisos-ada"], "💰 ADA - BOCAS": ["🏪boca-1"], "⚔️ ADA - GUERRA": ["⚔️guerra"]}},
    "pgc": {"nome": "PGC", "cor": 0x1F2937, "cargos": [{"nome": "👑 PGC - Dono", "permissoes": discord.Permissions(administrator=True)}, {"nome": "💼 PGC - Gerente", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🔫 PGC - Soldado", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"⚫ PGC - HIERARQUIA": ["📢avisos-pgc"], "💰 PGC - BOCAS": ["🏪boca-1"], "⚔️ PGC - GUERRA": ["⚔️guerra"]}}
}

# ============ PAINEL COM BOTÃO ============
class PainelRegras(View):
    def __init__(self, cargo_civil):
        super().__init__(timeout=None)
        self.cargo_civil = cargo_civil

    @discord.ui.button(label="✅ Aceitar Regras", style=discord.ButtonStyle.green, emoji="✅", custom_id="aceitar_regras")
    async def aceitar(self, interaction: discord.Interaction, button: Button):
        await interaction.user.add_roles(self.cargo_civil)
        await interaction.response.send_message("✅ Você aceitou as regras! Cargo liberado.", ephemeral=True)

@bot.command()
async def painel(ctx):
    """Cria o painel de regras"""
    cargo_civil = discord.utils.get(ctx.guild.roles, name="👤 Civil")
    if not cargo_civil:
        return await ctx.send("❌ Cargo `👤 Civil` não encontrado. Rode o!setup primeiro.")

    embed = discord.Embed(
        title="📜 REGRAS DO SERVIDOR",
        description="**1.** Respeite todos\n**2.** Sem racismo/homofobia\n**3.** Sem divulgar\n**4.** RP sempre\n**5.** Siga a hierarquia\n\nClique no botão abaixo para liberar o acesso!",
        color=0x2B2D31
    )
    embed.set_footer(text="Bot Criado por Biel")

    view = PainelRegras(cargo_civil)
    await ctx.send(embed=embed, view=view)

# ============ /dono EM 3s ============
@bot.command(name="dono")
@is_dono()
async def dono(ctx, *, descricao=None):
    if not isinstance(ctx.channel, discord.DMChannel):
        return await ctx.send("❌ Use no meu privado")
    if not descricao:
        return await ctx.send("❌ Ex: `!dono crie um comando de setup do core`")

    await ctx.send("⚡ Criando em **3 segundos**...")
    await asyncio.sleep(3)

    nome = gerar_nome(descricao)
    encontrado = None
    for key in TEMPLATES:
        if key in descricao.lower(): encontrado = key; break

    if encontrado:
        db["comandos_dinamicos"][nome] = {"tipo": "setup", "template": encontrado}
        save()
        registrar_setup(nome, encontrado)
        t = TEMPLATES[encontrado]
        embed = discord.Embed(title="✅ COMANDO CRIADO", description=f"Use: `!{nome}`\nOrg: {t['nome']}", color=t["cor"])
        await ctx.send(embed=embed)
    else:
        orgs = ", ".join(TEMPLATES.keys())
        await ctx.send(f"❌ Org não encontrada. Temos: {orgs}")

def gerar_nome(desc):
    for key in TEMPLATES:
        if key in desc.lower(): return "setup" + key
    return "setup" + str(random.randint(10,99))

def registrar_setup(nome, template_key):
    async def comando_setup(ctx, t=template_key):
        await criar_setup(ctx, t)
    bot.add_command(commands.Command(comando_setup, name=nome))

async def criar_setup(ctx, template_key):
    t = TEMPLATES[template_key]
    guild = ctx.guild
    msg = await ctx.send(f"🏗️ **Montando {t['nome']}**... `0%`")

    for role in guild.roles:
        if role.name!= "@everyone" and role.name!= guild.me.name:
            try: await role.delete()
    for channel in guild.channels:
        try: await channel.delete()

    for i, cargo in enumerate(t["cargos"]):
        await guild.create_role(name=cargo["nome"], permissions=cargo["permissoes"], color=discord.Color(t["cor"]))
        porcentagem = int(((i+1)/len(t["cargos"]))*50)
        await msg.edit(content=f"🏗️ **Montando {t['nome']}**... `{porcentagem}%`")

    total = sum(len(c) for c in t["categorias"].values())
    feito = 0
    for cat, canais in t["categorias"].items():
        categoria = await guild.create_category(cat)
        for canal in canais:
            await guild.create_text_channel(canal, category=categoria)
            feito += 1
            porcentagem = 50 + int((feito/total)*50)
            await msg.edit(content=f"🏗️ **Montando {t['nome']}**... `{porcentagem}%`")

    embed = discord.Embed(title=f"✅ {t['nome']} CONFIGURADO", description="Agora use `!painel` para criar o painel de regras", color=t["cor"])
    await msg.edit(content="", embed=embed)

@bot.event
async def on_ready():
    for nome, data in db["comandos_dinamicos"].items():
        if data["tipo"] == "setup": registrar_setup(nome, data["template"])
    print(f'✅ BOT V31 ONLINE - 13 ORGS + PAINEL')

bot.run(os.getenv("TOKEN"))
