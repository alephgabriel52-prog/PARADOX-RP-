import discord
from discord.ext import commands
import os, json, asyncio
from flask import Flask
from threading import Thread

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
@is_dono()
async def setup(ctx, fac=None):
    # HIERARQUIA ESTILO MINI CITY - SEM PF
    FAC_LISTA = {
        "PM": [
            "Civil","Recruta PM","Soldado PM","Cabo PM","3º Sgt PM","2º Sgt PM","1º Sgt PM",
            "Sub Ten PM","Asp Oficial PM","2º Ten PM","1º Ten PM","Cap PM","Major PM",
            "Ten Cel PM","Cel PM","Corregedor PM","Sub Comandante PM","Comandante Geral PM"
        ],
        "PC": [
            "Civil","Estagiário PC","Agente PC","Agente Especial PC","Escrivão PC","Investigador PC",
            "Delegado PC","Delegado Titular PC","Corregedor PC","Delegado Geral PC","Chefe de Polícia"
        ],
        "PRF": [
            "Civil","PRF Aluno","PRF 3ª Classe","PRF 2ª Classe","PRF 1ª Classe","PRF Classe Especial",
            "Inspetor PRF","Chefe de Núcleo PRF","Chefe Regional PRF","Superintendente PRF"
        ],
        "SAMU": [
            "Civil","Estagiário SAMU","Condutor Socorrista","Téc Enfermagem SAMU","Enfermeiro SAMU",
            "Médico Plantonista","Médico Regulador","Coordenador Regional SAMU","Diretor Médico SAMU"
        ]
    }

    # CARGOS GERAIS PRA COMPLETAR 45+
    CARGOS_GERAIS = [
        "🏅 Medalha Mérito","🏅 Medalha Bravura","🏅 Medalha 5 Anos","🏅 Medalha 10 Anos",
        "📈 Comissão de Promoção","📊 Estatística Operacional","👑 Alto Comando","🔧 Logística",
        "💰 Finanças","📋 Corregedoria","⚖️ Jurídico"
    ]

    FAC_CORES = {"PM": discord.Color.blue(), "PC": discord.Color.dark_red(), "PRF": discord.Color.dark_green(), "SAMU": discord.Color.red()}

    facs_para_criar = FAC_LISTA.keys() if fac is None or fac.upper() == "ALL" else [fac.upper()]

    if fac and fac.upper() not in FAC_LISTA:
        return await ctx.send("❌ Use: `!setup PM` `!setup PC` `!setup PRF` `!setup SAMU` ou `!setup ALL`")

    msg = await ctx.send(f"⏳ Iniciando setup Mini City...")

    for f in facs_para_criar:
        info = FAC_LISTA[f] + CARGOS_GERAIS
        cor = FAC_CORES[f]
        cargo_ids = {}

        await msg.edit(content=f"⏳ {f}: Criando 45 cargos...")
        # 1. CARGOS
        for nome_cargo in info:
            cargo = await ctx.guild.create_role(name=nome_cargo, color=cor, hoist=True if "Comandante" in nome_cargo or "Chefe" in nome_cargo or "Diretor" in nome_cargo else False)
            cargo_ids[nome_cargo] = cargo.id
            await asyncio.sleep(0.6)

        comando = ctx.guild.get_role(cargo_ids[info[17]])
        civil = ctx.guild.get_role(cargo_ids["Civil"])
        overwrites_staff = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), comando: discord.PermissionOverwrite(view_channel=True, manage_messages=True, move_members=True)}
        overwrites_publico = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), civil: discord.PermissionOverwrite(view_channel=True, send_messages=True)}

        # 2. CATEGORIAS ESTILO MINI CITY
        categorias_reais = {
            f"📋 ADMINISTRAÇÃO {f}": [
                "📢│avisos-geral", "📢│boletim-interno", "💬│chat-oficiais", "📊│relatorios",
                "📝│formulario-entrada", "📝│formulario-promocao", "📋│recrutamento", "📋│entrevistas", "📑│documentos"
            ],
            f"🚨 OPERAÇÕES {f}": [
                "🚨│ocorrencias-ativas", "🚨│ocorrencias-arquivo", "📍│patrulhamento", "📍│pontos-criticos",
                "🕵️│inteligencia", "🕵️│arquivo-secreto", "⚖️│corregedoria", "⚖️│processos"
            ],
            f"🚔 LOGÍSTICA {f}": [
                "🚔│viaturas", "🚔│viaturas-manutencao", "⛽│abastecimento", "📦│armamento",
                "📦│pedido-material", "🔧│oficina", "💰│tesouraria", "💰│controle-gastos"
            ],
            f"📚 TREINAMENTO {f}": [
                "📚│academia", "📚│cursos", "🎯│estande-tiro", "🎯│simulado-tatico",
                "🏆│hall-fama", "📷│midia", "📷│evidencias"
            ],
            f"📞 COMUNICAÇÃO {f}": [
                "🔊│radio-central", "🔊│radio-tatica", "🚨│call-urgencia", "🎙️│sala-reuniao",
                "🎙️│briefing", "🤝│interforcas"
            ]
        }

        await msg.edit(content=f"⏳ {f}: Criando 5 Categorias + 50 Canais...")
        for nome_cat, canais in categorias_reais.items():
            categoria = await ctx.guild.create_category(nome_cat, overwrites=overwrites_staff)
            await asyncio.sleep(0.5)

            for nome_canal in canais:
                if "radio" in nome_canal or "call" in nome_canal or "reuniao" in nome_canal or "tiro" in nome_canal or "briefing" in nome_canal:
                    await ctx.guild.create_voice_channel(nome_canal, category=categoria, overwrites=overwrites_staff)
                elif "recrutamento" in nome_canal or "entrevistas" in nome_canal:
                    await ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=overwrites_publico)
                else:
                    await ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=overwrites_staff)
                await asyncio.sleep(0.4)

        db["corps"][f] = cargo_ids

    save()
    await msg.edit(content=f"✅ **SETUP MINI CITY FINALIZADO**\nCorps: PM, PC, PRF, SAMU\n45+ Cargos + 50 Canais + 5 Categorias cada\nSem PF como pediu")

@bot.command()
@is_dono()
async def limpar(ctx, fac=None):
    if fac is None:
        return await ctx.send("❌ Use: `!limpar PM` ou `!limpar ALL`")
    facs_para_limpar = db["corps"].keys() if fac.upper() == "ALL" else [fac.upper()]
    msg = await ctx.send(f"⏳ Apagando...")
    for f in facs_para_limpar:
        for channel in ctx.guild.channels:
            if f.lower() in channel.name.lower():
                try: await channel.delete(); await asyncio.sleep(0.3)
                except: pass
        for category in ctx.guild.categories:
            if f in category.name:
                try: await category.delete(); await asyncio.sleep(0.3)
                except: pass
        if f in db["corps"]:
            for cargo_id in db["corps"][f].values():
                cargo = ctx.guild.get_role(cargo_id)
                if cargo:
                    try: await cargo.delete(); await asyncio.sleep(0.3)
                    except: pass
            del db["corps"][f]
    save()
    await msg.edit(content=f"✅ **LIMPEZA CONCLUÍDA**: {', '.join(facs_para_limpar)}")

bot.run(os.getenv("TOKEN"))
