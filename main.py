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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

WEBHOOK_URL = ""
tickets_abertos = {}
respostas_ticket = {}

async def enviar_log(tipo, user, staff, motivo, canal="logs-rp"):
    canal_logs = discord.utils.get(bot.get_all_channels(), name=canal)
    if canal_logs:
        embed = discord.Embed(title=f"📝 LOG - {tipo}", color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="Jogador", value=user.mention, inline=True)
        embed.add_field(name="Staff", value=staff.mention if staff else "SISTEMA", inline=True)
        embed.add_field(name="Motivo", value=motivo[:1024], inline=False)
        await canal_logs.send(embed=embed)

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
    "15. Qual será seu Nick no Discord? Ex: João Silva",
    "16. Por que devemos te aceitar no servidor?"
]

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
        embed = discord.Embed(title="📋 FORMULÁRIO DE WHITELIST", description="Responda as 16 perguntas abaixo. 1 por mensagem", color=0x2b2d31)
        await channel.send(f"{interaction.user.mention} Bem vindo! Responda a pergunta 1: **{PERGUNTAS[0]}**", view=TicketCloseView())
        await interaction.response.send_message(f"✅ Ticket criado: {channel.mention}", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
            return
        member = interaction.channel.members[1]
        user_id = str(member.id)
        role = discord.utils.get(interaction.guild.roles, name="Membro")
        if role: await member.add_roles(role)
        if user_id in respostas_ticket and len(respostas_ticket[user_id]) >= 15:
            nick = respostas_ticket[user_id][14]
            try:
                await member.edit(nick=nick[:32])
                nick_msg = f"Nick alterado para: **{nick}**"
            except:
                nick_msg = "❌ Não consegui mudar o nick. Dê 'Gerenciar Apelidos' pro bot e coloque ele no topo."
        else:
            nick_msg = "⚠️ Nick não encontrado nas respostas"
        await enviar_log("WHITELIST", member, interaction.user, f"Aprovado. {nick_msg}", "logs-rp")
        await interaction.response.send_message(f"✅ {member.mention} foi aprovado!\n{nick_msg}")
        if user_id in tickets_abertos: del tickets_abertos[user_id]
        if user_id in respostas_ticket: del respostas_ticket[user_id]
        await interaction.channel.delete()
    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.red, emoji="❌")
    async def reprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.channel.members[1]
        user_id = str(member.id)
        await enviar_log("WHITELIST REPROVADA", member, interaction.user, "Reprovado", "logs-rp")
        await interaction.response.send_message(f"❌ {member.mention} foi reprovado.")
        if user_id in tickets_abertos: del tickets_abertos[user_id]
        if user_id in respostas_ticket: del respostas_ticket[user_id]
        await interaction.channel.delete()

@bot.event
async def on_ready():
    print(f'{bot.user} Online 24h')
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
                    await message.channel.send(f"✅ Anotado! Agora responda a pergunta {num + 1}: **{PERGUNTAS[num]}**")
                else:
                    await message.channel.send("✅ Todas as perguntas respondidas! Aguarde uma staff analisar.")
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    await enviar_log("MENSAGEM APAGADA", message.author, None, f'Canal: #{message.channel.name}', "logs")

@bot.event
async def on_member_update(before, after): # CORRIGIDO
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
    embed.add_field(name="!painelwhitelist", value="Cria o painel de whitelist", inline=False)
    embed.add_field(name="!logs rp", value="Cria canal de logs RP", inline=False)
    embed.add_field(name="!logs", value="Cria canal de logs geral", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def painelwhitelist(ctx):
    canal = discord.utils.get(ctx.guild.channels, name="whitelist")
    if not canal: canal = await ctx.guild.create_text_channel("whitelist")
    embed = discord.Embed(title="🎫 SISTEMA DE WHITELIST", description="Clique no botão abaixo para iniciar sua whitelist\n**ATENÇÃO:** São 16 perguntas. Responda 1 por vez.", color=0x00ff00)
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
