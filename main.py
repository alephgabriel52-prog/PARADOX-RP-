import discord
from discord.ext import commands
import os, json, asyncio, random, re
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

# ============ TODOS OS TEMPLATES DA CIDADE ============
TEMPLATES = {
    # CORPORAÇÕES
    "pmrj": {"nome": "PMERJ", "cargos": ["Cel PM", "Ten Cel", "Cap PM", "Sgt PM", "Cb PM", "Sd PM", "Civil"], "categorias": {"🚨 PMERJ": ["avisos-pm", "patrulha", "ocorrencias"]}, "regras": "1. Hierarquia\n2. RP"},
    "prf": {"nome": "PRF", "cargos": ["PRF - Diretor", "PRF - Inspetor", "PRF - Agente", "Civil"], "categorias": {"🛣️ PRF": ["blitz", "patrulhamento"]}, "regras": "Lei 9.503"},
    "bope": {"nome": "BOPE", "cargos": ["BOPE - Comandante", "BOPE - Caveira", "Civil"], "categorias": {"💀 BOPE": ["operacoes", "arsenal"]}, "regras": "Elite PM"},
    "samu": {"nome": "SAMU", "cargos": ["SAMU - Diretor", "SAMU - Médico", "SAMU - Condutor", "Civil"], "categorias": {"🏥 SAMU": ["plantao", "ocorrencias"]}, "regras": "Salvar vidas"},
    "hospital": {"nome": "HOSPITAL", "cargos": ["HOSP - Diretor", "HOSP - Médico", "HOSP - Enfermeiro", "Civil"], "categorias": {"🏥 HOSPITAL": ["emergencia", "cirurgia"]}, "regras": "Atender todos"},
    "prefeitura": {"nome": "PREFEITURA", "cargos": ["Prefeito", "Secretário", "Funcionario", "Civil"], "categorias": {"🏛️ PREFEITURA": ["leis", "concursos"]}, "regras": "Cuidar da cidade"},
    "detran": {"nome": "DETRAN", "cargos": ["DETRAN - Diretor", "DETRAN - Atendente", "DETRAN - Vistoriador", "Civil"], "categorias": {"🚗 DETRAN": ["habilitacao", "vistoria", "multas"]}, "regras": "1. Fazer CNH\n2. Vistoriar veículos"},
    "bombeiros": {"nome": "BOMBEIROS", "cargos": ["BOMBEIRO - Comandante", "BOMBEIRO - Tenente", "BOMBEIRO - Soldado", "Civil"], "categorias": {"🚒 BOMBEIROS": ["incendio", "resgate", "ocorrencias"]}, "regras": "1. Salvar vidas\n2. Apagar fogo"},
    "governo": {"nome": "GOVERNO", "cargos": ["Governador", "Vice-Governador", "Ministro", "Assessor", "Civil"], "categorias": {"🏛️ GOVERNO": ["leis-estaduais", "decretos", "gabinete"]}, "regras": "1. Governar estado"},
    "oab": {"nome": "OAB", "cargos": ["OAB - Presidente", "OAB - Advogado", "OAB - Estagiário", "Civil"], "categorias": {"⚖️ OAB": ["processos", "audiencias", "escritorio"]}, "regras": "1. Defender clientes"},
    "uber": {"nome": "UBER", "cargos": ["UBER - Gerente", "UBER - Motorista", "Civil"], "categorias": {"🚕 UBER": ["corridas", "suporte-motorista"]}, "regras": "1. Levar passageiro"},

    # FACÇÕES
    "cv": {"nome": "CV", "cargos": ["CV - Dono", "CV - Gerente", "CV - Soldado", "CV - Vapor", "Civil"], "categorias": {"🔴 CV": ["geral-cv", "vendas", "guerra"]}, "regras": "1. Lealdade\n2. Não x9"},
    "tcp": {"nome": "TCP", "cargos": ["TCP - Dono", "TCP - Gerente", "TCP - Soldado", "Civil"], "categorias": {"🟢 TCP": ["geral-tcp", "vendas"]}, "regras": "1. Família"},
    "ada": {"nome": "ADA", "cargos": ["ADA - Dono", "ADA - Gerente", "ADA - Soldado", "Civil"], "categorias": {"🔵 ADA": ["geral-ada", "vendas"]}, "regras": "1. União"},
    "pcc": {"nome": "PCC", "cargos": ["PCC - Sintonia", "PCC - Gerente", "PCC - Soldado", "Civil"], "categorias": {"⚫ PCC": ["geral-pcc", "vendas", "justica"]}, "regras": "1. Igualdade\n2. Liberdade"},
    "terceiro": {"nome": "TERCEIRO", "cargos": ["3C - Dono", "3C - Gerente", "3C - Soldado", "Civil"], "categorias": {"⚫ TERCEIRO": ["geral-3c", "vendas"]}, "regras": "1. Negócio"},
    "milicia": {"nome": "MILÍCIA", "cargos": ["Miliciano - Chefe", "Miliciano - Soldado", "Civil"], "categorias": {"🟡 MILÍCIA": ["geral-milicia", "cobrança"]}, "regras": "1. Proteger área"}
}

