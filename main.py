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
intents.audit_logs = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

ARQUIVO_WARNS = 'warns.json'
try: warns = json.load(open(ARQUIVO_WARNS, 'r'))
except: warns = {}
def salvar_warns(): json.dump(warns, open(ARQUIVO_WARNS, 'w'))

async def criar_categoria_punicoes(guild):
    category = discord.utils.get(guild.categories, name="PUNIÇÕES")
    if not category: 
        category = await guild.create_category("PUNIÇÕES")
    
    canais = ["logs-ban", "logs-kick", "logs-warn", "logs-rp", "logs-antisabotagem"]
    for nome in canais:
        if not discord.utils.get(guild.channels, name=nome):
            overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
            await guild.create_text_channel(nome, category=category, overwrites=overwrites)
    return category

async def enviar_log(tipo, user, staff, motivo, canal_nome):
    canal = discord.utils.get(user.guild.channels, name=canal_nome)
    if canal:
        embed = discord.Embed(title=f"📝 LOG - {tipo}", color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="Jogador", value=user.mention, inline=True)
        embed.add_field(name="Staff", value=staff.mention if staff else "SISTEMA", inline=True)
        embed.add_field(name="Horário", value=datetime.now().strftime('%d/%m/%Y %H:%M'), inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        await canal.send(embed=embed)

tickets_abertos = {}
respostas_ticket = {}
PERGUNTAS = ["1. Nome RP?", "2. Idade?", "3. Leu as regras?", "4. O que é RP?", "5. FailRP?", "6. MetaGaming?", "7. PowerGaming?", "8. Jogou em outro servidor?", "9. Personagem?", "10. Abordado pela PM?", "11. Assaltado?", "12. Tem mic?", "13. Horas por dia?", "14. Promete não usar cheat?", "15. Nick Discord?", "16. Porque aceitar?"]

class WhitelistButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Fazer Whitelist", style=discord.ButtonStyle.green, emoji="✅", custom_id="btn_whitelist_001")
    async def whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) in tickets_abertos: return await interaction.response.send_message("❌ Já tem ticket aberto!", ephemeral=True)
        category = discord.utils.get(interaction.guild.categories, name="WHITELIST") or await interaction.guild.create_category("WHITELIST")
        channel = await interaction.guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites={interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True), interaction.guild.me: discord.PermissionOverwrite(view_channel=True)})
        tickets_abertos[str(interaction.user.id)] = channel.id
        respostas_ticket[str(interaction.user.id)] = []
        await channel.send(f"{interaction.user.mention} Pergunta 1: **{PERGUNTAS[0]}**", view=TicketCloseView())
        await interaction.response.send_message(f"✅ Ticket: {channel.mention}", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green, emoji="✅", custom_id="btn_aprovar_001")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_modal(MotivoModal(interaction.channel.members[1], "aprovado"))
    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.red, emoji="❌", custom_id="btn_reprovar_001")
    async def reprovar(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_modal(MotivoModal(interaction.channel.members[1], "reprovado"))

class MotivoModal(discord.ui.Modal):
    def __init__(self, member, tipo): 
        super().__init__(title=f"Motivo {tipo}")
        self.member, self.tipo = member, tipo
        self.motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, required=True, max_length=500)
        self.add_item(self.motivo)
    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(self.member.id)
        if self.tipo == "aprovado":
            role = discord.utils.get(interaction.guild.roles, name="Membro")
            if role: await self.member.add_roles(role)
            if user_id in respostas_ticket and len(respostas_ticket[user_id]) >= 15:
                nick = respostas_ticket[user_id][14]
                try: await self.member.edit(nick=nick[:32])
                except: pass
            try: await self.member.send(embed=discord.Embed(title="✅ APROVADO", description=f"Motivo: {self.motivo.value}", color=0x00ff00))
            except: pass
            await enviar_log("WHITELIST APROVADA", self.member, interaction.user, self.motivo.value, "logs-rp")
            await interaction.response.send_message(f"✅ {self.member.mention} aprovado!", ephemeral=True)
        else:
            try: await self.member.send(embed=discord.Embed(title="❌ REPROVADO", description=f"Motivo: {self.motivo.value}", color=0xff0000))
            except: pass
            await enviar_log("WHITELIST REPROVADA", self.member, interaction.user, self.motivo.value, "logs-rp")
            await interaction.response.send_message(f"❌ {self.member.mention} reprovado!", ephemeral=True)
        if user_id in tickets_abertos: del tickets_abertos[user_id]
        if user_id in respostas_ticket: del respostas_ticket[user_id]
        await interaction.channel.delete()

