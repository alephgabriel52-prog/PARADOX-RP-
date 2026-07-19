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

STAFF_ROLE_ID = 1528409545439969433  # CARGO EQUIPE STAFF
STAFF_MENTION = "<@&{}>".format(STAFF_ROLE_ID)

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

async def criar_categoria_punicoes(guild):
    category = discord.utils.get(guild.categories, name="PUNIÇÕES")
    if not category:
        category = await guild.create_category("PUNIÇÕES")
    canais = ["logs", "logs-rp", "logs-ban", "logs-kick", "logs-warn", "logs-antisabotagem"]
    for nome in canais:
        if not discord.utils.get(guild.channels, name=nome):
            overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
            await guild.create_text_channel(nome, category=category, overwrites=overwrites)
    return category

async def enviar_log(tipo, user, staff, motivo, canal_nome):
    canal = discord.utils.get(user.guild.channels, name=canal_nome)
    if canal:
        embed = discord.Embed(title="📝 LOG - {}".format(tipo), color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="Jogador", value=user.mention, inline=True)
        embed.add_field(name="Staff", value=staff.mention if staff else "SISTEMA", inline=True)
        embed.add_field(name="Horário", value=datetime.now().strftime('%d/%m/%Y %H:%M'), inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        await canal.send(embed=embed)

respostas_ticket = {}
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


class WhitelistButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Fazer Whitelist", style=discord.ButtonStyle.green, emoji="✅", custom_id="btn_whitelist_001")
    async def whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        if user_id in tickets_abertos:
            canal_ticket = interaction.guild.get_channel(tickets_abertos[user_id])
            if canal_ticket:
                return await interaction.response.send_message("❌ Você já tem um ticket aberto: {}".format(canal_ticket.mention), ephemeral=True)
            else:
                del tickets_abertos[user_id]
                salvar_tickets()
        category = discord.utils.get(interaction.guild.categories, name="WHITELIST") or await interaction.guild.create_category("WHITELIST")
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        channel = await interaction.guild.create_text_channel("whitelist-{}".format(interaction.user.name), category=category, overwrites=overwrites)
        tickets_abertos[user_id] = channel.id
        salvar_tickets()
        respostas_ticket[user_id] = []
        await channel.send("{} Bem-vindo a whitelist! Responda a pergunta 1:\n\n**{}**".format(interaction.user.mention, PERGUNTAS[0]), view=TicketCloseView())
        await interaction.response.send_message("✅ Ticket criado: {}".format(channel.mention), ephemeral=True)

class StaffButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Chamar Staff", style=discord.ButtonStyle.red, emoji="🚨", custom_id="btn_chamar_staff")
    async def chamar_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        if user_id in tickets_abertos:
            canal_ticket = interaction.guild.get_channel(tickets_abertos[user_id])
            return await interaction.response.send_message("❌ Já tem chamado aberto: {}".format(canal_ticket.mention), ephemeral=True)
        category = discord.utils.get(interaction.guild.categories, name="ATENDIMENTO") or await interaction.guild.create_category("ATENDIMENTO")
        role_staff = interaction.guild.get_role(STAFF_ROLE_ID)
        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True), interaction.guild.me: discord.PermissionOverwrite(view_channel=True)}
        if role_staff: overwrites[role_staff] = discord.PermissionOverwrite(view_channel=True)
        channel = await interaction.guild.create_text_channel("atendimento-{}".format(interaction.user.name), category=category, overwrites=overwrites)
        tickets_abertos[user_id] = channel.id
        salvar_tickets()
        await channel.send("{} {}".format(STAFF_MENTION, interaction.user.mention) + " abriu um chamado!")
        await interaction.response.send_message("✅ Atendimento aberto: {}".format(channel.mention), ephemeral=True)

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
        if self.tipo == "aprovado":
            dm_embed = discord.Embed(title="✅ WHITELIST APROVADA - PARADOX RP", description="Olá {}, sua whitelist foi **APROVADA**!\n\n**Motivo:** {}\n\nBem-vindo ao servidor! Leia as regras e bom RP.".format(self.member.name, self.motivo.value), color=0x00ff00)
            if interaction.guild.icon: dm_embed.set_thumbnail(url=interaction.guild.icon.url)
            role = discord.utils.get(interaction.guild.roles, name="Membro")
            if role: await self.member.add_roles(role)
            if user_id in respostas_ticket and len(respostas_ticket[user_id]) >= 15:
                nick = respostas_ticket[user_id][14]
                try: await self.member.edit(nick=nick[:32])
                except: pass
            await enviar_log("WHITELIST APROVADA", self.member, interaction.user, self.motivo.value, "logs-rp")
            await interaction.response.send_message("✅ {} aprovado! Apagando ticket em 3s...".format(self.member.mention), ephemeral=True)
        else:
            dm_embed = discord.Embed(title="❌ WHITELIST REPROVADA - PARADOX RP", description="Olá {}, infelizmente sua whitelist foi **REPROVADA**.\n\n**Motivo:** {}\n\nVocê pode abrir outro ticket após corrigir o motivo acima.".format(self.member.name, self.motivo.value), color=0xff0000)
            if interaction.guild.icon: dm_embed.set_thumbnail(url=interaction.guild.icon.url)
            await enviar_log("WHITELIST REPROVADA", self.member, interaction.user, self.motivo.value, "logs-rp")
            await interaction.response.send_message("❌ {} reprovado! Apagando ticket em 3s...".format(self.member.mention), ephemeral=True)
        try:
            await self.member.send(embed=dm_embed)
        except discord.Forbidden:
            await interaction.followup.send("⚠️ Não consegui mandar DM para {}. DM fechada.".format(self.member.mention), ephemeral=True)
        except Exception as e:
            print("Erro ao enviar DM: {}".format(e))
        await asyncio.sleep(3)
        if user_id in tickets_abertos:
            del tickets_abertos[user_id]
            salvar_tickets()
        if user_id in respostas_ticket: del respostas_ticket[user_id]
        await interaction.channel.delete()

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    canal_log = discord.utils.get(message.guild.channels, name="logs")
    if canal_log:
        embed = discord.Embed(title="🗑️ MENSAGEM APAGADA", color=0xffa500, timestamp=discord.utils.utcnow())
        embed.add_field(name="Autor", value=message.author.mention, inline=True)
        embed.add_field(name="Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="Conteúdo", value=message.content[:1024] if message.content else "*Embed/Anexo*", inline=False)
        await canal_log.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel):
    for user_id, channel_id in list(tickets_abertos.items()):
        if channel_id == channel.id:
            del tickets_abertos[user_id]
            salvar_tickets()
            if user_id in respostas_ticket: del respostas_ticket[user_id]
            break
    await asyncio.sleep(1)
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        if entry.user and not entry.user.bot:
            await punir_sabotador(entry.user, "Apagou o canal: {}".format(channel.name), channel.guild)

