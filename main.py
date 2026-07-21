import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import os, json, asyncio, datetime
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
STAFF_ROLE_ID = 1528409545439969433
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"tickets":{}, "servidores_permitidos": [], "logs": None, "logs_game": None}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

async def enviar_log(guild, tipo, embed):
    canal_id = db["logs_game"] if tipo == "game" else db["logs"]
    if canal_id:
        canal = guild.get_channel(canal_id)
        if canal: await canal.send(embed=embed)

# ============ ANTI ROUBO ============
@bot.event
async def on_guild_join(guild):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
        inviter = entry.user
    if not inviter or inviter.id!= DONO_ID:
        await guild.leave()
        dono = await bot.fetch_user(DONO_ID)
        await dono.send(f"🚨 **ANTI ROUBO**\nTentaram add no: **{guild.name}**")

@bot.command()
@is_dono()
async def liberar(ctx):
    if ctx.guild.id not in db["servidores_permitidos"]:
        db["servidores_permitidos"].append(ctx.guild.id)
        save()
        await ctx.send(f"✅ Servidor **{ctx.guild.name}** liberado")

@bot.check
async def check_servidor(ctx):
    if ctx.guild.id not in db["servidores_permitidos"] and ctx.author.id!= DONO_ID:
        return False
    return True

# ============ LOGS ============
@bot.command()
@is_dono()
async def logs(ctx):
    categoria = discord.utils.get(ctx.guild.categories, name="📝 LOGS")
    if not categoria: categoria = await ctx.guild.create_category("📝 LOGS")
    canal = discord.utils.get(categoria.channels, name="logs-geral")
    if not canal: canal = await ctx.guild.create_text_channel("logs-geral", category=categoria)
    db["logs"] = canal.id
    save()
    await ctx.send(f"✅ Canal de logs criado: {canal.mention}")

@bot.command()
@is_dono()
async def logsgame(ctx):
    categoria = discord.utils.get(ctx.guild.categories, name="📝 LOGS")
    if not categoria: categoria = await ctx.guild.create_category("📝 LOGS")
    canal = discord.utils.get(categoria.channels, name="logs-game")
    if not canal: canal = await ctx.guild.create_text_channel("logs-game", category=categoria)
    db["logs_game"] = canal.id
    save()
    await ctx.send(f"✅ Canal de logs game criado: {canal.mention}")

@bot.event
async def on_message_delete(message):
    if not message.author.bot and db["logs"]:
        embed = discord.Embed(title="🗑️ Mensagem Apagada", description=f"**Autor:** {message.author.mention}\n**Canal:** {message.channel.mention}\n**Conteúdo:** {message.content}", color=0xFF0000, timestamp=datetime.datetime.now())
        await enviar_log(message.guild, "geral", embed)

# ============ MODAIS ============
class ModalWL(Modal, title="Whitelist - 15 Perguntas RP"):
    def __init__(self):
        super().__init__()
        for i in range(1, 16):
            self.add_item(TextInput(label=f"{i}. Pergunta RP {i}", style=discord.TextStyle.paragraph, required=True))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ WL enviada! Aguarde um staff.", ephemeral=True)
        guild = interaction.guild
        categoria = discord.utils.get(guild.categories, name="🎫 WHITELIST")
        if not categoria: categoria = await guild.create_category("🎫 WHITELIST")
        staff_role = discord.utils.get(guild.roles, id=STAFF_ROLE_ID)
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True), staff_role: discord.PermissionOverwrite(view_channel=True)}
        canal = await guild.create_text_channel(f"wl-{interaction.user.name}", category=categoria, overwrites=overwrites)
        db["tickets"][f"wl-{interaction.user.id}"] = {"canal": canal.id, "staff": None, "tipo": "WL"}
        save()
        respostas = "\n".join([f"**{i.label}**\n{i.value}" for i in self.children])
        embed = discord.Embed(title=f"📋 WL de {interaction.user}", description=respostas, color=0x5865F2)
        await canal.send(embed=embed, view=BotoesWL(interaction.user.id))

# ============ PAINEIS E BOTOES ============
class PainelPrincipal(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Suporte", style=discord.ButtonStyle.blurple, emoji="🎫", custom_id="ticket_suporte")
    async def suporte(self, interaction, button): await abrir_ticket(interaction, "Suporte")
    @discord.ui.button(label="Denuncia", style=discord.ButtonStyle.red, emoji="🚨", custom_id="ticket_denuncia")
    async def denuncia(self, interaction, button): await abrir_ticket(interaction, "Denuncia")

class PainelVIP(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="VIP Bronze", style=discord.ButtonStyle.secondary, emoji="🥉")
    async def bronze(self, interaction, button): await abrir_ticket(interaction, "VIP Bronze")
    @discord.ui.button(label="VIP Prata", style=discord.ButtonStyle.gray, emoji="🥈")
    async def prata(self, interaction, button): await abrir_ticket(interaction, "VIP Prata")
    @discord.ui.button(label="VIP Ouro", style=discord.ButtonStyle.green, emoji="🥇")
    async def ouro(self, interaction, button): await abrir_ticket(interaction, "VIP Ouro")

class PainelWL(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Fazer WL", style=discord.ButtonStyle.green, emoji="📋")
    async def fazerwl(self, interaction, button):
        if f"wl-{interaction.user.id}" in db["tickets"]:
            return await interaction.response.send_message("❌ Você já tem uma WL aberta!", ephemeral=True)
        await interaction.response.send_modal(ModalWL())

class BotoesTicket(View):
    def __init__(self, dono_id):
        super().__init__(timeout=None)
        self.dono_id = dono_id
    @discord.ui.button(label="Assumir", style=discord.ButtonStyle.green, emoji="✅")
    async def assumir(self, interaction, button): await assumir_ticket(interaction, self.dono_id, "normal")
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, interaction, button): await fechar_ticket(interaction, self.dono_id)

class BotoesWL(View):
    def __init__(self, dono_id):
        super().__init__(timeout=None)
        self.dono_id = dono_id
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green, emoji="✅")
    async def aprovar(self, interaction, button): await aprovar_wl(interaction, self.dono_id, True)
    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.red, emoji="❌")
    async def reprovar(self, interaction, button): await aprovar_wl(interaction, self.dono_id, False)

