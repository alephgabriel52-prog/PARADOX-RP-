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
    # HIERARQUIA COMPLETA + PROMOÇÃO
    FAC_LISTA = {
        "PM": {
            "cargos": ["Civil","Recruta PM","Soldado PM","Cabo PM","3º Sgt PM","2º Sgt PM","1º Sgt PM","Sub Ten PM","Asp Oficial PM","2º Ten PM","1º Ten PM","Cap PM","Major PM","Ten Cel PM","Cel PM","Corregedor PM","Sub Comandante PM","Comandante Geral PM"],
            "divisoes": ["🚔 BATALHÃO", "⚡ ROTA", "🛡️ BOP", "🚨 CHOQUE", "🚁 AEROPOL"],
            "promocao": ["📈 Promoção PM"]
        },
        "PC": {
            "cargos": ["Civil","Estagiário PC","Agente PC","Agente Especial PC","Escrivão PC","Investigador PC","Delegado PC","Delegado Titular PC","Corregedor PC","Delegado Geral PC","Chefe de Polícia"],
            "divisoes": ["🔍 DHPP", "💰 DEIC", "🕵️ DEAM", "💊 DENARC", "🚔 DP Geral"],
            "promocao": ["📈 Promoção PC"]
        },
        "PRF": {
            "cargos": ["Civil","PRF Aluno","PRF 3ª Classe","PRF 2ª Classe","PRF 1ª Classe","PRF Classe Especial","Inspetor PRF","Chefe de Núcleo PRF","Chefe Regional PRF","Superintendente PRF"],
            "divisoes": ["🛣️ Patrulhamento", "📦 Fiscalização", "🚨 Operações", "📊 Educação", "🆘 Resgate"],
            "promocao": ["📈 Promoção PRF"]
        },
        "SAMU": {
            "cargos": ["Civil","Estagiário SAMU","Condutor Socorrista","Téc Enfermagem SAMU","Enfermeiro SAMU","Médico Plantonista","Médico Regulador","Coordenador Regional SAMU","Diretor Médico SAMU"],
            "divisoes": ["🚑 USB Básica", "🚑 USA Avançada", "🏥 Regulação Médica", "📞 Call Center", "🔧 Frota"],
            "promocao": ["📈 Promoção SAMU"]
        }
    }

    CARGOS_GERAIS = ["🏅 Medalha Mérito","🏅 Medalha Bravura","🏅 Medalha 5 Anos","🏅 Medalha 10 Anos","📊 Estatística","👑 Alto Comando","🔧 Logística","💰 Finanças","⚖️ Jurídico"]
    FAC_CORES = {"PM": discord.Color.blue(), "PC": discord.Color.dark_red(), "PRF": discord.Color.dark_green(), "SAMU": discord.Color.red()}

    facs_para_criar = FAC_LISTA.keys() if fac is None or fac.upper() == "ALL" else [fac.upper()]
    if fac and fac.upper() not in FAC_LISTA:
        return await ctx.send("❌ Use: `!setup PM` `!setup PC` `!setup PRF` `!setup SAMU` ou `!setup ALL`")

    msg = await ctx.send(f"⏳ TURBO MAX INICIADO...")

    # CANTINHO CIVIL GLOBAL
    await msg.edit(content="⏳ Criando Cantinho Civil...")
    civil_cat = await ctx.guild.create_category("🏙️ ÁREA CIVIL")
    await ctx.guild.create_text_channel("📋│recrutamento-geral", category=civil_cat)
    await ctx.guild.create_text_channel("❓│duvidas", category=civil_cat)
    await asyncio.sleep(0.1)

    for f in facs_para_criar:
        dados = FAC_LISTA[f]
        info = dados["cargos"] + dados["divisoes"] + dados["promocao"] + CARGOS_GERAIS
        cor = FAC_CORES[f]
        cargo_ids = {}

        await msg.edit(content=f"⏳ {f}: Criando 60 cargos TURBO...")
        # TURBO MAX: Cria tudo de uma vez
        tasks = [ctx.guild.create_role(name=n, color=cor, hoist="Comandante" in n or "Chefe" in n or "Diretor" in n) for n in info]
        cargos = await asyncio.gather(*tasks)
        for i, cargo in enumerate(cargos):
            cargo_ids[info[i]] = cargo.id

        # PERMISSÕES POR HIERARQUIA
        comando = ctx.guild.get_role(cargo_ids[dados["cargos"][-1]]) # Comandante
        oficial = ctx.guild.get_role(cargo_ids[dados["cargos"][9]]) # Tenente
        praça = ctx.guild.get_role(cargo_ids[dados["cargos"][3]]) # Cabo
        civil = ctx.guild.get_role(cargo_ids["Civil"])
        promocao = ctx.guild.get_role(cargo_ids[dados["promocao"][0]])

        overwrites_comando = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), comando: discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_roles=True, move_members=True)}
        overwrites_oficial = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), oficial: discord.PermissionOverwrite(view_channel=True, manage_messages=True)}
        overwrites_praça = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), praça: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        overwrites_civil = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), civil: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        overwrites_promocao = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), promocao: discord.PermissionOverwrite(view_channel=True, send_messages=True)}

        categorias_reais = {
            f"📋 ADMINISTRAÇÃO {f}": {"canais": ["📢│avisos", "💬│chat-oficiais", "📊│relatorios", "📝│formulario-entrada", "📝│formulario-promocao"], "perm": overwrites_oficial},
            f"🚨 OPERAÇÕES {f}": {"canais": ["🚨│ocorrencias", "📍│patrulhamento", "🕵️│inteligencia"], "perm": overwrites_praça},
            f"🚔 LOGÍSTICA {f}": {"canais": ["🚔│viaturas", "📦│armamento", "🔧│oficina"], "perm": overwrites_praça},
            f"📚 TREINAMENTO {f}": {"canais": ["📚│academia", "🎯│estande-tiro", "🏆│hall-fama"], "perm": overwrites_praça},
            f"📞 COMUNICAÇÃO {f}": {"canais": ["🔊│radio-central", "🚨│call-urgencia"], "perm": overwrites_praça},
            f"📈 PROMOÇÃO {f}": {"canais": ["📈│requerimento-promocao", "📈│analise-comando"], "perm": overwrites_promocao}
        }

        for div in dados["divisoes"]:
            categorias_reais[f"{div} {f}"] = {"canais": [f"💬│chat-{div.split()[1].lower()}", f"📋│ocorrencias-{div.split()[1].lower()}"], "perm": overwrites_praça}

        await msg.edit(content=f"⏳ {f}: Criando 11 categorias TURBO...")
        # TURBO MAX: Cria categorias e canais em lote
        for nome_cat, data in categorias_reais.items():
            categoria = await ctx.guild.create_category(nome_cat, overwrites=data["perm"])
            tasks = []
            for nome_canal in data["canais"]:
                if "radio" in nome_canal or "call" in nome_canal:
                    tasks.append(ctx.guild.create_voice_channel(nome_canal, category=categoria, overwrites=data["perm"]))
                elif "recrutamento" in nome_canal:
                    tasks.append(ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=overwrites_civil))
                else:
                    tasks.append(ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=data["perm"]))
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.1)

        db["corps"][f] = cargo_ids

    save()
    await msg.edit(content=f"✅ **SETUP TURBO MAX FINALIZADO**\n60+ Cargos | 70+ Canais | 11 Cats | Permissões configuradas | Cantinho Civil")

@bot.command()
@is_dono()
async def limpar(ctx, fac=None):
    if fac is None:
        return await ctx.send("❌ Use: `!limpar PM` ou `!limpar ALL`")
    msg = await ctx.send(f"⏳ APAGANDO TURBO MAX...")

    # LIMPAR ALL APAGA TUDO MESMO
    tasks = []
    for channel in ctx.guild.channels: tasks.append(channel.delete())
    await asyncio.gather(*tasks)

    tasks = []
    for category in ctx.guild.categories: tasks.append(category.delete())
    await asyncio.gather(*tasks)

    tasks = []
    for role in ctx.guild.roles:
        if role.name!= "@everyone" and not role.managed and role!= ctx.guild.me.top_role:
            tasks.append(role.delete())
    await asyncio.gather(*tasks)

    db["corps"] = {}
    save()
    await msg.edit(content=f"✅ **SERVIDOR 100% LIMPO**\nCargos + Canais + Categorias apagados")

bot.run(os.getenv("TOKEN"))