@bot.event
async def on_guild_role_delete(role):
    await asyncio.sleep(1)
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        if entry.user and not entry.user.bot:
            await punir_sabotador(entry.user, "Apagou o cargo: {}".format(role.name), role.guild)

async def punir_sabotador(member, motivo, guild):
    try:
        await member.edit(roles=[])
        try: await member.send("🚨 Tá pensando que aqui é bagunça")
        except: pass
        await enviar_log("ANTI-SABOTAGEM", member, guild.me, motivo, "logs-antisabotagem")
    except Exception as e:
        print("Erro ao punir: {}".format(e))

@bot.event
async def on_ready():
    print('{} Online'.format(bot.user))
    bot.add_view(WhitelistButton())
    bot.add_view(TicketCloseView())
    bot.add_view(StaffButton())

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
                    await message.channel.send("✅ Todas as 16 perguntas respondidas! Aguarde um membro da {} para Aprovar/Reprovar.".format(STAFF_MENTION))
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ Você não tem permissão. Precisa ser da equipe staff.", delete_after=5)
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando `!{}` não existe. Use `!cmds`".format(ctx.invoked_with), delete_after=5)

@bot.command()
async def cmds(ctx):
    embed = discord.Embed(title="📜 PAINEL DE COMANDOS - PARADOX RP", color=0x3498db)
    embed.add_field(name="🎫 PAINÉIS - `Administrador`", value="`!painelwhitelist`\n`!painelstaff`\n`!painelinfo`\n`!painelanti`", inline=False)
    embed.add_field(name="👮 EQUIPE STAFF - Cargo {}".format(STAFF_MENTION), value="`!algemar @user`\n`!warn @user motivo`\n`!buscar @user`\n`!addgogo @user`\n`!listajogo`", inline=False)
    embed.add_field(name="🔨 ADMIN - `Banir/Expulsar`", value="`!ban @user motivo`\n`!kick @user motivo`", inline=False)
    embed.add_field(name="ℹ️ GERAL", value="`!cmds` - Mostra este painel no PV", inline=False)

    try:
        await ctx.author.send(embed=embed)
        await ctx.send("📩 {} Te mandei a lista de comandos no PV!".format(ctx.author.mention), delete_after=3)
    except discord.Forbidden:
        await ctx.send("❌ {} Não consegui te mandar PV. Abre sua DM pra eu conseguir enviar.".format(ctx.author.mention))

