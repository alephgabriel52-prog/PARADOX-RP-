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

WEBHOOK_URL = "" # COLE A URL DO ROBLOX AQUI DEPOIS

async def enviar_log(tipo, user, staff, motivo):
    canal_logs = discord.utils.get(bot.get_all_channels(), name="logs-rp")
    if canal_logs:
        embed = discord.Embed(title=f"📝 LOG RP - {tipo}", color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="Jogador", value=user.mention, inline=True)
        embed.add_field(name="Staff", value=staff.mention, inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        await canal_logs.send(embed=embed)
    
    if WEBHOOK_URL != "":
        data = {"tipo": tipo, "jogador": str(user), "staff": str(staff), "motivo": motivo}
        try: requests.post(WEBHOOK_URL, json=data, timeout=3)
        except: print("Erro ao enviar pro Roblox")

@bot.event
async def on_ready():
    print(f'{bot.user} Online 24h')

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    print(f"[DEBUG] Mensagem recebida: {message.content}") # PRA VER NO LOG DO RENDER
    await bot.process_commands(message)

@bot.command()
async def comandos(ctx):
    embed = discord.Embed(title="📜 COMANDOS RP", color=0x5865F2)
    embed.add_field(name="!ban @user motivo", value="Bane o jogador", inline=False)
    embed.add_field(name="!kick @user motivo", value="Expulsa o jogador", inline=False)
    embed.add_field(name="!whitelist @user", value="Dá cargo Membro", inline=False)
    embed.add_field(name="!logs rp", value="Cria o sistema de logs", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="logs")
@commands.has_permissions(administrator=True)
async def logs(ctx, tipo=None):
    if tipo and tipo.lower() == "rp":
        guild = ctx.guild
        category = discord.utils.get(guild.categories, name="LOGS RP")
        if not category: category = await guild.create_category("LOGS RP")
        
        canal = discord.utils.get(guild.channels, name="logs-rp")
        if not canal:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            canal = await guild.create_text_channel("logs-rp", category=category, overwrites=overwrites)
        
        await canal.send("✅ Sistema de logs ativado!")
        await ctx.send(f"✅ Logs criados: {canal.mention}")
    else:
        await ctx.send("Use `!logs rp`")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.ban(reason=reason)
    await enviar_log("BAN", member, ctx.author, reason)
    await ctx.send(f"🔨 {member.mention} foi banido. Motivo: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.kick(reason=reason)
    await enviar_log("KICK", member, ctx.author, reason)
    await ctx.send(f"👢 {member.mention} foi expulso. Motivo: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def whitelist(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Membro")
    if not role: 
        await ctx.send("❌ Crie um cargo chamado `Membro` primeiro")
        return
    await member.add_roles(role)
    await enviar_log("WHITELIST", member, ctx.author, "Aprovado")
    await ctx.send(f"✅ {member.mention} recebeu whitelist")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão pra usar esse comando")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Marque um membro válido: `!ban @usuario`")
    else:
        print(error)

bot.run(os.getenv("TOKEN"))
