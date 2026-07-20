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
    # HIERARQUIA + DIVISÕES ESTILO MINI CITY
    FAC_LISTA = {
        "PM": {
            "cargos": ["Civil","Recruta PM","Soldado PM","Cabo PM","3º Sgt PM","2º Sgt PM","1º Sgt PM","Sub Ten PM","Asp Oficial PM","2º Ten PM","1º Ten PM","Cap PM","Major PM","Ten Cel PM","Cel PM","Corregedor PM","Sub Comandante PM","Comandante Geral PM"],
            "divisoes": ["🚔 BATALHÃO", "⚡ ROTA", "🛡️ BOP", "🚨 CHOQUE", "🚁 AEROPOL"]
        },
        "PC": {
            "cargos": ["Civil","Estagiário PC","Agente PC","Agente Especial PC","Escrivão PC","Investigador PC","Delegado PC","Delegado Titular PC","Corregedor PC","Delegado Geral PC","Chefe de Polícia"],
            "divisoes": ["🔍 DHPP", "💰 DEIC", "🕵️ DEAM", "💊 DENARC", "🚔 DP Geral"]
        },
        "PRF": {
            "cargos": ["Civil","PRF Aluno","PRF 3ª Classe","PRF 2ª Classe","PRF 1ª Classe","PRF Classe Especial","Inspetor PRF","Chefe de Núcleo PRF","Chefe Regional PRF","Superintendente PRF"],
            "divisoes": ["🛣️ Patrulhamento", "📦 Fiscalização", "🚨 Operações", "📊 Educação", "🆘 Resgate"]
        },
        "SAMU": {
            "cargos": ["Civil","Estagiário SAMU","Condutor Socorrista","Téc Enfermagem SAMU","Enfermeiro SAMU","Médico Plantonista","Médico Regulador","Coordenador Regional SAMU","Diretor Médico SAMU"],
            "divisoes": ["🚑 USB Básica", "🚑 USA Avançada", "🏥 Regulação Médica", "📞 Call Center", "🔧 Frota"]
        }
    }

    CARGOS_GERAIS = [
        "🏅 Medalha Mérito","🏅 Medalha Bravura","🏅 Medalha 5 Anos","🏅 Medalha 10 Anos",
        "📈 Comissão de Promoção","📊 Estatística","👑 Alto Comando","🔧 Logística","💰 Finanças"
    ]

    FAC_CORES = {"PM": discord.Color.blue(), "PC": discord.Color.dark_red(), "PRF": discord.Color.dark_green(), "SAMU": discord.Color.red()}

    facs_para_criar = FAC_LISTA.keys() if fac is None or fac.upper() == "ALL" else [fac.upper()]

    if fac and fac.upper() not in FAC_LISTA:
        return await ctx.send("❌ Use: `!setup PM` `!setup PC` `!setup PRF` `!setup SAMU` ou `!setup ALL`")

    msg = await ctx.send(f"⏳ Iniciando setup com Divisões...")

    for f in facs_para_criar:
        dados = FAC_LISTA[f]
        info = dados["cargos"] + dados["divisoes"] + CARGOS_GERAIS
        cor = FAC_CORES[f]
        cargo_ids = {}

        await msg.edit(content=f"⏳ {f}: Criando cargos + {len(dados['divisoes'])} divisões...")
        # 1. CARGOS + DIVISOES COMO CARGOS
        for nome_cargo in info:
            cargo = await ctx.guild.create_role(name=nome_cargo, color=cor, hoist=True if "Comandante" in nome_cargo or "Chefe" in nome_cargo or "Diretor" in nome_cargo or "Divisão" in nome_cargo else False)
            cargo_ids[nome_cargo] = cargo.id
            await asyncio.sleep(0.6)

        comando = ctx.guild.get_role(cargo_ids[dados["cargos"][17]])
        civil = ctx.guild.get_role(cargo_ids["Civil"])
        overwrites_staff = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), comando: discord.PermissionOverwrite(view_channel=True, manage_messages=True)}
        overwrites_publico = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), civil: discord.PermissionOverwrite(view_channel=True, send_messages=True)}

        # 2. CATEGORIAS + CATEGORIA PRA CADA DIVISÃO
        categorias_reais = {
            f"📋 ADMINISTRAÇÃO {f}": ["📢│avisos", "💬│chat-oficiais", "📊│relatorios", "📝│formulario-entrada", "📝│formulario-promocao", "📋│recrutamento", "📋│entrevistas"],
            f"🚨 OPERAÇÕES {f}": ["🚨│ocorrencias", "📍│patrulhamento", "🕵️│inteligencia", "⚖️│corregedoria"],
            f"🚔 LOGÍSTICA {f}": ["🚔│viaturas", "📦│armamento", "🔧│oficina", "💰│tesouraria"],
            f"📚 TREINAMENTO {f}": ["📚│academia", "🎯│estande-tiro", "🏆│hall-fama"],
            f"📞 COMUNICAÇÃO {f}": ["🔊│radio-central", "🚨│call-urgencia", "🎙️│sala-reuniao"]
        }

        # ADICIONA CATEGORIA PRA CADA DIVISÃO
        for div in dados["divisoes"]:
            categorias_reais[f"{div} {f}"] = [
                f"💬│chat-{div.lower().replace(' ', '-')}",
                f"📋│ocorrencias-{div.lower().replace(' ', '-')}",
                f"🔊│radio-{div.lower().replace(' ', '-')}"
            ]

        await msg.edit(content=f"⏳ {f}: Criando {len(categorias_reais)} Categorias + 60+ Canais...")
        for nome_cat, canais in categorias_reais.items():
            categoria = await ctx.guild.create_category(nome_cat, overwrites=overwrites_staff)
            await asyncio.sleep(0.5)

            for nome_canal in canais:
                if "radio" in nome_canal or "call" in nome_canal or "reuniao" in nome_canal or "tiro" in nome_canal:
                    await ctx.guild.create_voice_channel(nome_canal, category=categoria, overwrites=overwrites_staff)
                elif "recrutamento" in nome_canal or "entrevistas" in nome_canal:
                    await ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=overwrites_publico)
                else:
                    await ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=overwrites_staff)
                await asyncio.sleep(0.4)

        db["corps"][f] = cargo_ids

    save()
    await msg.edit(content=f"✅ **SETUP MINI CITY COM DIVISÕES FINALIZADO**\nCorps: PM, PC, PRF, SAMU\n50+ Cargos + 60+ Canais + 10 Categorias cada")