@bot.command()
@is_staff()
async def buscar(ctx, member: discord.Member):
    user_id = str(member.id)
    total_warns = len(warns.get(user_id, []))
    embed = discord.Embed(title="🔍 FICHA DE {}".format(member.name.upper()), color=0x2ecc71)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Entrou em", value=member.joined_at.strftime('%d/%m/%Y'), inline=True)
    embed.add_field(name="Warns", value="**{}/3**".format(total_warns), inline=True)
    if total_warns > 0:
        embed.add_field(name="Motivos", value="\n".join(warns[user_id]), inline=False)
    await ctx.send(embed=embed)

@bot.command()
@is_staff()
async def algemar(ctx, member: discord.Member):
    role_algema = discord.utils.get(ctx.guild.roles, name="Algemado")
    if not role_algema: role_algema = await ctx.guild.create_role(name="Algemado", color=0x808080)
    if role_algema in member.roles:
        await member.remove_roles(role_algema)
        await ctx.send("🔓 {} foi **desalgemado**".format(member.mention))
        await enviar_log("DESALGEMAR", member, ctx.author, "Liberado", "logs-rp")
    else:
        await member.add_roles(role_algema)
        await ctx.send("⛓️ {} foi **algemado**".format(member.mention))
        await enviar_log("ALGEMAR", member, ctx.author, "Algemado para abordagem RP", "logs-rp")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.ban(reason=reason)
    await enviar_log("BAN", member, ctx.author, reason, "logs-ban")
    await ctx.send("🔨 {} foi banido.\nMotivo: {}".format(member.mention, reason))

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.kick(reason=reason)
    await enviar_log("KICK", member, ctx.author, reason, "logs-kick")
    await ctx.send("👢 {} foi expulso.\nMotivo: {}".format(member.mention, reason))

@bot.command()
@is_staff()
async def warn(ctx, member: discord.Member, *, motivo):
    user_id = str(member.id)
    if user_id not in warns: warns[user_id] = []
    warns[user_id].append(motivo)
    salvar_warns()
    total = len(warns[user_id])
    await enviar_log("WARN", member, ctx.author, "{} | Total: {}/3".format(motivo, total), "logs-warn")
    await ctx.send("⚠️ {} recebeu warn. Total: **{}/3**".format(member.mention, total))

@bot.command()
@is_staff()
async def addgogo(ctx, member: discord.Member):
    """Adiciona alguém na gogo"""
    await ctx.send("✅ {} foi adicionado na gogo".format(member.mention))
    await enviar_log("ADDGOGO", member, ctx.author, "Adicionado na gogo", "logs-rp")

@bot.command()
@is_staff()
async def listajogo(ctx):
    """Lista quem está na gogo"""
    await ctx.send("📋 **Lista da Gogo:**\nNenhum player na lista ainda.")

@bot.command()
@commands.has_permissions(administrator=True)
async def painel(ctx):
    ed = discord.Embed(
        title="🏠 Painel Principal - PARADOXO RP",
        description="Precisa de ajuda? Escolha uma opção abaixo:",
        color=0x9B59B6
    )
    a = discord.ui.View()
    a.add_item(discord.ui.Button(label="Suporte", emoji="🎫", style=discord.ButtonStyle.gray, custom_id="suporte"))
    a.add_item(discord.ui.Button(label="Denunciar", emoji="🚨", style=discord.ButtonStyle.red, custom_id="denuncia"))
    a.add_item(discord.ui.Button(label="Loja/VIP", emoji="💎", style=discord.ButtonStyle.green, custom_id="loja"))
    await ctx.send(embed=ed, view=a)
@commands.has_permissions(administrator=True)
async def painelwhitelist(ctx):
    embed = discord.Embed(title="📋 SISTEMA DE WHITELIST", description="Clique no botão abaixo para iniciar a whitelist com 15 perguntas", color=0x2ECC71)
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Fazer Whitelist", emoji="📝", style=discord.ButtonStyle.green, custom_id="wl"))
    await ctx.send(embed=embed, view=view)
    
