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

STAFF_ROLE_ID = 1528409545439969433
STAFF_MENTION = "<@&{}>".format(STAFF_ROLE_ID)
CATEGORIA_NORMAL = 1528445353022455951
CATEGORIA_LOJA = 1528506502791430144
CATEGORIA_WHITELIST = ID_WHITELIST # TROCA AQUI

ARQUIVO_WARNS = 'warns.json'
ARQUIVO_TICKETS = 'tickets.json'
try:
    with open(ARQUIVO_WARNS, 'r', encoding='utf-8') as f: warns = json.load(f)
except: warns = {}
try:
    with open(ARQUIVO_TICKETS, 'r', encoding='utf-8') as f: tickets_abertos = json.load(f)
except: tickets_abertos = {}
respostas_ticket = {}

def salvar_warns():
    with open(ARQUIVO_WARNS, 'w', encoding='utf-8') as f: json.dump(warns, f, ensure_ascii=False, indent=4)
def salvar_tickets():
    with open(ARQUIVO_TICKETS, 'w', encoding='utf-8') as f: json.dump(tickets_abertos, f, ensure_ascii=False, indent=4)

def is_staff():
    async def predicate(ctx):
        return any(role.id == STAFF_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)

PERGUNTAS = [
    "1. Qual seu nome completo e idade?",
    "2. Você já jogou RP antes? Em qual(is) cidade(s)?",
    "3. O que é RDM e VDM? Dê exemplos.",
    "4. O que é Metagaming? Como você evita?",
    "5. O que é Powergaming? Dê um exemplo.",
    "6. Você está sendo roubado. O que faz para não quebrar regras?",
    "7. Qual a diferença entre IC e OOC? Quando usar cada um?",
    "8. O que você faria se visse 2 players fazendo RDM?",
    "9. Conte a história do seu personagem. Nome, profissão e objetivo:",
    "10. Como você reage a uma abordagem policial? Cite 3 atitudes.",
    "11. O que é Fear RP e como aplicar na prática?",
    "12. Você pode usar informações do Discord no jogo? Explique.",
    "13. Qual seu horário disponível para jogar na Cidade?",
    "14. Você tem microfone? Sabe fazer RP de voz?",
    "15. Por que devemos te aceitar na Cidade? Seja sincero." ]

class TicketPainelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def get_ticket_owner(self, interaction):
        for uid, cid in tickets_abertos.items():
            if cid == interaction.channel.id:
                return interaction.guild.get_member(int(uid))
        return None
    @discord.ui.button(label="Assumir Ticket", style=discord.ButtonStyle.primary, emoji="👮", custom_id="assumir_ticket")
    async def assumir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == STAFF_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Só a equipe {} pode assumir tickets!".format(STAFF_MENTION), ephemeral=True)
        await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
        await interaction.response.send_message("{} **assumiu este ticket!**".format(interaction.user.mention))
    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="fechar_ticket")
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == STAFF_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Só a equipe {} pode fechar tickets!".format(STAFF_MENTION), ephemeral=True)
        member = await self.get_ticket_owner(interaction)
        await interaction.response.send_message("🔒 Fechando ticket em 3 segundos...")
        await asyncio.sleep(3)
        if member:
            user_id = str(member.id)
            if user_id in tickets_abertos:
                del tickets_abertos[user_id]
                salvar_tickets()
            if user_id in respostas_ticket: del respostas_ticket[user_id]
        await interaction.channel.delete()

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Suporte", custom_id="suporte", style=discord.ButtonStyle.primary)
    async def suporte(self, interaction, button): await criar_ticket(interaction, "suporte")
    @discord.ui.button(label="Denuncia", custom_id="denuncia", style=discord.ButtonStyle.danger)
    async def denuncia(self, interaction, button): await criar_ticket(interaction, "denuncia")
    @discord.ui.button(label="Loja VIP", custom_id="loja", style=discord.ButtonStyle.success)
    async def loja(self, interaction, button): await criar_ticket(interaction, "loja")

class LojaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="VIP Bronze", custom_id="vipbronze", style=discord.ButtonStyle.secondary)
    async def bronze(self, interaction, button): await criar_ticket_vip(interaction, "vip-bronze")
    @discord.ui.button(label="VIP Prata", custom_id="vipprata", style=discord.ButtonStyle.primary)
    async def prata(self, interaction, button): await criar_ticket_vip(interaction, "vip-prata")
    @discord.ui.button(label="VIP Ouro", custom_id="vipouro", style=discord.ButtonStyle.success)
    async def ouro(self, interaction, button): await criar_ticket_vip(interaction, "vip-ouro")

class WhitelistButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Fazer Whitelist", style=discord.ButtonStyle.green, emoji="✅", custom_id="btn_whitelist_001")
    async def whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await criar_ticket_whitelist(interaction)

class TicketCloseView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def get_ticket_owner(self, interaction):
        for uid, cid in tickets_abertos.items():
            if cid == interaction.channel.id:
                return interaction.guild.get_member(int(uid))
        return None
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green, emoji="✅", custom_id="btn_aprovar_001")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == STAFF_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Só quem tem {} pode aprovar!".format(STAFF_MENTION), ephemeral=True)
        member = await self.get_ticket_owner(interaction)
        if not member: return await interaction.response.send_message("❌ Não achei o dono do ticket.", ephemeral=True)
        await interaction.response.send_modal(MotivoModal(member, "aprovado"))
    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.red, emoji="❌", custom_id="btn_reprovar_001")
    async def reprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == STAFF_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Só quem tem {} pode reprovar!".format(STAFF_MENTION), ephemeral=True)
        member = await self.get_ticket_owner(interaction)
        if not member: return await interaction.response.send_message("❌ Não achei o dono do ticket.", ephemeral=True)
        await interaction.response.send_modal(MotivoModal(member, "reprovado"))

class MotivoModal(discord.ui.Modal):
    def __init__(self, member, tipo):
        super().__init__(title="Motivo {}".format(tipo))
        self.member, self.tipo = member, tipo
        self.motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, required=True, max_length=500)
        self.add_item(self.motivo)
    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(self.member.id)
        channel = interaction.channel
        category = channel.category
        if self.tipo == "aprovado":
            dm_embed = discord.Embed(title="✅ WHITELIST APROVADA - PARADOX RP", description="Olá {}, sua whitelist foi **APROVADA**!\n\n**Motivo:** {}\n\nBem-vindo ao servidor!".format(self.member.name, self.motivo.value), color=0x00ff00)
            role = discord.utils.get(interaction.guild.roles, name="Membro")
            if role: await self.member.add_roles(role)
            if user_id in respostas_ticket and len(respostas_ticket[user_id]) >= 15:
                nick = respostas_ticket[user_id][14]
                try: await self.member.edit(nick=nick[:32])
                except: pass
            await enviar_log("WHITELIST APROVADA", self.member, interaction.user, self.motivo.value, "logs-rp")
            await interaction.response.send_message("✅ {} aprovado!".format(self.member.mention), ephemeral=True)
        else:
            dm_embed = discord.Embed(title="❌ WHITELIST REPROVADA - PARADOX RP", description="Olá {}, sua whitelist foi **REPROVADA**.\n\n**Motivo:** {}".format(self.member.name, self.motivo.value), color=0xff0000)
            await enviar_log("WHITELIST REPROVADA", self.member, interaction.user, self.motivo.value, "logs-rp")
            await interaction.response.send_message("❌ {} reprovado!".format(self.member.mention), ephemeral=True)
        try: await self.member.send(embed=dm_embed)
        except: pass
        await asyncio.sleep(3)
        if user_id in tickets_abertos:
            del tickets_abertos[user_id]
            salvar_tickets()
        if user_id in respostas_ticket: del respostas_ticket[user_id]
        await channel.delete()
        if category and category.name == "WHITELIST":
            if len(category.channels) == 0:
                await category.delete()

