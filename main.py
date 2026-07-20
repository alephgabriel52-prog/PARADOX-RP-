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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

DONO_ID = 1438010935783460954
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"economia":{}, "warns":{}, "corps":{}, "hierarquia":{}, "tickets":{}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

def is_staff(guild, user):
    cargos_staff = ["👑 Alto Comando", "Admin", "Moderador", "Equipe Staff", "DEV"]
    return any(discord.utils.get(guild.roles, name=c) in user.roles for c in cargos_staff)

# TEMPLATES DE CARGOS POR ORG - CADA UM DIFERENTE
TEMPLATES = {
    "PM": ["Recruta", "Soldado 2ª Classe", "Soldado 1ª Classe", "Cabo", "3º Sargento", "2º Sargento", "1º Sargento", "Sub Tenente", "Aspirante", "2º Tenente", "1º Tenente", "Capitão", "Major", "Tenente Coronel", "Coronel", "Comandante Geral"],
    "PC": ["Estagiário", "Agente", "Agente Especial", "Escrivão", "Delegado Adjunto", "Delegado", "Delegado Geral"],
    "BOPE": ["Recruta BOPE", "Operador", "Operador Especial", "Sargento BOPE", "Tenente BOPE", "Capitão BOPE", "Comandante BOPE"],
    "PF": ["Estagiário PF", "Agente PF", "Escrivão PF", "Delegado PF", "Superintendente PF"],
    "SAMU": ["Estagiário SAMU", "Técnico de Enfermagem", "Enfermeiro", "Médico", "Diretor SAMU"],
    "CORREGEDORIA": ["Assistente", "Corregedor", "Corregedor Geral"],
    "FRANÇA": ["Soldado", "Cabo", "Sargento", "Tenente", "Capitão", "General"],
    "CV": ["Vapor", "Soldado CV", "Gerente", "Vaqueiro", "Dono"],
    "MÁFIA": ["Associado", "Soldado", "Caporegime", "Consigliere", "Don"],
    "TRIBUNAL": ["Estagiário Direito", "Advogado", "Promotor", "Juiz", "Desembargador", "Ministro"],
    "RP": ["Visitante", "Cidadão", "Empresário", "Mecânico", "Policial", "Médico", "Admin RP", "Dono RP"]
}

# DIVISÕES POR ORG - CADA UM DIFERENTE
DIVISOES = {
    "PM": ["ROTAM", "ROCAM", "CHOQUE", "TRÂNSITO"],
    "BOPE": ["GATE", "AERÉO", "CANIL"],
    "PC": ["HOMICÍDIOS", "DROGAS", "SEQUESTRO"],
    "PF": ["INTELIGÊNCIA", "FRONTEIRA"],
    "SAMU": ["UTI", "RESCATE"],
    "CORREGEDORIA": ["INVESTIGAÇÃO"],
    "FRANÇA": ["INFANTARIA", "ARTILHARIA"],
    "CV": ["GUERRA", "VENDAS"],
    "MÁFIA": ["TRÁFICO", "LAVAGEM"],
    "TRIBUNAL": ["CÍVEL", "CRIMINAL"],
    "RP": ["POLÍCIA", "HOSPITAL", "MECÂNICA", "PREFEITURA"]
}

def tem_permissao_promover(cargo_nome):
    return any(x in cargo_nome for x in ["Comandante", "Coronel", "Major", "Capitão", "Delegado", "Diretor", "General", "Dono", "Don", "Ministro", "Juiz", "Admin RP"])

def pegar_maior_cargo(membro, corp):
    for role in membro.roles:
        if corp in role.name: return role.name
    return "Civil"

