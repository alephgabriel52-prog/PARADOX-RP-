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
except: db = {"corps":{}, "tickets":{}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

@bot.command()
@is_dono()
async def setup(ctx, fac=None):
    FAC_LISTA = {
        "PM": {"cargos": ["Civil","Recruta PM","Soldado PM","Cabo PM","3º Sgt PM","2º Sgt PM","1º Sgt PM","Sub Ten PM","Asp Oficial PM","2º Ten PM","1º Ten PM","Cap PM","Major PM","Ten Cel PM","Cel PM","Corregedor PM","Sub Comandante Geral PM","Comandante Geral PM"],"divisoes": ["🚔 1º BATALHÃO", "⚡ ROTA", "🛡️ BOP"],"promocao": ["📈 Promoção PM"]},
        "PC": {"cargos": ["Civil","Estagiário PC","Agente PC","Agente Especial PC","Escrivão PC","Investigador PC","Delegado PC","Delegado Titular PC","Corregedor PC","Delegado Geral PC","Chefe de Polícia"],"divisoes": ["🔍 DHPP", "💰 DEIC", "🕵️ DEAM"],"promocao": ["📈 Promoção PC"]},
        "PRF": {"cargos": ["Civil","PRF Aluno","PRF 3ª Classe","PRF 2ª Classe","PRF 1ª Classe","PRF Classe Especial","Inspetor PRF","Chefe de Núcleo PRF","Chefe Regional PRF","Superintendente PRF"],"divisoes": ["🛣️ Patrulhamento", "📦 Fiscalização"],"promocao": ["📈 Promoção PRF"]},
        "SAMU": {"cargos": ["Civil","Estagiário SAMU","Condutor Socorrista","Téc Enfermagem SAMU","Enfermeiro SAMU","Médico Plantonista","Médico Regulador","Coordenador Regional SAMU","Diretor Médico SAMU"],"divisoes": ["🚑 USB Básica", "🚑 USA Avançada"],"promocao": ["📈 Promoção SAMU"]},
        "TRIBUNAL": {"cargos": ["Civil","Estagiário Jurídico","Assessor Jurídico","Advogado TC","Promotor TC","Juiz TC","Desembargador TC","Ministro TC","Presidente do Tribunal"],"divisoes": ["⚖️ Vara Criminal", "⚖️ Vara Civil"],"promocao": ["📈 Promoção Tribunal"]},
        "CORREGEDORIA": {"cargos": ["Civil","Corregedor Estagiário","Corregedor Adjunto","Corregedor Geral","Ouvidor Geral","Procurador Corregedoria"],"divisoes": ["📁 Processos PM", "📁 Processos PC"],"promocao": ["📈 Promoção Corregedoria"]}
    }

    CARGOS_GERAIS = ["🏅 Medalha Mérito","📊 Estatística","📞 Atendente Ticket"]
    FAC_CORES = {"PM": discord.Color.blue(), "PC": discord.Color.dark_red(), "PRF": discord.Color.dark_green(), "SAMU": discord.Color.red(), "TRIBUNAL": discord.Color.gold(), "CORREGEDORIA": discord.Color.dark_purple()}

    facs_para_criar = FAC_LISTA.keys() if fac is None or fac.upper() == "ALL" else [fac.upper()]
    msg = await ctx.send(f"⏳ SETUP COM TICKET INTELIGENTE...")

    civil_cat = await ctx.guild.create_category("🏙️ ÁREA CIVIL")
    await ctx.guild.create_text_channel("💬│chat-civil", category=civil_cat)
    await ctx.guild.create_text_channel("📋│recrutamento-geral", category=civil_cat)
    await asyncio.sleep(0.5)

    for f in facs_para_criar:
        dados = FAC_LISTA[f]
        info = dados["cargos"] + dados["divisoes"] + dados["promocao"] + CARGOS_GERAIS
        cor = FAC_CORES[f]
        cargo_ids = {}

        await msg.edit(content=f"⏳ {f}: Criando cargos...")
        for nome_cargo in info:
            cargo = await ctx.guild.create_role(name=nome_cargo, color=cor)
            cargo_ids[nome_cargo] = cargo.id
            await asyncio.sleep(0.3)

        comando = ctx.guild.get_role(cargo_ids[dados["cargos"][-1]])
        oficial = ctx.guild.get_role(cargo_ids[dados["cargos"][9]])
        civil = ctx.guild.get_role(cargo_ids["Civil"])
        atendente = ctx.guild.get_role(cargo_ids["📞 Atendente Ticket"])

        perm_ver = discord.PermissionOverwrite(view_channel=True, send_messages=False)
        perm_atender = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)

        categorias_reais = {
            f"📞 ATENDIMENTO {f}": {
                "canais": ["📞│ouvidoria", "🎫│abrir-ticket", "📋│faq"],
                "perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), civil: discord.PermissionOverwrite(view_channel=True, send_messages=True), atendente: perm_atender, oficial: perm_atender}
            }
        }

        for nome_cat, data in categorias_reais.items():
            categoria = await ctx.guild.create_category(nome_cat, overwrites=data["perm"])
            await asyncio.sleep(0.3)
            for nome_canal in data["canais"]:
                canal = await ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=data["perm"])
                if "abrir-ticket" in nome_canal:
                    embed = discord.Embed(title=f"🎫 SISTEMA DE TICKET {f}", description="Reaja com 🎫 para abrir seu atendimento\n**Regras:**\n1 ticket por pessoa\nAo ser assumido o ticket é bloqueado", color=cor)
                    msg_ticket = await canal.send(embed=embed)
                    await msg_ticket.add_reaction("🎫")
                await asyncio.sleep(0.3)

        db["corps"][f] = {"cargos": cargo_ids, "categoria": categoria.id}

    save()
    await msg.edit(content=f"✅ **SETUP FINALIZADO**\nSistema de ticket com lock ativo")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if "🎫│abrir-ticket" in channel.name and str(payload.emoji) == "🎫":
        user = guild.get_member(payload.user_id)
        fac = channel.category.name.split()[2]

        # 1. VERIFICA SE JÁ TEM TICKET ABERTO
        if str(user.id) in db.get("tickets", {}):
            await user.send(f"❌ Você já tem um ticket aberto na {fac}")
            await message.remove_reaction("🎫", user)
            return

        # 2. CRIA O TICKET
        atendente = discord.utils.get(guild.roles, name="📞 Atendente Ticket")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            atendente: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        ticket = await guild.create_text_channel(f"🎫│{user.name}", category=channel.category, overwrites=overwrites)

        db["tickets"][str(user.id)] = ticket.id
        save()

        embed = discord.Embed(title=f"Ticket {user.name}", description="Aguarde um atendente...\n\nUm policial com cargo `📞 Atendente Ticket` pode assumir com `!assumir`", color=0x00ff00)
        await ticket.send(f"{atendente.mention}", embed=embed)
        await message.remove_reaction("🎫", user)

