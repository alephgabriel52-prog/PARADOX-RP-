import discord
from discord.ext import commands
import os
import json
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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

ARQUIVO_DINHEIRO = 'economia.json'
ARQUIVO_WARNS = 'warns.json'
ARQUIVO_FICHA = 'ficha.json'
ARQUIVO_ITENS = 'itens.json'
for arquivo, var in [(ARQUIVO_WARNS, 'warns'), (ARQUIVO_DINHEIRO, 'economia'), (ARQUIVO_FICHA, 'ficha'), (ARQUIVO_ITENS, 'itens')]:
    try: globals()[var] = json.load(open(arquivo, 'r'))
    except: globals()[var] = {}
def salvar_tudo():
    json.dump(warns, open(ARQUIVO_WARNS, 'w'))
    json.dump(economia, open(ARQUIVO_DINHEIRO, 'w'))
    json.dump(ficha, open(ARQUIVO_FICHA, 'w'))
    json.dump(itens, open(ARQUIVO_ITENS, 'w'))

async def get_canal_punicao(guild, tipo):
    category = discord.utils.get(guild.categories, name="PUNIÇÕES")
    if not category: category = await guild.create_category("PUNIÇÕES")
    nome_canal = f"logs-{tipo}"
    canal = discord.utils.get(guild.channels, name=nome_canal)
    if not canal:
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        canal = await guild.create_text_channel(nome_canal, category=category, overwrites=overwrites)
    return canal

async def enviar_log(tipo, user, staff, motivo, canal_tipo="rp", extra=""):
    guild = user.guild
    if canal_tipo == "ban": canal = await get_canal_punicao(guild, "ban")
    elif canal_tipo == "kick": canal = await get_canal_punicao(guild, "kick")
    elif canal_tipo == "warn": canal = await get_canal_punicao(guild, "warn")
    else: canal = discord.utils.get(guild.channels, name="logs-rp")

    if canal:
        embed = discord.Embed(title=f"📝 LOG - {tipo}", color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="Jogador", value=user.mention, inline=True)
        embed.add_field(name="Staff", value=staff.mention if staff else "SISTEMA", inline=True)
        embed.add_field(name="Horário", value=datetime.now().strftime('%d/%m/%Y %H:%M'), inline=True)
        embed.add_field(name="Motivo", value=motivo[:1024], inline=False)
        if extra: embed.add_field(name="Detalhes", value=extra, inline=False)
        await canal.send(embed=embed)

tickets_abertos = {}
respostas_ticket = {}
PERGUNTAS = ["1. Nome RP?", "2. Idade?", "3. Leu as regras?", "4. O que é RP?", "5. FailRP?", "6. MetaGaming?", "7. PowerGaming?", "8. Jogou em outro servidor?", "9. Personagem?", "10. Abordado pela PM?", "11. Assaltado?", "12. Tem mic?", "13. Horas por dia?", "14. Promete não usar cheat?", "15. Nick Discord?", "16. Porque aceitar?"]

CARGOS_RP = {"policia": "Policial", "medico": "Médico", "mecanico": "Mecânico", "taxista": "Taxista", "desempregado": "Desempregado"}
SALARIOS = {"Policial": 800, "Médico": 700, "Mecânico": 600, "Taxista": 400, "Desempregado": 100}

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
        motivo_texto = self.motivo.value
        if self.tipo == "aprovado":
            role = discord.utils.get(interaction.guild.roles, name="Membro")
            if role: await self.member.add_roles(role)
            if user_id not in economia: economia[user_id] = {"carteira": 1000, "banco": 0, "ultimo_salario": 0}
            if user_id not in itens: itens[user_id] = []
            if user_id in respostas_ticket and len(respostas_ticket[user_id]) >= 15:
                nick = respostas_ticket[user_id][14]
                try: await self.member.edit(nick=nick[:32])
                except: pass
            salvar_tudo()
            try: await self.member.send(embed=discord.Embed(title="✅ APROVADO", description=f"Motivo: {motivo_texto}", color=0x00ff00))
            except: pass
            await enviar_log("WHITELIST APROVADA", self.member, interaction.user, motivo_texto, "rp")
            await interaction.response.send_message(f"✅ {self.member.mention} aprovado! DM enviada", ephemeral=True)
        else:
            try: await self.member.send(embed=discord.Embed(title="❌ REPROVADO", description=f"Motivo: {motivo_texto}", color=0xff0000))
            except: pass
            await enviar_log("WHITELIST REPROVADA", self.member, interaction.user, motivo_texto, "rp")
            await interaction.response.send_message(f"❌ {self.member.mention} reprovado! DM enviada", ephemeral=True)
        if user_id in tickets_abertos: del tickets_abertos[user_id]
        if user_id in respostas_ticket: del respostas_ticket[user_id]
        await interaction.channel.delete()

@bot.event
async def on_ready():
    print(f'{bot.user} Online')
    bot.add_view(WhitelistButton())
    bot.add_view(TicketCloseView())

# TIREI O on_member_remove = SEM COMBAT LOG

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
        await enviar_log("DESALGEMAR", member, ctx.author, "Liberado", "rp")
    else:
        await member.add_roles(role_algema)
        await ctx.send(f"⛓️ {member.mention} foi **algemado**") # TIREI A PARTE DE 3 DIAS BAN
        await enviar_log("ALGEMAR", member, ctx.author, "Algemado para abordagem RP", "rp")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def setpolicial(ctx, member: discord.Member, *, corporacao):
    role = discord.utils.get(ctx.guild.roles, name="Policial")
    if not role: role = await ctx.guild.create_role(name="Policial", color=0x0000ff)
    for r in CARGOS_RP.values():
        role_old = discord.utils.get(ctx.guild.roles, name=r)
        if role_old in member.roles: await member.remove_roles(role_old)
    await member.add_roles(role)
    extra = f"Corporação: {corporacao}\nSetado por: {ctx.author.name}"
    await enviar_log("SET POLICIAL", member, ctx.author, f"Adicionado na PM", "rp", extra)
    await ctx.send(f"👮 {member.mention} foi setado como **Policial**\n🏢 Corporação: **{corporacao}**")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    extra = f"Banido por: {ctx.author.name}\nHorário: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    await member.ban(reason=reason)
    await enviar_log("BAN", member, ctx.author, reason, "ban", extra)
    await ctx.send(f"🔨 {member.mention} foi banido.\nMotivo: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    extra = f"Kickado por: {ctx.author.name}\nHorário: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    await member.kick(reason=reason)
    await enviar_log("KICK", member, ctx.author, reason, "kick", extra)
    await ctx.send(f"👢 {member.mention} foi expulso.\nMotivo: {reason}")

@bot.command()
@commands.has_permissions(administrator=True)
async def painelwhitelist(ctx):
    canal = discord.utils.get(ctx.guild.channels, name="whitelist") or await ctx.guild.create_text_channel("whitelist")
    await canal.send(embed=discord.Embed(title="🎫 SISTEMA DE WHITELIST", description="Clique no botão abaixo", color=0x00ff00), view=WhitelistButton())
    await ctx.send(f"✅ Painel criado em {canal.mention}")

bot.run(os.getenv("TOKEN"))