# ===== ANTI SABOTAGEM =====
@bot.event
async def on_guild_channel_delete(channel):
    await asyncio.sleep(1)
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        if entry.user and not entry.user.bot:
            await punir_sabotador(entry.user, f"Apagou o canal: {channel.name}", channel.guild)

@bot.event
async def on_guild_role_delete(role):
    await asyncio.sleep(1)
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        if entry.user and not entry.user.bot:
            await punir_sabotador(entry.user, f"Apagou o cargo: {role.name}", role.guild)

async def punir_sabotador(member, motivo, guild):
    try:
        await member.edit(roles=[])
        try: await member.send("🚨 Tá pensando que aqui é bagunça")
        except: pass
        await enviar_log("ANTI-SABOTAGEM", member, guild.me, motivo, "logs-antisabotagem")
    except Exception as e:
        print(f"Erro ao punir: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} Online')
    bot.add_view(WhitelistButton())
    bot.add_view(TicketCloseView())

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.name.startswith("ticket-"):
        for user_id, channel_id in tickets_abertos.items():
            if channel_id == message.channel.id:
                if user_id not in respostas_ticket: respostas_ticket[user_id] = []
                respostas_ticket[user_id].append(message.content)
                num = len(respostas_ticket[user_id])
                if num < len(PERGUNTAS):
                    await message.channel.send(f"✅ Anotado! Pergunta {num + 1}: **{PERGUNTAS[num]}**")
                else:
                    await message.channel.send("✅ Todas respondidas! Clique em Aprovar/Reprovar e escreva o motivo.")
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def algemar(ctx, member: discord.Member):
    role_algema = discord.utils.get(ctx.guild.roles, name="Algemado")
    if not role_algema: role_algema = await ctx.guild.create_role(name="Algemado", color=0x808080)
    if role_algema in member.roles:
        await member.remove_roles(role_algema)
        await ctx.send(f"🔓 {member.mention} foi **desalgemado**")
        await enviar_log("DESALGEMAR", member, ctx.author, "Liberado", "logs-rp")
    else:
        await member.add_roles(role_algema)
        await ctx.send(f"⛓️ {member.mention} foi **algemado**")
        await enviar_log("ALGEMAR", member, ctx.author, "Algemado para abordagem RP", "logs-rp")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.ban(reason=reason)
    await enviar_log("BAN", member, ctx.author, reason, "logs-ban")
    await ctx.send(f"🔨 {member.mention} foi banido.\nMotivo: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.kick(reason=reason)
    await enviar_log("KICK", member, ctx.author, reason, "logs-kick")
    await ctx.send(f"👢 {member.mention} foi expulso.\nMotivo: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def warn(ctx, member: discord.Member, *, motivo):
    user_id = str(member.id)
    if user_id not in warns: warns[user_id] = []
    warns[user_id].append(motivo)
    salvar_warns()
    total = len(warns[user_id])
    await enviar_log("WARN", member, ctx.author, f"{motivo} | Total: {total}/3", "logs-warn")
    await ctx.send(f"⚠️ {member.mention} recebeu warn. Total: **{total}/3**")

@bot.command()
@commands.has_permissions(administrator=True)
async def painelwhitelist(ctx):
    canal = discord.utils.get(ctx.guild.channels, name="whitelist") or await ctx.guild.create_text_channel("whitelist")
    await canal.send(embed=discord.Embed(title="🎫 SISTEMA DE WHITELIST", description="Clique no botão abaixo", color=0x00ff00), view=WhitelistButton())
    await ctx.send(f"✅ Painel criado em {canal.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def painelanti(ctx):
    await criar_categoria_punicoes(ctx.guild)
    canal = discord.utils.get(ctx.guild.channels, name="logs-antisabotagem")
    embed = discord.Embed(title="🚨 PAINEL ANTI-SABOTAGEM", description="Quem apagar canal ou cargo perde todos os cargos e leva DM", color=0x8b0000)
    await canal.send(embed=embed)
    await ctx.send("✅ Categoria `PUNIÇÕES` e canal `logs-antisabotagem` criados com sucesso!")

bot.run(os.getenv("TOKEN"))
