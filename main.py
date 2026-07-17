import discord
from discord.ext import commands
import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from threading import Thread

app = Flask('')

# ROTA PRA RECEBER DO ROBLOX
@app.route('/policial', methods=['POST'])
def log_policial():
    data = request.json
    acao = data.get('acao') # "prender" "multar" "apreender_carro"
    policial = data.get('policial')
    alvo = data.get('alvo')
    motivo = data.get('motivo')
    tempo = data.get('tempo') # "10m" "1h"

    # MANDA PRO DISCORD
    bot.loop.create_task(enviar_log_policial(acao, policial, alvo, motivo, tempo))
    return jsonify({"status": "ok"})

@app.route('/')
def home(): return "Bot Online 24h"

def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

WEBHOOK_URL = ""
ARQUIVO_DINHEIRO = 'economia.json'
ARQUIVO_WARNS = 'warns.json'
ARQUIVO_FICHA = 'ficha.json'
ARQUIVO_ITENS = 'itens.json'

for arquivo, var in [(ARQUIVO_WARNS, 'warns'), (ARQUIVO_DINHEIRO, 'economia'), (ARQUIVO_FICHA, 'ficha'), (ARQUIVO_ITENS, 'itens')]:
    try:
        with open(arquivo, 'r') as f: globals()[var] = json.load(f)
    except: globals()[var] = {}

def salvar_tudo():
    with open(ARQUIVO_WARNS, 'w') as f: json.dump(warns, f)
    with open(ARQUIVO_DINHEIRO, 'w') as f: json.dump(economia, f)
    with open(ARQUIVO_FICHA, 'w') as f: json.dump(ficha, f)
    with open(ARQUIVO_ITENS, 'w') as f: json.dump(itens, f)

async def get_canal_punicao(guild, tipo):
    category = discord.utils.get(guild.categories, name="PUNIÇÕES")
    if not category: category = await guild.create_category("PUNIÇÕES")
    nome_canal = f"logs-{tipo}"
    canal = discord.utils.get(guild.channels, name=nome_canal)
    if not canal:
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        canal = await guild.create_text_channel(nome_canal, category=category, overwrites=overwrites)
    return canal

async def get_canal_policial(guild):
    category = discord.utils.get(guild.categories, name="LOGS POLICIAL")
    if not category: category = await guild.create_category("LOGS POLICIAL")
    canal = discord.utils.get(guild.channels, name="logs-rp-policial")
    if not canal:
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        canal = await guild.create_text_channel("logs-rp-policial", category=category, overwrites=overwrites)
    return canal

async def enviar_log(tipo, user, staff, motivo, canal_tipo="rp", extra=""):
    guild = user.guild
    if canal_tipo == "ban": canal = await get_canal_punicao(guild, "ban")
    elif canal_tipo == "kick": canal = await get_canal_punicao(guild, "kick")
    elif canal_tipo == "warn": canal = await get_canal_punicao(guild, "warn")
    elif canal_tipo == "combatlog": canal = await get_canal_punicao(guild, "combatlog")
    else: canal = discord.utils.get(guild.channels, name="logs-rp")

    if canal:
        embed = discord.Embed(title=f"📝 LOG - {tipo}", color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="Jogador", value=user.mention, inline=True)
        embed.add_field(name="Staff", value=staff.mention if staff else "SISTEMA", inline=True)
        embed.add_field(name="Horário", value=datetime.now().strftime('%d/%m/%Y %H:%M'), inline=True)
        embed.add_field(name="Motivo", value=motivo[:1024], inline=False)
        if extra: embed.add_field(name="Detalhes", value=extra, inline=False)
        await canal.send(embed=embed)

async def enviar_log_policial(acao, policial_nome, alvo_nome, motivo, tempo):
    """Função que o Roblox vai chamar"""
    for guild in bot.guilds:
        canal = await get_canal_policial(guild)

        if acao == "prender":
            embed = discord.Embed(title="🚔 PRISÃO REALIZADA", color=0x0000ff, timestamp=discord.utils.utcnow())
            embed.add_field(name="Policial", value=policial_nome, inline=True)
            embed.add_field(name="Preso", value=alvo_nome, inline=True)
            embed.add_field(name="Tempo", value=tempo, inline=True)
            embed.add_field(name="Motivo", value=motivo, inline=False)

        elif acao == "multar":
            embed = discord.Embed(title="🎫 MULTA APLICADA", color=0xffff00, timestamp=discord.utils.utcnow())
            embed.add_field(name="Policial", value=policial_nome, inline=True)
            embed.add_field(name="Multado", value=alvo_nome, inline=True)
            embed.add_field(name="Valor", value=motivo.split('|')[0], inline=True)
            embed.add_field(name="Motivo", value=motivo.split('|')[1], inline=False)

        elif acao == "apreender_carro":
            embed = discord.Embed(title="🚗 CARRO APREENDIDO", color=0xff0000, timestamp=discord.utils.utcnow())
            embed.add_field(name="Policial", value=policial_nome, inline=True)
            embed.add_field(name="Dono", value=alvo_nome, inline=True)
            embed.add_field(name="Motivo", value=motivo, inline=False)

        await canal.send(embed=embed)