async def enviar_log(tipo, user, staff, motivo, canal_nome):
    canal = discord.utils.get(user.guild.channels, name=canal_nome)
    if canal:
        embed = discord.Embed(title="📝 LOG - {}".format(tipo), color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="Jogador", value=user.mention, inline=True)
        embed.add_field(name="Staff", value=staff.mention if staff else "SISTEMA", inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        await canal.send(embed=embed)

# FUNÇÃO GLOBAL PRA VERIFICAR SE JÁ TEM TICKET
async def ja_tem_ticket(guild, user, interaction):
    user_id = str(user.id)
    if user_id in tickets_abertos:
        canal_ticket = guild.get_channel(tickets_abertos[user_id])
        if canal_ticket:
            await interaction.response.send_message("❌ Você já tem um ticket aberto: {}".format(canal_ticket.mention), ephemeral=True)
            return True
        else:
            del tickets_abertos[user_id]
            salvar_tickets()
    return False

async def criar_ticket(interaction, tipo):
    guild = interaction.guild
    user = interaction.user
    if await ja_tem_ticket(guild, user, interaction): return
    categoria = discord.utils.get(guild.categories, id=CATEGORIA_NORMAL)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }
    nome = f"ticket-{tipo}-{user.name}"
    canal = await guild.create_text_channel(name=nome, category=categoria, overwrites=overwrites)
    tickets_abertos[str(user.id)] = canal.id
    salvar_tickets()
    await canal.send(f"{user.mention} <@&{STAFF_ROLE_ID}>\n**Ticket {tipo} aberto!**", view=TicketPainelView())
    await interaction.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

async def criar_ticket_vip(interaction, tipo):
    guild = interaction.guild
    user = interaction.user
    if await ja_tem_ticket(guild, user, interaction): return
    categoria = discord.utils.get(guild.categories, id=CATEGORIA_LOJA)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }
    nome = f"ticket-{tipo}-{user.name}"
    canal = await guild.create_text_channel(name=nome, category=categoria, overwrites=overwrites)
    tickets_abertos[str(user.id)] = canal.id
    salvar_tickets()
    await canal.send(f"{user.mention} <@&{STAFF_ROLE_ID}>\n**Ticket {tipo.upper()} aberto!**", view=TicketPainelView())
    await interaction.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

async def criar_ticket_whitelist(interaction):
    guild = interaction.guild
    user = interaction.user
    if await ja_tem_ticket(guild, user, interaction): return
    categoria = discord.utils.get(guild.categories, id=CATEGORIA_WHITELIST)
    if not categoria: categoria = await guild.create_category("WHITELIST")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }
    canal = await guild.create_text_channel("whitelist-{}".format(user.name), category=categoria, overwrites=overwrites)
    tickets_abertos[str(user.id)] = canal.id
    salvar_tickets()
    respostas_ticket[str(user.id)] = []
    await canal.send("{} Bem-vindo a whitelist! **{}**".format(user.mention, PERGUNTAS[0]), view=TicketCloseView())
    await interaction.response.send_message("✅ Ticket criado: {}".format(canal.mention), ephemeral=True)

@bot.event
async def on_ready():
    print('{} Online'.format(bot.user))
    bot.add_view(TicketPainelView())
    bot.add_view(TicketView())
    bot.add_view(LojaView())
    bot.add_view(WhitelistButton())
    bot.add_view(TicketCloseView())

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.name.startswith("whitelist-"):
        for user_id, channel_id in tickets_abertos.items():
            if channel_id == message.channel.id:
                if user_id not in respostas_ticket: respostas_ticket[user_id] = []
                respostas_ticket[user_id].append(message.content)
                num = len(respostas_ticket[user_id])
                if num < len(PERGUNTAS):
                    await message.channel.send("✅ Anotado! Pergunta {}: **{}**".format(num + 1, PERGUNTAS[num]))
                else:
                    await message.channel.send("✅ Todas as 15 perguntas respondidas! Aguarde a {} aprovar.".format(STAFF_MENTION))
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def painel(ctx):
    await ctx.send(embed=discord.Embed(title="🏠 Painel Principal", description="Escolha uma opção:", color=0x9B59B6), view=TicketView())

@bot.command()
@commands.has_permissions(administrator=True)
async def painelloja(ctx):
    await ctx.send(embed=discord.Embed(title="💎 LOJA PARADOXO RP", description="VIP abaixo:", color=0xF1C40F), view=LojaView())

@bot.command()
@commands.has_permissions(administrator=True)
async def painelwhitelist(ctx):
    await ctx.send(embed=discord.Embed(title="📋 SISTEMA DE WHITELIST", description="15 perguntas", color=0x2ECC71), view=WhitelistButton())

bot.run(os.getenv("TOKEN"))