@bot.command()
@is_dono()
async def limpar(ctx, fac=None):
    if fac is None:
        return await ctx.send("❌ Use: `!limpar PM` ou `!limpar ALL`")
    msg = await ctx.send(f"⏳ Apagando...")
    if fac.upper() == "ALL":
        for channel in ctx.guild.channels:
            try: await channel.delete(); await asyncio.sleep(0.2)
            except: pass
        for category in ctx.guild.categories:
            try: await category.delete(); await asyncio.sleep(0.2)
            except: pass
        for role in ctx.guild.roles:
            if role.name!= "@everyone" and role.managed == False and role!= ctx.guild.me.top_role:
                try: await role.delete(); await asyncio.sleep(0.3)
                except: pass
        db["corps"] = {}
    else:
        fac = fac.upper()
        for channel in ctx.guild.channels:
            if fac.lower() in channel.name.lower():
                try: await channel.delete(); await asyncio.sleep(0.2)
                except: pass
        for category in ctx.guild.categories:
            if fac in category.name:
                try: await category.delete(); await asyncio.sleep(0.2)
                except: pass
        if fac in db["corps"]:
            for cargo_id in db["corps"][fac].values():
                cargo = ctx.guild.get_role(cargo_id)
                if cargo:
                    try: await cargo.delete(); await asyncio.sleep(0.3)
                    except: pass
            del db["corps"][fac]
    save()
    await msg.edit(content=f"✅ **LIMPEZA CONCLUÍDA**")

bot.run(os.getenv("TOKEN"))
