import discord
from discord.ext import commands
import os
import json
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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

WEBHOOK_URL = "" # AQUI VAI A URL DO ROBLOX

async def enviar_log(tipo, user, staff, motivo):
    canal_logs = discord.utils.get(bot.get_all_channels(), name="logs-rp")
    if canal_logs:
        embed = discord.Embed(title=f"LOG RP - {tipo}", color=0xff0000)
        embed.add_field(name="Jogador", value=user.mention, inline=True)
        embed.add_field(name="Staff", value=staff.mention, inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        await canal_logs.send(embed=embed)
    
    # ENVIA PRO ROBLOX TAMBEM
    if WEBHOOK_URL != "":
        import requests
        data = {"tipo": tipo, "jogador": user.name, "staff": staff.name, "motivo": motivo}
        try: requests.post(WEBHOOK_URL, json=data)
        except: pass

@bot.event
async def on_ready():
    print(f'{bot.user} Online 24h')
    await bot.change_presence(activity=discord.Game(name="!comandos"))

@bot.command()
async def ping(ctx): 
    await ctx.send("Pong! Bot 24h ON")

@bot.command(name="comandos")
async def help_command(ctx):
    embed = discord.Embed(title="COMANDOS PARADOX RP", color=0x00ff00)
    embed.add_field(name="LOGS", value="`!logs` `!logs RP`", inline=False)
    embed.add_field(name="MODERACAO", value="`!ban` `!kick` `!mutar` `!whitelist`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def logs(ctx):
    await ctx.send("Use `!logs RP` para criar o sistema de logs do RP")

@bot.command()
@commands.has_permissions(administrator=True)
async def logsRP(ctx):
    guild = ctx.guild
    
    # CRIA CATEGORIA E CANAL DE LOGS
    category = await guild.create_category("LOGS RP")
    canal = await guild.create_text_channel("logs-rp", category=category)
    await canal.send("Canal de logs criado! Todas as acoes vao aparecer aqui")
    
    # GERA URL PRO ROBLOX STUDIO
    url = f"https://discord.com/api/webhooks/SEU_WEBHOOK_AQUI"
    
    embed = discord.Embed(title="SISTEMA DE LOGS ATIVADO", color=0x00ff00)
    embed.add_field(name="Canal criado", value=canal.mention, inline=False)
    embed.add_field(name="URL PARA ROBLOX STUDIO", value=f"```{url}```", inline=False)
    embed.add_field(name="Como usar", value="Copie essa URL e cole no Script do Roblox Studio. Todas as logs vao aparecer no jogo automaticamente.", inline=False)
    await ctx.send(embed=embed)
    await ctx.send("COPIE A URL ACIMA E MANDE PRO DEV DO ROBLOX")

class TicketButton(discord.ui.View):
    @discord.ui.button(label="ABRIR TICKET", style=discord.ButtonStyle.green, emoji="🎫")
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name="equipe staff")
        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}")
        await channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
        if role:
            await channel.set_permissions(role, view_channel=True, send_messages=True)
        await channel.send(f"{interaction.user.mention} {role.mention if role else ''} Ticket aberto!")
        await interaction.response.send_message("Ticket criado!", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def ticketsetup(ctx, cargo: discord.Role, canal: discord.TextChannel):
    embed = discord.Embed(title="CENTRAL DE SUPORTE PARADOX RP", description="Clique no botao abaixo para abrir um ticket", color=0x5865F2)
    await canal.send(embed=embed, view=TicketButton())
    await ctx.send(f"Painel criado no {canal.mention}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.ban(reason=reason)
    await enviar_log("BAN", member, ctx.author, reason)
    await ctx.send(f"{member.mention} foi banido. Motivo: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.kick(reason=reason)
    await enviar_log("KICK", member, ctx.author, reason)
    await ctx.send(f"{member.mention} foi expulso. Motivo: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def whitelist(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Membro")
    await member.add_roles(role)
    await enviar_log("WHITELIST", member, ctx.author, "Aprovado")
    await ctx.send(f"{member.mention} recebeu whitelist")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mutar(ctx, member: discord.Member, tempo: int, *, reason="Sem motivo"):
    role = discord.utils.get(ctx.guild.roles, name="Mutado")
    await member.add_roles(role)
    await enviar_log("MUTE", member, ctx.author, reason)
    await ctx.send(f"{member.mention} foi mutado por {tempo}min")

bot.run(os.getenv("TOKEN"))