@bot.command()
@commands.has_permissions(administrator=True)
async def painelloja(ctx):
    ed = discord.Embed(
        title="💎 LOJA PARADOXO RP",
        description="Compre seus itens VIP abaixo:",
        color=0xF1C40F
    )
    a = discord.ui.View()
    a.add_item(discord.ui.Button(label="VIP Bronze", emoji="🥉", style=discord.ButtonStyle.secondary, custom_id="vipbronze"))
    a.add_item(discord.ui.Button(label="VIP Prata", emoji="🥈", style=discord.ButtonStyle.secondary, custom_id="vipprata"))
    a.add_item(discord.ui.Button(label="VIP Ouro", emoji="🥇", style=discord.ButtonStyle.success, custom_id="vipouro"))
    await ctx.send(embed=ed, view=a)
    
async def painelinfo(ctx):
    canal = discord.utils.get(ctx.guild.channels, name="informacoes") or await ctx.guild.create_text_channel("informacoes")
    membros = ctx.guild.member_count
    embed = discord.Embed(title="📢 INFORMAÇÕES DO SERVIDOR", color=0x3498db, timestamp=discord.utils.utcnow())
    embed.add_field(name="👑 Dono", value=ctx.guild.owner.mention, inline=True)
    embed.add_field(name="👥 Membros", value="{}".format(membros), inline=True)
    embed.add_field(name="📅 Criado em", value=ctx.guild.created_at.strftime('%d/%m/%Y'), inline=True)
    embed.add_field(name="🌐 IP do Servidor", value="`ip.aqui.com:30120`", inline=False)
    embed.add_field(name="⏰ Horário RP", value="Seg - Dom: 14h às 00h", inline=False)
    await canal.send(embed=embed)
    await ctx.send("✅ Painel de informações criado em {}".format(canal.mention))

@bot.command()
@commands.has_permissions(administrator=True)
async def painelstaff(ctx):
    canal = discord.utils.get(ctx.guild.channels, name="staff") or await ctx.guild.create_text_channel("staff")
    role_staff = ctx.guild.get_role(STAFF_ROLE_ID)
    staff_online = len([m for m in ctx.guild.members if m.status!= discord.Status.offline and role_staff in m.roles]) if role_staff else 0
    desc = "Precisa de ajuda? Clique no botão abaixo\nStaff: " + STAFF_MENTION
    embed = discord.Embed(title="👮 EQUIPE DE STAFF", description=desc, color=0xe74c3c)
    embed.add_field(name="Staff Online", value="**{}** online agora".format(staff_online), inline=False)
    embed.add_field(name="Como funciona", value="1. Clique no botão\n2. Um ticket será aberto\n3. Aguarde um staff te atender", inline=False)
    await canal.send(embed=embed, view=StaffButton())
    await ctx.send("✅ Painel de staff criado em {}".format(canal.mention))
@bot.event
async def on_interaction(interaction):
    if interaction.type!= discord.InteractionType.component:
        return

    guild = interaction.guild
    user = interaction.user
    custom_id = interaction.data['custom_id']
    STAFF_ROLE_ID = 152840954539960433 # Já tá no teu código linha 378

    # WL
    if custom_id == 'wl':
        categoria = discord.utils.get(guild.categories, id=1528409546148544572)
        nome = f"wl-{user.name}"
        msg = f"{user.mention} <@&{STAFF_ROLE_ID}>\n**Bem-vindo a Whitelist!**\n\n**Pergunta 1/15:** {PERGUNTAS[0]}"

    # TICKET NORMAL
    elif custom_id == "vipbronze":
    await criar_ticket(interaction, "vip-bronze")
elif custom_id == "vipprata":
    await criar_ticket(interaction, "vip-prata")
elif custom_id == "vipouro":
    await criar_ticket(interaction, "vip-ouro")
    else:
        categoria = discord.utils.get(guild.categories, id=1528445353022455951)
        nome = f"ticket-{custom_id}-{user.name}"
        msg = f"{user.mention} <@&{STAFF_ROLE_ID}>\n**Ticket de {custom_id} aberto!** Explique seu caso."

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    channel = await guild.create_text_channel(name=nome, category=categoria, overwrites=overwrites)
    await channel.send(msg)
    await interaction.response.send_message(f"✅ Ticket criado: {channel.mention}", ephemeral=True)
bot.run(os.getenv("TOKEN"))