# ============ FUNCOES TICKET ============
async def abrir_ticket(interaction, tipo):
    if str(interaction.user.id) in db["tickets"] or f"{tipo.lower()}-{interaction.user.id}" in db["tickets"]:
        return await interaction.response.send_message("❌ Você já tem um ticket aberto!", ephemeral=True)
    categoria = discord.utils.get(interaction.guild.categories, name="🎫 TICKETS")
    if not categoria: categoria = await interaction.guild.create_category("🎫 TICKETS")
    staff_role = discord.utils.get(interaction.guild.roles, id=STAFF_ROLE_ID)
    overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
    canal = await interaction.guild.create_text_channel(f"{tipo.lower()}-{interaction.user.name}", category=categoria, overwrites=overwrites)
    db["tickets"][str(interaction.user.id)] = {"canal": canal.id, "staff": None, "tipo": tipo}
    save()
    embed = discord.Embed(title=f"🎫 Ticket {tipo}", description=f"Olá {interaction.user.mention}\nAguarde um staff assumir.", color=0x5865F2)
    await canal.send(embed=embed, view=BotoesTicket(interaction.user.id))
    await interaction.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

async def assumir_ticket(interaction, dono_id, tipo):
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("❌ Só staff pode assumir", ephemeral=True)
    key = str(dono_id) if tipo == "normal" else f"wl-{dono_id}"
    ticket = db["tickets"].get(key)
    if not ticket or ticket["staff"]: return await interaction.response.send_message("❌ Já foi assumido", ephemeral=True)
    ticket["staff"] = interaction.user.id
    save()
    canal = interaction.guild.get_channel(ticket["canal"])
    await canal.set_permissions(interaction.guild.default_role, send_messages=False)
    await canal.set_permissions(interaction.user, send_messages=True)
    await canal.set_permissions(interaction.guild.get_member(dono_id), send_messages=True)
    await canal.send(f"✅ **Assumido por {interaction.user.mention}**\n🔒 Canal trancado. Só você e {interaction.guild.get_member(dono_id).mention} podem falar.")
    await interaction.response.send_message("✅ Assumido!", ephemeral=True)

async def aprovar_wl(interaction, dono_id, aprovado):
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("❌ Só staff", ephemeral=True)
    membro = interaction.guild.get_member(dono_id)
    canal = interaction.channel
    if aprovado:
        await membro.send(f"✅ **WL APROVADA**\nParabéns! Você foi aprovado na WL.")
        await canal.send(f"✅ **APROVADO por {interaction.user.mention}**")
    else:
        await membro.send(f"❌ **WL REPROVADA**\nMotivo: Aguarde contato de um staff.")
        await canal.send(f"❌ **REPROVADO por {interaction.user.mention}**")
    await asyncio.sleep(5)
    await canal.delete()
    if f"wl-{dono_id}" in db["tickets"]: del db["tickets"][f"wl-{dono_id}"]
    save()

async def fechar_ticket(interaction, dono_id):
    key = str(dono_id)
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles] and interaction.user.id!= dono_id:
        return await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
    if key in db["tickets"]: del db["tickets"][key]
    save()
    await interaction.response.send_message("🔒 Fechando em 5s...")
    await asyncio.sleep(5)
    await interaction.channel.delete()

# ============ COMANDOS ============
@bot.command()
@is_dono()
async def painel(ctx):
    await ctx.send(embed=discord.Embed(title="🏠 Painel Principal", description="Suporte e Denuncia", color=0x5865F2), view=PainelPrincipal())
    await ctx.message.delete()

@bot.command()
@is_dono()
async def painelloja(ctx):
    await ctx.send(embed=discord.Embed(title="💎 Painel Loja VIP", description="Escolha seu VIP", color=0xFFD700), view=PainelVIP())
    await ctx.message.delete()

@bot.command()
@is_dono()
async def painelwl(ctx):
    await ctx.send(embed=discord.Embed(title="📋 Painel WL", description="Clique para fazer sua Whitelist", color=0x5865F2), view=PainelWL())
    await ctx.message.delete()

@bot.event
async def on_ready():
    bot.add_view(PainelPrincipal())
    bot.add_view(PainelVIP())
    bot.add_view(PainelWL())
    print('✅ BOT V12 ONLINE')

bot.run(os.getenv("TOKEN"))