# ============ SETUP 1 ORG POR VEZ ============
@bot.command()
@is_dono()
async def setup(ctx, corp: str = "PM"):
    corp = corp.upper()
    if corp not in TEMPLATES:
        return await ctx.send("❌ Orgs disponíveis: PM, PC, BOPE, PF, SAMU, CORREGEDORIA, FRANÇA, CV, MÁFIA, TRIBUNAL, RP")

    await ctx.send(f"⚡ **INICIANDO SETUP DA {corp}**... Aguarde 1 min")
    guild = ctx.guild
    everyone = guild.default_role

    # 1. CRIA CARGOS SÓ DA ORG ESCOLHIDA
    cargos_list = ["👑 Alto Comando", "DEV", "Equipe Staff", "Civil", "Staff", "Moderador", "Admin", "Mutado"]

    for patente in TEMPLATES: # CORRIGIDO
        cargos_list.append(f"{patente}")

    if corp in DIVISOES:
        for div in DIVISOES: # CORRIGIDO
            cargos_list.append(f"{div} {corp}")

    roles = {}
    for nome in cargos_list:
        role = discord.utils.get(guild.roles, name=nome)
        if not role:
            role = await guild.create_role(name=nome)
            await asyncio.sleep(0.1)
        roles[nome] = role

    await roles["👑 Alto Comando"].edit(permissions=discord.Permissions(administrator=True))
    await roles["Admin"].edit(permissions=discord.Permissions(administrator=True))
    await roles["DEV"].edit(permissions=discord.Permissions(manage_messages=True, manage_roles=True))
    await roles["Moderador"].edit(permissions=discord.Permissions(manage_messages=True, kick_members=True, ban_members=True))
    await roles["Equipe Staff"].edit(permissions=discord.Permissions(manage_messages=True))
    await roles["Mutado"].edit(permissions=discord.Permissions(send_messages=False, speak=False))

    # 2. OVERWRITES
    overw_ac = {everyone: discord.PermissionOverwrite(view_channel=False), roles["👑 Alto Comando"]: discord.PermissionOverwrite(view_channel=True)}
    primeiro_cargo = f"{TEMPLATES[0]}"
    overw_corp = {everyone: discord.PermissionOverwrite(view_channel=False), roles[primeiro_cargo]: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
    overw_civil = {everyone: discord.PermissionOverwrite(view_channel=True)}

    # 3. CRIA CANAIS SÓ DA ORG ESCOLHIDA
    if corp == "RP":
        if not discord.utils.get(guild.categories, name="🏙️ CIDADE RP"):
            cat_rp = await guild.create_category("🏙️ CIDADE RP", overwrites=overw_civil)
            await guild.create_text_channel("💬│geral-rp", category=cat_rp)
            await guild.create_text_channel("📢│anuncios", category=cat_rp)
            await guild.create_text_channel("🚗│vendas", category=cat_rp)
            await guild.create_voice_channel("🔊│Lobby", category=cat_rp)

        if not discord.utils.get(guild.categories, name="👮 ORGÃOS"):
            cat_org = await guild.create_category("👮 ORGÃOS", overwrites=overw_corp)
            await guild.create_text_channel("📋│boletim", category=cat_org)

    else:
        if not discord.utils.get(guild.categories, name=f"🚔 {corp}"):
            cat_corp = await guild.create_category(f"🚔 {corp}", overwrites=overw_corp)
            await guild.create_text_channel("📋│boletim-ocorrencias", category=cat_corp)
            await guild.create_text_channel("📄│fichas", category=cat_corp)
            await guild.create_text_channel("🎫│tickets", category=cat_corp)
            await guild.create_text_channel("💰│multas", category=cat_corp)
            await guild.create_voice_channel("📻│Radio Geral", category=cat_corp)

        if corp in DIVISOES:
            for div in DIVISOES:
                if not discord.utils.get(guild.categories, name=f"⚔️ {div} {corp}"):
                    overw_div = {everyone: discord.PermissionOverwrite(view_channel=False), roles[f"{div} {corp}"]: discord.PermissionOverwrite(view_channel=True)}
                    cat_div = await guild.create_category(f"⚔️ {div} {corp}", overwrites=overw_div)
                    await guild.create_text_channel(f"📋│{div.lower()}", category=cat_div)

    if not discord.utils.get(guild.categories, name="👑 ALTO COMANDO"):
        cat_ac = await guild.create_category("👑 ALTO COMANDO", overwrites=overw_ac)
        await guild.create_text_channel("🔒│ac-geral", category=cat_ac)
        await guild.create_text_channel("📈│promoções", category=cat_ac)

    if not discord.utils.get(guild.categories, name="👤 CIVIL"):
        cat_civil = await guild.create_category("👤 CIVIL", overwrites=overw_civil)
        await guild.create_text_channel("💬│geral", category=cat_civil)
        await guild.create_text_channel("🤖│comandos", category=cat_civil)

    db["corps"][str(guild.id)] = corp; save()
    await ctx.send(f"✅ **SETUP DA {corp} CONCLUÍDO!**\n✅ {len(cargos_list)} cargos\n✅ Canais e divisões da {corp} criadas")

# ============ PAINEIS ============
@bot.command(name='paineldono')
async def paineldono(ctx):
    if ctx.author.id!= DONO_ID:
        await ctx.send("❌ **Você não tem permissão.** Só o dono pode usar.")
        return
    embed = discord.Embed(title="👑 PAINEL DO DONO", description="Gerencie seu servidor RP", color=0xFF0000)
    embed.add_field(name="Dar Cargo Staff", value="`!setstaff @membro Equipe Staff`", inline=False)
    embed.add_field(name="Setup", value="`!setup pm` `!setup pc` `!setup bope`", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='painelstaff')
async def painelstaff(ctx):
    cargos_membro = [cargo.name for cargo in ctx.author.roles]
    if "Equipe Staff" not in cargos_membro:
        await ctx.send("❌ **Você não tem permissão.** Só quem tem `Equipe Staff` pode usar.")
        return
    embed = discord.Embed(title="📋 PAINEL EQUIPE STAFF", description="Comandos disponíveis", color=0x00FF00)
    embed.add_field(name="Promover", value="`!promover @membro Cargo`", inline=False)
    embed.add_field(name="Rebaixar", value="`!rebaixar @membro Cargo`", inline=False)
    embed.add_field(name="Exonerar", value="`!exonerar @membro`", inline=False)
    await ctx.send(embed=embed)

# ============ COMANDOS HIERARQUIA ============
@bot.command()
async def promover(ctx, membro: discord.Member, *, cargo_novo: str):
    corp = db["corps"].get(str(ctx.guild.id), "PM")
    cargo_autor = pegar_maior_cargo(ctx.author, corp)
    if not tem_permissao_promover(cargo_autor): return await ctx.send("❌ Só cargo alto pode promover")
    cargo_obj = discord.utils.get(ctx.guild.roles, name=cargo_novo)
    if not cargo_obj: return await ctx.send("❌ Cargo não existe")
    for c in membro.roles:
        if corp in c.name: await membro.remove_roles(c)
    await membro.add_roles(cargo_obj)
    await ctx.send(f"📈 {membro.mention} promovido para **{cargo_novo}**")

@bot.command()
async def rebaixar(ctx, membro: discord.Member, *, cargo_novo: str):
    corp = db["corps"].get(str(ctx.guild.id), "PM")
    cargo_autor = pegar_maior_cargo(ctx.author, corp)
    if not tem_permissao_promover(cargo_autor): return await ctx.send("❌ Só cargo alto pode rebaixar")
    cargo_obj = discord.utils.get(ctx.guild.roles, name=cargo_novo)
    for c in membro.roles:
        if corp in c.name: await membro.remove_roles(c)
    await membro.add_roles(cargo_obj)
    await ctx.send(f"📉 {membro.mention} rebaixado para **{cargo_novo}**")

@bot.command()
async def exonerar(ctx, membro: discord.Member):
    corp = db["corps"].get(str(ctx.guild.id), "PM")
    cargo_autor = pegar_maior_cargo(ctx.author, corp)
    if not tem_permissao_promover(cargo_autor): return await ctx.send("❌ Só cargo alto pode exonerar")
    for c in membro.roles:
        if corp in c.name: await membro.remove_roles(c)
    civil = discord.utils.get(ctx.guild.roles, name="Civil")
    await membro.add_roles(civil)
    await ctx.send(f"❌ {membro.mention} foi **EXONERADO** da {corp}")

@bot.command()
@is_dono()
async def setstaff(ctx, membro: discord.Member, *, cargo: str):
    cargo_obj = discord.utils.get(ctx.guild.roles, name=cargo)
    if not cargo_obj: return await ctx.send(f"❌ Cargo `{cargo}` não existe")
    await membro.add_roles(cargo_obj)
    await ctx.send(f"✅ {membro.mention} agora é **{cargo}**")

@bot.command()
async def ban(ctx, membro: discord.Member, *, motivo="Sem motivo"):
    if not is_staff(ctx.guild, ctx.author): return await ctx.send("❌ Sem permissão")
    await membro.ban(reason=motivo); await ctx.send(f"🔨 {membro.mention} banido")

@bot.event
async def on_ready():
    print(f'✅ MASTER BOT ONLINE - 11 TEMPLATES + PAINEIS')

bot.run(os.getenv("TOKEN"))
