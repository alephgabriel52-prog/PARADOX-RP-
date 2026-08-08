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

# ============ MESMOS TEMPLATES PESADOS ============
TEMPLATES = {
    "pmrj": {
        "nome": "PMERJ", "cor": 0x1E3A8A,
        "cargos": [
            {"nome": "👑 Coronel PM", "permissoes": discord.Permissions(administrator=True)},
            {"nome": "⭐ Tenente-Coronel PM", "permissoes": discord.Permissions(manage_roles=True, manage_channels=True)},
            {"nome": "🎖️ Major PM", "permissoes": discord.Permissions(manage_roles=True)},
            {"nome": "⚔️ Capitão PM", "permissoes": discord.Permissions(ban_members=True, kick_members=True)},
            {"nome": "🚔 1º Tenente PM", "permissoes": discord.Permissions(kick_members=True, manage_messages=True)},
            {"nome": "🚓 2º Tenente PM", "permissoes": discord.Permissions(kick_members=True, manage_messages=True)},
            {"nome": "🪖 Aspirante-a-Oficial PM", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "🪖 Subtenente PM", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "🪖 1º Sargento PM", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "🪖 2º Sargento PM", "permissoes": discord.Permissions()},
            {"nome": "🪖 3º Sargento PM", "permissoes": discord.Permissions()},
            {"nome": "👮 Cabo PM", "permissoes": discord.Permissions(mute_members=True)},
            {"nome": "🚨 Soldado 1ª Classe PM", "permissoes": discord.Permissions(send_messages=True, connect=True)},
            {"nome": "🚨 Soldado 2ª Classe PM", "permissoes": discord.Permissions(send_messages=True, connect=True)},
            {"nome": "📋 Adj Comandamento", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "📋 Adj Operações", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "📋 Adj Pessoal", "permissoes": discord.Permissions()},
            {"nome": "📋 Adj Logística", "permissoes": discord.Permissions()},
            {"nome": "📋 Adj Inteligência", "permissoes": discord.Permissions()},
            {"nome": "🎯 GATE", "permissoes": discord.Permissions()},
            {"nome": "🐕 K9", "permissoes": discord.Permissions()},
            {"nome": "🏍️ ROCAM", "permissoes": discord.Permissions()},
            {"nome": "🚁 AEROPOL", "permissoes": discord.Permissions()},
            {"nome": "🚤 GPAER", "permissoes": discord.Permissions()},
            {"nome": "🏥 SAÚDE PM", "permissoes": discord.Permissions()},
            {"nome": "⚖️ CORREGEDORIA", "permissoes": discord.Permissions(ban_members=True)},
            {"nome": "📚 INSTRUTOR", "permissoes": discord.Permissions()},
            {"nome": "📢 ASSESSORIA", "permissoes": discord.Permissions()},
            {"nome": "💰 FINANCEIRO", "permissoes": discord.Permissions()},
            {"nome": "🔧 MANUTENÇÃO", "permissoes": discord.Permissions()},
            {"nome": "📡 COMUNICAÇÕES", "permissoes": discord.Permissions()},
            {"nome": "👤 Civil", "permissoes": discord.Permissions(send_messages=True, connect=True)}
        ],
        "categorias": {
            "📢 PMERJ - INFORMAÇÕES": ["📜│regras-pm", "📣│avisos-gerais", "🎖️│promocoes", "📅│escala-servico", "📊│efetivo"],
            "🚓 PMERJ - COMANDO GERAL": ["📡│radio-coronel", "📡│radio-oficiais", "📋│bo-comando", "📑│portarias", "📊│relatorios"],
            "🚨 PMERJ - OPERAÇÕES": ["📡│radio-geral", "🚨│190", "🗺️│qth", "📋│bo", "📝│entrada-e-saida", "🎯│patrulhamento", "🚔│viaturas"],
            "🔒 PMERJ - ADMINISTRATIVO": ["🔒│arsenal", "🚗│garagem", "📚│doutrina", "🏥│saude-pm", "💰│folha-pagamento", "📋│processos"],
            "🎯 PMERJ - FORÇAS ESPECIAIS": ["🎯│gate", "🐕│k9", "🏍️│rocam", "🚁│aeropol", "🚤│gpaer"],
            "💬 PMERJ - GERAL": ["💬│chat-geral", "📸│midias", "🎮│sugestoes", "🎤│reunioes"]
        }
    },
    "bope": {
        "nome": "BOPE", "cor": 0x000,
        "cargos": [
            {"nome": "💀 Tenente-Coronel BOPE", "permissoes": discord.Permissions(administrator=True)},
            {"nome": "⚔️ Major BOPE", "permissoes": discord.Permissions(manage_roles=True)},
            {"nome": "🎯 Capitão BOPE", "permissoes": discord.Permissions(ban_members=True)},
            {"nome": "🔫 1º Tenente BOPE", "permissoes": discord.Permissions(kick_members=True)},
            {"nome": "🔫 2º Tenente BOPE", "permissoes": discord.Permissions(kick_members=True)},
            {"nome": "🪖 Aspirante BOPE", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "🪖 Subtenente BOPE", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "🪖 1º Sargento BOPE", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "🪖 2º Sargento BOPE", "permissoes": discord.Permissions()},
            {"nome": "🪖 3º Sargento BOPE", "permissoes": discord.Permissions()},
            {"nome": "👮 Cabo BOPE", "permissoes": discord.Permissions()},
            {"nome": "🚨 Soldado BOPE", "permissoes": discord.Permissions()},
            {"nome": "💣 ESPECIALISTA EXPLOSIVOS", "permissoes": discord.Permissions()},
            {"nome": "🎯 ATIRADOR DE ELITE", "permissoes": discord.Permissions()},
            {"nome": "🏥 MÉDICO BOPE", "permissoes": discord.Permissions()},
            {"nome": "🚁 PILOTO BOPE", "permissoes": discord.Permissions()},
            {"nome": "🔒 NEGOCIADOR", "permissoes": discord.Permissions()},
            {"nome": "📡 COMUNICAÇÕES", "permissoes": discord.Permissions()},
            {"nome": "🔧 ARMAMENTO", "permissoes": discord.Permissions()},
            {"nome": "📊 INTELIGENCIA", "permissoes": discord.Permissions()},
            {"nome": "👤 Civil", "permissoes": discord.Permissions()}
        ],
        "categorias": {
            "💀 BOPE - GERAL": ["📢│avisos-bope", "📜│regras-bope", "🎯│treinamento", "📊│estatisticas"],
            "🎯 BOPE - COMANDO": ["📡│radio-comando", "📊│relatorios", "📑│oficios-bope", "💣│explosivos", "🔒│arquivo-secreto"],
            "⚔️ BOPE - OPERAÇÕES": ["🚨│operações-especiais", "🗺️│qth-bope", "📋│bo-bope", "📡│radio-tropa", "🎯│missões"],
            "🔒 BOPE - LOGÍSTICA": ["🔒│arsenal-bope", "🚁│aeronaves", "📦│suprimentos"]
        }
    },
    "pcrj": {
        "nome": "PCERJ", "cor": 0x4B5563,
        "cargos": [
            {"nome": "👑 Delegado-Geral", "permissoes": discord.Permissions(administrator=True)},
            {"nome": "🕵️ Subsecretário", "permissoes": discord.Permissions(manage_roles=True)},
            {"nome": "🕵️ Delegado Titular", "permissoes": discord.Permissions(manage_roles=True)},
            {"nome": "🕵️ Delegado Adjunto", "permissoes": discord.Permissions(manage_roles=True)},
            {"nome": "🚔 Inspetor Chefe", "permissoes": discord.Permissions(kick_members=True)},
            {"nome": "🚔 Inspetor", "permissoes": discord.Permissions(kick_members=True)},
            {"nome": "📝 Escrivão Chefe", "permissoes": discord.Permissions()},
            {"nome": "📝 Escrivão", "permissoes": discord.Permissions()},
            {"nome": "🔎 Perito Criminal", "permissoes": discord.Permissions()},
            {"nome": "🔎 Papiloscopista", "permissoes": discord.Permissions()},
            {"nome": "🔎 Técnico Policial", "permissoes": discord.Permissions()},
            {"nome": "📊 ANALISTA", "permissoes": discord.Permissions()},
            {"nome": "🔒 DGI", "permissoes": discord.Permissions()},
            {"nome": "🔒 DRCO", "permissoes": discord.Permissions()},
            {"nome": "🔒 DH", "permissoes": discord.Permissions()},
            {"nome": "🔒 DPCA", "permissoes": discord.Permissions()},
            {"nome": "👤 Civil", "permissoes": discord.Permissions()}
        ],
        "categorias": {
            "🕵️ PCERJ - GERAL": ["📜│regras-pc", "📢│avisos-pc", "📊│estatisticas"],
            "📁 PCERJ - DELEGACIA": ["🔍│gabinete-delegado", "📂│inquerito-policial", "📝│registro-ocorrencia", "🔎│aipe", "🔒│dgi", "🔒│drco"],
            "⚖️ PCERJ - ADM": ["📊│estatistica", "📑│oficios-pc", "📞│disque-denuncia", "🔍│inteligencia"],
            "🏛️ PCERJ - ESPECIALIZADAS": ["🔒│dh", "🔒│dpca", "🔒│deam"]
        }
    },
    "cv": {
        "nome": "CV", "cor": 0xDC2626,
        "cargos": [
            {"nome": "👑 CV - Dono", "permissoes": discord.Permissions(administrator=True)},
            {"nome": "💼 CV - Gerente Geral", "permissoes": discord.Permissions(manage_roles=True)},
            {"nome": "💼 CV - Gerente", "permissoes": discord.Permissions(manage_roles=True)},
            {"nome": "🔫 CV - Soldado", "permissoes": discord.Permissions()},
            {"nome": "🔫 CV - Fogueteiro", "permissoes": discord.Permissions()},
            {"nome": "🔫 CV - Olheiro", "permissoes": discord.Permissions()},
            {"nome": "💊 CV - Vapor", "permissoes": discord.Permissions()},
            {"nome": "💰 CV - LAVADOR", "permissoes": discord.Permissions()},
            {"nome": "📦 CV - ESTOQUISTA", "permissoes": discord.Permissions()},
            {"nome": "🎯 CV - ATIRADOR", "permissoes": discord.Permissions()},
            {"nome": "📊 CV - FINANCEIRO", "permissoes": discord.Permissions()},
            {"nome": "👤 Civil", "permissoes": discord.Permissions()}
        ],
        "categorias": {
            "🔴 CV - HIERARQUIA": ["📢│avisos-cv", "💬│chat-gerencia", "💬│chat-soldado", "📋│lista-negra", "📊│relatorios"],
            "💰 CV - BOCAS": ["🏪│boca-mangueira", "🏪│boca-alemao", "🏪│boca-rocinha", "🏪│boca-vg", "📦│estoque", "💰│lavagem"],
            "⚔️ CV - GUERRA": ["⚔️│guerra", "📝│contratos", "📊│caixa", "🎯│ataque", "🗺️│territorio"],
            "🔒 CV - LOGÍSTICA": ["📦│armas", "💊│drogas", "💰│dinheiro"]
        }
    },
    "tcp": {"nome": "TCP", "cor": 0x059669, "cargos": [{"nome": "👑 TCP - Dono", "permissoes": discord.Permissions(administrator=True)}, {"nome": "💼 TCP - Gerente Geral", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "💼 TCP - Gerente", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🔫 TCP - Soldado", "permissoes": discord.Permissions()}, {"nome": "🔫 TCP - Fogueteiro", "permissoes": discord.Permissions()}, {"nome": "🔫 TCP - Olheiro", "permissoes": discord.Permissions()}, {"nome": "💊 TCP - Vapor", "permissoes": discord.Permissions()}, {"nome": "💰 TCP - LAVADOR", "permissoes": discord.Permissions()}, {"nome": "📦 TCP - ESTOQUISTA", "permissoes": discord.Permissions()}, {"nome": "🎯 TCP - ATIRADOR", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🟢 TCP - HIERARQUIA": ["📢│avisos-tcp", "💬│chat-gerencia", "💬│chat-soldado", "📋│lista-negra"], "💰 TCP - BOCAS": ["🏪│boca-vg", "🏪│boca-cidade-deus", "🏪│boca-jacare", "🏪│boca-vasco", "📦│estoque", "💰│lavagem"], "⚔️ TCP - GUERRA": ["⚔️│guerra", "📊│caixa", "🎯│ataque"]}},
    "ada": {"nome": "ADA", "cor": 0x7C3AED, "cargos": [{"nome": "👑 ADA - Dono", "permissoes": discord.Permissions(administrator=True)}, {"nome": "💼 ADA - Gerente", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🔫 ADA - Soldado", "permissoes": discord.Permissions()}, {"nome": "🔫 ADA - Fogueteiro", "permissoes": discord.Permissions()}, {"nome": "🔫 ADA - Olheiro", "permissoes": discord.Permissions()}, {"nome": "💊 ADA - Vapor", "permissoes": discord.Permissions()}, {"nome": "💰 ADA - LAVADOR", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🟣 ADA - HIERARQUIA": ["📢│avisos-ada", "💬│chat-gerencia", "💬│chat-soldado"], "💰 ADA - BOCAS": ["🏪│boca-mare", "🏪│boca-penha", "🏪│boca-vila-cruzeiro", "📦│estoque"], "⚔️ ADA - GUERRA": ["⚔️│guerra", "📊│caixa"]}},
    "pgc": {"nome": "PGC", "cor": 0x1F2937, "cargos": [{"nome": "👑 PGC - Dono", "permissoes": discord.Permissions(administrator=True)}, {"nome": "💼 PGC - Gerente", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🔫 PGC - Soldado", "permissoes": discord.Permissions()}, {"nome": "🔫 PGC - Fogueteiro", "permissoes": discord.Permissions()}, {"nome": "🔫 PGC - Olheiro", "permissoes": discord.Permissions()}, {"nome": "💊 PGC - Vapor", "permissoes": discord.Permissions()}, {"nome": "💰 PGC - LAVADOR", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"⚫ PGC - HIERARQUIA": ["📢│avisos-pgc", "💬│chat-gerencia", "💬│chat-soldado"], "💰 PGC - BOCAS": ["🏪│boca-vila-cruzeiro", "🏪│boca-parada-de-lucas", "🏪│boca-penha", "📦│estoque"], "⚔️ PGC - GUERRA": ["⚔️│guerra", "📊│caixa"]}},
    "prf": {"nome": "PRF", "cor": 0x2563EB, "cargos": [{"nome": "👑 Inspetor-Chefe PRF", "permissoes": discord.Permissions(administrator=True)}, {"nome": "🚨 Inspetor PRF", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🚔 Agente PRF", "permissoes": discord.Permissions()}, {"nome": "🚔 Agente Especial", "permissoes": discord.Permissions()}, {"nome": "🛣️ FISCALIZAÇÃO", "permissoes": discord.Permissions()}, {"nome": "🚨 BPRV", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🛣️ PRF - GERAL": ["📢│avisos-prf", "📜│regras-prf"], "🚓 PRF - RODOVIAS": ["📡│radio-prf", "🗺️│qth-prf", "🚨│acidentes", "📑│autos-infracao", "🚗│fiscalizacao"], "📁 PRF - ADM": ["📊│relatorios-prf", "🚗│frota"]}},
    "samu": {"nome": "SAMU 192", "cor": 0xEF4444, "cargos": [{"nome": "👑 Diretor SAMU", "permissoes": discord.Permissions(administrator=True)}, {"nome": "👨‍⚕️ Médico Regulador", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "👨‍⚕️ Médico Intervencionista", "permissoes": discord.Permissions()}, {"nome": "🚑 Enfermeiro", "permissoes": discord.Permissions()}, {"nome": "🚨 Técnico de Enfermagem", "permissoes": discord.Permissions()}, {"nome": "🚨 Condutor Socorrista", "permissoes": discord.Permissions()}, {"nome": "📞 TARM", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🚑 SAMU - GERAL": ["📢│avisos-samu", "📜│regras-samu"], "🏥 SAMU - OPERAÇÕES": ["📡│radio-samu", "🚨│192", "📊│pacientes", "🚑│usa", "🚑│usb", "🏥│hospital"], "📁 SAMU - ADM": ["📝│escala", "📋│relatorios-samu"]}},
    "detran": {"nome": "DETRAN-RJ", "cor": 0xF59E0B, "cargos": [{"nome": "👑 Presidente DETRAN", "permissoes": discord.Permissions(administrator=True)}, {"nome": "📝 Diretor", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "📝 Agente de Trânsito", "permissoes": discord.Permissions()}, {"nome": "📝 Vistoriador", "permissoes": discord.Permissions()}, {"nome": "📝 Examinador", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🚗 DETRAN - GERAL": ["📢│avisos-detran", "📜│regras-detran"], "📁 DETRAN - ADM": ["📝│cnh", "🚙│veiculos", "📑│multas", "📊│estatistica", "💰│arrecadacao"]}},
    "core": {"nome": "CORE", "cor": 0x374151, "cargos": [{"nome": "👑 Coordenador CORE", "permissoes": discord.Permissions(administrator=True)}, {"nome": "⚔️ Delegado CORE", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "⚔️ Policial CORE", "permissoes": discord.Permissions()}, {"nome": "⚔️ OPERADOR TÁTICO", "permissoes": discord.Permissions()}, {"nome": "🔎 ANALISTA INTEL", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🖤 CORE - GERAL": ["📢│avisos-core", "📜│regras-core"], "🎯 CORE - OP": ["🚨│operações-core", "📊│inteligencia", "📋│relatorios", "🔒│arquivo-secreto"]}},
    "bpf": {"nome": "BPF", "cor": 0x166534, "cargos": [{"nome": "👑 Major BPF", "permissoes": discord.Permissions(administrator=True)}, {"nome": "🌲 Capitão BPF", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🪖 Tenente BPF", "permissoes": discord.Permissions()}, {"nome": "🪖 Sargento BPF", "permissoes": discord.Permissions()}, {"nome": "👮 Cabo BPF", "permissoes": discord.Permissions()}, {"nome": "🚨 Soldado BPF", "permissoes": discord.Permissions()}, {"nome": "🐕 K9 BPF", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🌲 BPF - GERAL": ["📢│avisos-bpf", "📜│regras-bpf"], "🚓 BPF - OP": ["🚨│ocorrencias-bpf", "🗺️│mata", "📡│radio-bpf", "🎯│patrulha-rural"]}},
    "gat": {"nome": "GAT", "cor": 0x991B1B, "cargos": [{"nome": "👑 Coordenador GAT", "permissoes": discord.Permissions(administrator=True)}, {"nome": "🎯 Tenente GAT", "permissoes": discord.Permissions(manage_roles=True)}, {"nome": "🎯 GAT", "permissoes": discord.Permissions()}, {"nome": "🎯 ATIRADOR GAT", "permissoes": discord.Permissions()}, {"nome": "👤 Civil", "permissoes": discord.Permissions()}], "categorias": {"🔴 GAT - GERAL": ["📢│avisos-gat", "📜│regras-gat"], "🎯 GAT - OP": ["🚨│ocorrencias-gat", "📡│radio-gat", "🗺️│qth-gat"]}}
}

# ============ PAINEL ============
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
    cargo_civil = discord.utils.get(ctx.guild.roles, name="👤 Civil")
    if not cargo_civil: return await ctx.send("❌ Cargo `👤 Civil` não encontrado. Rode o!setup primeiro.")
    embed = discord.Embed(title="📜 REGRAS DO SERVIDOR", description="**1.** Respeite todos\n**2.** Sem racismo/homofobia\n**3.** Sem divulgar\n**4.** RP sempre\n**5.** Siga a hierarquia\nClique no botão abaixo para liberar o acesso!", color=0x2B2D31)
    embed.set_footer(text="Bot Criado por Biel")
    await ctx.send(embed=embed, view=PainelRegras(cargo_civil))

# ============ /dono EM 3s ============
@bot.command(name="dono")
@is_dono()
async def dono(ctx, *, descricao=None):
    if not isinstance(ctx.channel, discord.DMChannel): return await ctx.send("❌ Use no meu privado")
    if not descricao: return await ctx.send("❌ Ex: `!dono crie um comando de setup do bope`")
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
        await ctx.send(embed=discord.Embed(title="✅ COMANDO CRIADO", description=f"Use: `!{nome}`\nOrg: {t['nome']}\n**{len(t['cargos'])} Cargos | {sum(len(c) for c in t['categorias'].values())} Canais**", color=t["cor"]))
    else: await ctx.send(f"❌ Org não encontrada. Temos: {', '.join(TEMPLATES.keys())}")

def gerar_nome(desc):
    for key in TEMPLATES:
        if key in desc.lower(): return "setup" + key
    return "setup" + str(random.randint(10,99))

def registrar_setup(nome, 
