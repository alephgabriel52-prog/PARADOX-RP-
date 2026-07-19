import discord
from discord.ext import commands
import os
import json
import asyncio
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online 24h"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
start_time = datetime.now()

# ===== CONFIG DE SEGURANÇA =====
DONO_ID = 1438010935783460954 # SEU ID
STAFF_ROLE_ID = 1528409545439969433
LOG_CHANNEL_ID = None

ARQUIVO_CONFIG = 'config.json'
ARQUIVO_WARNS = 'warns.json'
ARQUIVO_GOGO = 'gogo.json'
ARQUIVO_PONTO = 'ponto.json'
ARQUIVO_PROCESSOS = 'processos.json'

try:
    with open(ARQUIVO_CONFIG, 'r') as f: config = json.load(f)
except: config = {"log_channel": None, "civil_role": None, "corps": {}, "facs": {}, "correg": {}, "tribunal": {}}

for arq in [ARQUIVO_WARNS, ARQUIVO_GOGO, ARQUIVO_PONTO, ARQUIVO_PROCESSOS]:
    try:
        with open(arq, 'r', encoding='utf-8') as f:
            if arq == ARQUIVO_WARNS: warns = json.load(f)
            if arq == ARQUIVO_GOGO: lista_gogo = json.load(f)
            if arq == ARQUIVO_PONTO: ponto = json.load(f)
            if arq == ARQUIVO_PROCESSOS: processos = json.load(f)
    except:
        if arq == ARQUIVO_WARNS: warns = {}
        if arq == ARQUIVO_GOGO: lista_gogo = []
        if arq == ARQUIVO_PONTO: ponto = {}
        if arq == ARQUIVO_PROCESSOS: processos = {}

def salvar(arquivo, dados):
    with open(arquivo, 'w', encoding='utf-8') as f: json.dump(dados, f, ensure_ascii=False, indent=4)

def is_dono():
    async def predicate(ctx):
        if ctx.author.id == DONO_ID: return True
        try: await ctx.author.send("❌ Só o Biel pode usar esse comando!")
        except: pass
        return False
    return commands.check(predicate)

def is_staff():
    async def predicate(ctx):
        if ctx.author.id == DONO_ID: return True
        if ctx.author.guild_permissions.administrator: return True
        staff_role = ctx.guild.get_role(STAFF_ROLE_ID)
        if staff_role and staff_role in ctx.author.roles: return True
        try: await ctx.author.send("😡 Tá pensando que aqui é bagunça? Fale com o Biel pra te dar permissão cara safado")
        except: pass
        await ctx.message.delete()
        return False
    return commands.check(predicate)

# ===== ANTI-ROUBO CORRIGIDO =====
@bot.event
async def on_guild_join(guild):
    # VERIFICA SE VOCÊ TÁ NO SERVIDOR
    dono = guild.get_member(DONO_ID)

    if not dono:
        # VOCÊ NÃO TÁ LÁ = VAZA
        msg_saida = "🚨 **VOCÊ NÃO É O BIEL**\nSó entro em servidor que o Biel ID: 1438010935783460954 estiver.\nBot saindo em 3s..."

        for canal in guild.text_channels:
            try:
                if canal.permissions_for(guild.me).send_messages:
                    await canal.send(msg_saida)
                    break
            except: pass

        await asyncio.sleep(3)
        await guild.leave()
        print(f"SAÍ: {guild.name} - Biel não estava no servidor")
    else:
        print(f"Entrei em: {guild.name} - Biel está aqui ✅")

@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")
    # CHECA TODOS SERVIDORES AO INICIAR
    for guild in bot.guilds:
        dono = guild.get_member(DONO_ID)
        if not dono:
            print(f"SAINDO: {guild.name} - Biel não está aqui")
            await guild.leave()

async def log(ctx, acao, alvo, motivo):
    if LOG_CHANNEL_ID:
        canal = bot.get_channel(LOG_CHANNEL_ID)
        if canal:
            embed = discord.Embed(title="📋 LOG", color=0xff0000, timestamp=datetime.now())
            embed.add_field(name="Ação", value=acao); embed.add_field(name="Staff", value=ctx.author.mention)
            embed.add_field(name="Alvo", value=alvo.mention); embed.add_field(name="Motivo", value=motivo)
            await canal.send(embed=embed)