@bot.command()
async def assumir(ctx):
    if not any(r.name == "📞 Atendente Ticket" for r in ctx.author.roles):
        return await ctx.send("❌ Você não tem permissão")

    if "🎫│" not in ctx.channel.name:
        return await ctx.send("❌ Use este comando dentro de um ticket")

    # 3. LOCK: REMOVE PERMISSÃO DE TODOS MENOS QUEM ASSUMIU
    atendente = discord.utils.get(ctx.guild.roles, name="📞 Atendente Ticket")
    await ctx.channel.set_permissions(atendente, view_channel=True, send_messages=False)
    await ctx.channel.set_permissions(ctx.author, view_channel=True, send_messages=True, manage_channels=True)

    # Deixa todo mundo só ver
    for role in ctx.guild.roles:
        if role!= ctx.author and role!= ctx.guild.default_role:
            await ctx.channel.set_permissions(role, view_channel=True, send_messages=False)

    embed = discord.Embed(title="🔒 TICKET ASSUMIDO", description=f"Assumido por {ctx.author.mention}\nAgora apenas ele pode responder. Outros só podem ver.", color=0xff0000)
    await ctx.send(embed=embed)

@bot.command()
async def fechar(ctx):
    if "🎫│" not in ctx.channel.name:
        return await ctx.send("❌ Use dentro de um ticket")

    for user_id, ticket_id in db["tickets"].items():
        if ticket_id == ctx.channel.id:
            del db["tickets"][user_id]
            break
    save()
    await ctx.send("⏳ Fechando ticket em 5s...")
    await asyncio.sleep(5)
    await ctx.channel.delete()

@bot.command()
@is_dono()
async def limpar(ctx, fac=None):
    msg = await ctx.send(f"⏳ APAGANDO COM DELAY DE 3s...")
    for channel in ctx.guild.channels:
        try: await channel.delete(); await asyncio.sleep(3)
        except: pass
    for category in ctx.guild.categories:
        try: await category.delete(); await asyncio.sleep(3)
        except: pass
    for role in ctx.guild.roles:
        if role.name!= "@everyone" and not role.managed and role!= ctx.guild.me.top_role:
            try: await role.delete(); await asyncio.sleep(3)
            except: pass
    db["corps"] = {}; db["tickets"] = {}
    save()
    await msg.edit(content=f"✅ **SERVIDOR LIMPO**")

bot.run(os.getenv("TOKEN"))
