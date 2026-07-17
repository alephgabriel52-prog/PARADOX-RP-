import discord
from discord.ext import commands
import os
import requests
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
intents.message_history = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

WEBHOOK_URL = ""
tickets_abertos = {}

async def enviar_log(tipo, user, staff, motivo, canal="logs-rp"):
    canal_logs = discord.utils.get(bot.get_all_channels(), name=canal)
    if canal_logs:
        embed = discord.Embed(title=f"📝 LOG - {tipo}", color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="Jogador", value=user.mention, inline=True)
        embed.add_field(name="Staff", value=staff.mention if staff else "SISTEMA", inline=True)
        embed.add_field(name="Motivo", value=motivo[:1024], inline=False)
        await canal_logs.send(embed=embed)
    if WEBHOOK_URL!= "":
        data = {"tipo": tipo, "jogador": str(user), "staff": str(staff), "motivo": motivo}
        try: requests.post(WEBHOOK_URL, json=data, timeout=3)
        except: pass

# 15 PERGUNTAS DA WHITELIST
PERGUNTAS = [
    "1. Qual seu nome RP completo?",
    "2. Qual sua idade?",
    "3. Você leu todas as regras do servidor?",
    "4. O que é RP?",
    "5. O que é FailRP? Dê um exemplo",
    "6. O que é MetaGaming?",
    "7. O que é PowerGaming?",
    "8. Você já jogou em outro servidor de RP? Qual?",
    "9. Qual personagem você pretende fazer? Conte um pouco",
    "10. O que você faria se fosse abordado pela polícia?",
    "11. O que você faria se fosse assaltado?",
    "12. Você tem microfone e sabe falar no RP?",
    "13. Quantas horas por dia você pode jogar?",
    "14. Você promete não usar cheats/mods?",
    "15. Por que devemos te aceitar no servidor?"
]

# BOTÃO DO PAINEL
class WhitelistButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fazer Whitelist", style=discord.ButtonStyle.green, emoji="✅", custom_id="whitelist_btn")
    async def whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if str(interaction.user.id) in tickets_abertos:
            await interaction.response.send_message("❌ Você já tem um ticket aberto!", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        category = discord.utils.get(guild.categories, name="WHITELIST")
        if not category: category = await guild.create_category("WHITELIST")

        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites, category=category)
        tickets_abertos[str(interaction.user.id)] = channel.id

        embed = discord.Embed(title="📋 FORMULÁRIO DE WHITELIST", description="Responda as 15 perguntas abaixo. Seja detalhado!", color=0x2b2d31)
        for i, p in enumerate(PERGUNTAS):
            embed.add_field(name=p, value="Responda aqui embaixo ↓", inline=False)

        view = TicketCloseView()
        await channel.send(f"{interaction.user.mention}", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket criado: {channel.mention}", ephemeral=True)

# BOTÃO DE FECHAR/APROVAR TICKET
class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
            return
        member = interaction.channel.members[1]
        role = discord.utils.get(interaction.guild.roles, name="Membro")
        if role: await member.add_roles(role)
        await enviar_log("WHITELIST", member, interaction.user, "Aprovado via Ticket com 15 perguntas", "logs-rp")
        await interaction.response.send_message(f"✅ {member.mention} foi aprovado e recebeu whitelist!")
        for k,v in tickets_abertos.items():
            if v == interaction.channel.id: del tickets_abertos[k]; break
        await interaction.channel.delete()

    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.red, emoji="❌")
    async def reprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
            return
        member = interaction.channel.members[1]
        await enviar_log("WHITELIST REPROVADA", member, interaction.user, "Reprovado via Ticket", "logs-rp")
        await interaction.response.send_message(f"❌ {member.mention} foi reprovado.")
        for k,v in tickets_abertos.items():
            if v == interaction.channel.id: del tickets_abertos[k]; break
        await interaction.channel.delete()

@bot.event
async def on_ready():
    print(f'{bot.user} Online 24h')
    bot.add_view(WhitelistButton())
    bot.add_view(TicketCloseView())

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    await enviar_log("MENSAGEM APAGADA", message.author, None, f'Canal: #{message.channel.name} | {message.content[:500]}', "logs")

@bot.event
async asyncon_member_update(before, after):
    if before.roles!= after.roles:
        await enviar_log("CARGO ALTERADO", after, None, "Cargos modificados", "logs")
        try:
            await after.edit(roles=[])
            await after.send("tá me tirando")
        except: pass

@bot.command()
async def comandos(ctx):
    embed = discord.Embed(title="📜 COMANDOS", color=0x5865F2)
    embed.add_field(name="!ban @user motivo", value="Bane o jogador", inline=False)
    embed.add_field(name="!kick @user motivo", value="Expulsa o jogador", inline=False)
    embed.add_field(name="!painelwhitelist", value="Cria o painel de whitelist com 15 perguntas", inline=False)
    embed.add_field(name="!logs rp", value="Cria canal de logs RP", inline=False)
    embed.add_field(name="!logs", value="Cria canal de logs anti-sabotagem", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def painelwhitelist(ctx):
    canal = discord.utils.get(ctx.guild.channels, name="whitelist")
    if not canal: canal = await ctx.guild.create_text_channel("whitelist")
    embed = discord.Embed(title="🎫 SISTEMA DE WHITELIST", description="Clique no botão abaixo para iniciar sua whitelist\n\n**ATENÇÃO:** São 15 perguntas. Responda com calma!", color=0x00ff00)
    await canal.send(embed=embed, view=WhitelistButton())
    await ctx.send(f"✅ Painel criado em {canal.mention}")

@bot.command(name="logs")
@commands.has_permissions(administrator=True)
async def logs(ctx, tipo=None):
    guild = ctx.guild
    if tipo and tipo.lower() == "rp": nome_cat, nome_canal = "LOGS RP", "logs-rp"
    else: nome_cat, nome_canal = "LOGS", "logs"
    category = discord.utils.get(guild.categories, name=nome_cat)
    if not category: category = await guild.create_category(nome_cat)
    canal = discord.utils.get(guild.channels, name=nome_canal)
    if not canal:
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        canal = await guild.create_text_channel(nome_canal, category=category, overwrites=overwrites)
    await canal.send("✅ Sistema de logs ativado!")
    await ctx.send(f"✅ Logs criados: {canal.mention}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.ban(reason=reason)
    await enviar_log("BAN", member, ctx.author, reason, "logs-rp")
    await ctx.send(f"🔨 {member.mention} foi banido. Motivo: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.kick(reason=reason)
    await enviar_log("KICK", member, ctx.author, reason, "logs-rp")
    await ctx.send(f"👢 {member.mention} foi expulso. Motivo: {reason}")

bot.run(os.getenv("TOKEN"))