HIERARQUIAS_CORP = {"pm": ["Comandante Geral", "Coronel", "Tenente Coronel", "Major", "Capitão", "1º Tenente", "2º Tenente", "Sub Tenente", "1º Sargento", "2º Sargento", "3º Sargento", "Cabo", "Soldado 1ª Classe", "Soldado 2ª Classe", "Recruta"]}
HIERARQUIAS_FAC = {"cv": ["Dono", "Vapor", "Gerente Geral", "Gerente", "Vendedor", "Olheiro", "Membro", "Recruta"]}
HIERARQUIA_CORREG = ["Corregedor Geral", "Corregedor Chefe", "Corregedor", "Assessor Corregedoria", "Estagiário Correg"]
HIERARQUIA_TRIBUNAL = ["Juiz Supremo", "Desembargador", "Juiz", "Promotor", "Advogado", "Escrivão Tribunal"]

# ===== COMANDOS SÓ DONO =====
@bot.command()
@is_dono()
async def setup(ctx, tipo, *, nome):
    guild = ctx.guild; tipo = tipo.lower(); nome_key = nome.lower(); nome_display = nome.title()
    civil_role = discord.utils.get(guild.roles, name="Civil") or await guild.create_role(name="Civil", color=discord.Color(0x95A5A6))
    config["civil_role"] = civil_role.id; staff_role = guild.get_role(STAFF_ROLE_ID)
    if tipo == "corp": cargos = HIERARQUIAS_CORP.get(nome_key, HIERARQUIAS_CORP["pm"]); canais_texto = ["📢・avisos","📋・pontos","💬・chat","🚨・ocorrencias"]; canais_voz = ["🔊・Rádio"]; cor = 0x3498DB; emoji = "👮"; storage = config["corps"]
    elif tipo == "fac": cargos = HIERARQUIAS_FAC.get(nome_key, HIERARQUIAS_FAC["cv"]); canais_texto = ["📢・avisos","💰・caixa","💬・chat","📦・estoque"]; canais_voz = ["🔊・Sala"]; cor = 0xE74C3C; emoji = "💼"; storage = config["facs"]
    elif tipo == "corregedoria": cargos = HIERARQUIA_CORREG; canais_texto = ["📢・avisos","📋・processos","💬・chat"]; canais_voz = ["🔊・Interrogatório"]; cor = 0x34495E; emoji = "👮‍♂️"; storage = config["correg"]
    elif tipo == "tribunal": cargos = HIERARQUIA_TRIBUNAL; canais_texto = ["📢・avisos","⚖️・audiencias","💬・chat"]; canais_voz = ["🔊・Audiência"]; cor = 0x8E44AD; emoji = "⚖️"; storage = config["tribunal"]
    else: return await ctx.send("❌ Use: corp/fac/corregedoria/tribunal")
    if nome_key in storage: return await ctx.send("❌ Já existe!")
    msg = await ctx.send(f"⏳ Criando {tipo.upper()} **{nome_display}**...")
    cargos_criados = []
    for i, cargo_nome in enumerate(cargos):
        perms = discord.Permissions();
        if i <= 2: perms.manage_messages = True
        if i == 0: perms.administrator = True
        cargo = await guild.create_role(name=f"{emoji} {nome_display} | {cargo_nome}", color=discord.Color(cor), permissions=perms, position=50-i)
        cargos_criados.append(cargo); await asyncio.sleep(0.3)
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), staff_role: discord.PermissionOverwrite(read_messages=True), civil_role: discord.PermissionOverwrite(read_messages=False)}
    for cat in [config["corps"], config["facs"], config["correg"], config["tribunal"]]:
        for outra in cat.values():
            outro_cargo = guild.get_role(outra["cargo_id"])
            if outro_cargo: overwrites[outro_cargo] = discord.PermissionOverwrite(read_messages=False)
    for cargo in cargos_criados: overwrites[cargo] = discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True)
    categoria = await guild.create_category(f"{emoji} {nome_display}", overwrites=overwrites)
    for canal_nome in canais_texto: await guild.create_text_channel(canal_nome, category=categoria)
    for canal_nome in canais_voz: await guild.create_voice_channel(canal_nome, category=categoria)
    storage[nome_key] = {"cargo_id": cargos_criados[0].id, "categoria_id": categoria.id, "cargos": [c.id for c in cargos_criados]}; salvar(ARQUIVO_CONFIG, config)
    await msg.edit(content="", embed=discord.Embed(title="✅ SETUP CONCLUÍDO", description=f"{categoria.mention}", color=0x2ECC71))

