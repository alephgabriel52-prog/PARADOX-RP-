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

async def enviar_log(tipo, user, staff, motivo, canal_tipo="rp"):
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
            await self.member.add_roles(discord.utils.get(interaction.guild.roles, name="Membro"))
            if user_id not in economia: economia[user_id] = {"carteira": 1000, "banco": 0}
            salvar_tudo()
            try: await self.member.send(f"✅ APROVADO! Motivo: {self.motivo.value}")
            except: pass
            await enviar_log("WHITELIST APROVADA", self.member, interaction.user, self.motivo.value)
            await interaction.response.send_message(f"✅ {self.member.mention} aprovado!", ephemeral=True)
        else:
            try: await self.member.send(f"❌ REPROVADO! Motivo: {self.motivo.value}")
            except: pass
            await enviar_log("WHITELIST REPROVADA", self.member, interaction.user, self.motivo.value)
            await interaction.response.send_message(f"❌ {self.member.mention} reprovado!", ephemeral=True)
        del tickets_abertos[user_id]
        del respostas_ticket[user_id]
        await interaction.channel.delete()

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
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def painelwhitelist(ctx): # <-- COMANDO CORRETO
    canal = discord.utils.get(ctx.guild.channels, name="whitelist") or await ctx.guild.create_text_channel("whitelist")
    await canal.send(embed=discord.Embed(title="🎫 SISTEMA DE WHITELIST", description="Clique no botão abaixo", color=0x00ff00), view=WhitelistButton())
    await ctx.send(f"✅ Painel criado em {canal.mention}")

bot.run(os.getenv("TOKEN"))