# ============ /dono VIA DM ============
@bot.command(name="dono")
@is_dono()
async def dono(ctx, *, descricao=None):
    if not isinstance(ctx.channel, discord.DMChannel):
        return await ctx.send("❌ Use no meu privado")
    if not descricao:
        return await ctx.send("❌ Ex: `!dono crie um comando de setup do detran`")

    await ctx.send("🤖 Criando em 10 segundos...")
    await asyncio.sleep(10)

    nome = gerar_nome(descricao)
    encontrado = None
    for key in TEMPLATES:
        if key in descricao.lower():
            encontrado = key
            break

    if encontrado:
        db["comandos_dinamicos"][nome] = {"tipo": "setup", "template": encontrado}
        save()
        registrar_setup(nome, encontrado)
        t = TEMPLATES[encontrado]
        return await ctx.send(f"✅ **PRONTO CHEFE!**\nComando: `!{nome}`\nTemplate: **{t['nome']}**")

    resposta = gerar_resposta_ia(descricao)
    db["comandos_dinamicos"][nome] = {"tipo": "normal", "resposta": resposta}
    save()
    registrar_normal(nome, resposta)
    await ctx.send(f"✅ **PRONTO CHEFE!**\nComando: `!{nome}`")

def gerar_nome(desc):
    for key in TEMPLATES:
        if key in desc.lower(): return "setup" + key
    palavras = re.findall(r'\w+', desc.lower())
    for p in palavras:
        if p not in ["crie","comando","que"] and len(p)>3: return p
    return "cmd"+str(random.randint(10,99))

def gerar_resposta_ia(desc):
    if "avisa" in desc: return "⚠️ {membro} {args}"
    if "ban" in desc: return "🔨 {membro} banido. Motivo: {args}"
    return f"✅ {desc}"

def registrar_setup(nome, template_key):
    async def comando_setup(ctx, t=template_key):
        await criar_setup(ctx, t)
    bot.add_command(commands.Command(comando_setup, name=nome))

def registrar_normal(nome, resposta):
    async def comando_dinamico(ctx, *, args=None, r=resposta, n=nome):
        resp = r.replace("{membro}", ctx.author.mention).replace("{args}", args if args else "")
        await ctx.send(resp)
        dono = bot.get_user(DONO_ID)
        if dono: await dono.send(f"📊 `!{n}` usado por {ctx.author}")
    bot.add_command(commands.Command(comando_dinamico, name=nome))

async def criar_setup(ctx, template_key):
    t = TEMPLATES[template_key]
    guild = ctx.guild
    await ctx.send(f"🏗️ Criando **{t['nome']}**...")

    for cargo in t["cargos"]:
        await guild.create_role(name=cargo)
        await asyncio.sleep(0.2)

    for cat, canais in t["categorias"].items():
        categoria = await guild.create_category(cat)
        for canal in canais:
            await guild.create_text_channel(canal, category=categoria)
            await asyncio.sleep(0.1)

    await ctx.send(f"✅ **{t['nome']} CRIADO!**")

@bot.event
async def on_ready():
    for nome, data in db["comandos_dinamicos"].items():
        if data["tipo"] == "setup":
            registrar_setup(nome, data["template"])
        else:
            registrar_normal(nome, data["resposta"])
    print(f'✅ BOT V24 ONLINE - {len(TEMPLATES)} templates carregados')

@bot.command()
@is_dono()
async def listacomandos(ctx):
    if not isinstance(ctx.channel, discord.DMChannel): return
    txt = "\n".join([f"!{k} - {TEMPLATES[v['template']]['nome']}" for k,v in db["comandos_dinamicos"].items() if v['tipo']=='setup'])
    await ctx.send(f"**📜 SETUPS CRIADOS**\n{txt}")

bot.run(os.getenv("TOKEN"))