# ===== COMANDOS STAFF =====
@bot.command()
@is_staff()
async def transferir(ctx, member: discord.Member, org_sair: str, org_entrar: str):
    await ctx.message.delete()
    org1 = config["corps"].get(org_sair.lower()) or config["facs"].get(org_sair.lower())
    org2 = config["corps"].get(org_entrar.lower()) or config["facs"].get(org_entrar.lower())
    if not org1 or not org2: return await ctx.send("❌ Uma das orgs não existe!")
    for cid in org1["cargos"]:
        cargo = ctx.guild.get_role(cid)
        if cargo and cargo in member.roles: await member.remove_roles(cargo)
    cargo_novo = ctx.guild.get_role(org2["cargos"][-1]); await member.add_roles(cargo_novo)
    await ctx.send(f"✅ {member.mention} transferido para {cargo_novo.mention}")
    await log(ctx, "Transferir", member, f"{org_sair} -> {org_entrar}")

@bot.command()
@is_staff()
async def advertencia(ctx, member: discord.Member, *, motivo):
    user_id = str(member.id)
    if "ads" not in warns: warns["ads"] = {}
    if user_id not in warns["ads"]: warns["ads"][user_id] = []
    warns["ads"][user_id].append({"motivo": motivo, "data": datetime.now().strftime("%d/%m/%Y")}); salvar(ARQUIVO_WARNS, warns)
    await ctx.message.delete(); await ctx.send(f"📄 {member.mention} recebeu **ADVERTÊNCIA** por: {motivo}")
    await log(ctx, "Advertência", member, motivo)

@bot.command()
@is_staff()
async def escala(ctx, data: str, *, quem: str):
    await ctx.message.delete()
    embed = discord.Embed(title=f"📅 ESCALA DO DIA {data}", description=quem, color=0x3498DB)
    embed.set_footer(text=f"Feito por: {ctx.author.name}"); await ctx.send("@here", embed=embed)

@bot.command()
@is_staff()
async def reuniao(ctx, tempo: int, *, assunto):
    await ctx.message.delete()
    msg = await ctx.send(f"📢 @everyone **REUNIÃO EM {tempo} MINUTOS**\n**Assunto:** {assunto}")
    await asyncio.sleep(tempo*60); await ctx.send(f"📢 @everyone **REUNIÃO COMEÇANDO AGORA**\n**Assunto:** {assunto}")

@bot.command()
@is_staff()
async def contratar(ctx, member: discord.Member, *, cargo: discord.Role):
    await ctx.message.delete()
    cargo_valido = any(cargo.id in org["cargos"] for orgs in [config["corps"], config["facs"], config["correg"], config["tribunal"]] for org in orgs.values())
    if not cargo_valido: return await ctx.send("❌ Esse cargo não é de org!")
    await member.add_roles(cargo); await ctx.send(embed=discord.Embed(title="✅ CONTRATAÇÃO", description=f"{member.mention} foi contratado(a) como {cargo.mention}", color=0x2ECC71))

# ===== COMANDOS GERAIS =====
@bot.command()
async def cmds(ctx):
    embed = discord.Embed(title="📜 LISTA DE COMANDOS", color=0x5865F2)
    embed.description = f"**Dono do Bot:** <@{DONO_ID}>"
    embed.add_field(name="👑 SÓ O DONO PODE", value="`!setup`", inline=False)
    embed.add_field(name="👮 STAFF PODE USAR", value="`!contratar` `!demitir` `!transferir` `!promover` `!rebaixar`\n`!warn` `!kick` `!ban` `!mutar` `!limpar`\n`!advertencia` `!escala` `!reuniao`", inline=False)
    embed.add_field(name="😄 TODOS PODEM", value="`!ping` `!avatar` `!infouser` `!cmds`", inline=False)
    embed.set_footer(text="Trava: Só fica no serv se o Biel estiver 😈")
    await ctx.author.send(embed=embed); await ctx.send("✅ Mandei a lista no seu PV!")

bot.run(os.getenv("TOKEN"))