tickets_abertos = {}
respostas_ticket = {}

PERGUNTAS = [
    "1. Qual seu nome RP completo?", "2. Qual sua idade?", "3. Você leu todas as regras do servidor?",
    "4. O que é RP?", "5. O que é FailRP? Dê um exemplo", "6. O que é MetaGaming?", "7. O que é PowerGaming?",
    "8. Você já jogou em outro servidor de RP? Qual?", "9. Qual personagem você pretende fazer? Conte um pouco",
    "10. O que você faria se fosse abordado pela polícia?", "11. O que você faria se fosse assaltado?",
    "12. Você tem microfone e sabe falar no RP?", "13. Quantas horas por dia você pode jogar?",
    "14. Você promete não usar cheats/mods?", "15. Qual será seu Nick no Discord? Ex: João Silva",
    "16. Por que devemos te aceitar no servidor?"
]

CARGOS_RP = {"policia": "Policial", "medico": "Médico", "mecanico": "Mecânico", "taxista": "Taxista", "desempregado": "Desempregado"}
SALARIOS = {"Policial": 800, "Médico": 700, "Mecânico": 600, "Taxista": 400, "Desempregado": 100}

class WhitelistButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Fazer Whitelist", style=discord.ButtonStyle.green, emoji="✅", custom_id="whitelist_btn")
    async def whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if str(interaction.user.id) in tickets_abertos:
            await interaction.response.send_message("❌ Você já tem um ticket aberto!", ephemeral=True)
            return
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        category = discord.utils.get(guild.categories, name="WHITELIST")
        if not category: category = await guild.create_category("WHITELIST")
        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites, category=category)
        tickets_abertos[str(interaction.user.id)] = channel.id
        respostas_ticket[str(interaction.user.id)] = []
        await channel.send(f"{interaction.user.mention} Bem vindo! Responda a pergunta 1: **{PERGUNTAS[0]}**", view=TicketCloseView())
        await interaction.response.send_message(f"✅ Ticket criado: {channel.mention}", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles: return
        member = interaction.channel.members[1]
        await interaction.response.send_modal(MotivoModal(member, "aprovado"))
    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.red, emoji="❌")
    async def reprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles: return
        member = interaction.channel.members[1]
        await interaction.response.send_modal(MotivoModal(member, "reprovado"))

class MotivoModal(discord.ui.Modal):
    def __init__(self, member, tipo):
        super().__init__(title=f"Motivo da {tipo.title()}")
        self.member = member
        self.tipo = tipo
        self.motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, required=True, max_length=500)
        self.add_item(self.motivo)
    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(self.member.id)
        motivo_texto = self.motivo.value
        if self.tipo == "aprovado":
            role = discord.utils.get(interaction.guild.roles, name="Membro")
            if role: await self.member.add_roles(role)
            if user_id not in economia: economia[user_id] = {"carteira": 1000, "banco": 0, "ultimo_salario": 0}
            embed_dm = discord.Embed(title="✅ WHITELIST APROVADA", description="Parabéns! Você foi aprovado.", color=0x00ff00)
            embed_dm.add_field(name="Motivo", value=motivo_texto, inline=False)
            try: await self.member.send(embed=embed_dm)
            except: pass
            await enviar_log("WHITELIST APROVADA", self.member, interaction.user, motivo_texto, "rp")
            await interaction.response.send_message(f"✅ {self.member.mention} aprovado! DM enviada.", ephemeral=True)
        else:
            embed_dm = discord.Embed(title="❌ WHITELIST REPROVADA", description="Sua whitelist foi reprovada.", color=0xff0000)
            embed_dm.add_field(name="Motivo", value=motivo_texto, inline=False)
            try: await self.member.send(embed=embed_dm)
            except: pass
            await enviar_log("WHITELIST REPROVADA", self.member, interaction.user, motivo_texto, "rp")
            await interaction.response.send_message(f"❌ {self.member.mention} reprovado! DM enviada.", ephemeral=True)
        if user_id in tickets_abertos: del tickets_abertos[user_id]
        if user_id in respostas_ticket: del respostas_ticket[user_id]
        await interaction.channel.delete()

@bot.event
async def on_ready():
    print(f'{bot.user} Online 24h')
    bot.add_view(WhitelistButton())
    bot.add_view(TicketCloseView())

bot.run(os.getenv("TOKEN"))
