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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

WEBHOOK_URL = "" # COLE A URL DO ROBLOX AQUI DEPOIS

async def enviar_log(tipo, user, staff, motivo):
    canal_logs = discord.utils.get(bot.get_all_channels(), name="logs-rp")
    if canal_logs:
        embed = discord.Embed(title=f"📝 LOG RP - {tipo}", color=0xff0000)
        embed.add_field(name="Jogador", value=user.mention, inline=True)
        embed.add_field(name="Staff", value=staff.mention, inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await canal_logs.send(embed=embed)
    
    if WEBHOOK_URL != "":
        data = {"tipo": tipo, "jogador": user.name, "staff": staff.name, "motivo": motivo}
        try: requests.post(WEBHOOK_URL, json=data, timeout=3)
        except: pass

@bot.event
async def on_ready():
    print(f'{bot.user} Online 24h')

@bot.command(name="comandos")
async def help_command(ctx):
    embed = discord.Embed(title="COMANDOS PARADOX RP", color=0x00ff00)
    embed.add_field(name="LOGS", value="`!logs rp` - Cria categoria e canal de logs sozinho", inline=False)
    embed.add_field(name="MOD", value="`!ban` `!kick` `!mutar` `!whitelist`", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="logs")
@commands.has_permissions(administrator=True)
async def logs(ctx, tipo=None):
    if tipo and tipo.lower() == "rp":
        guild = ctx.guild
        
        # VERIFICA SE JA EXISTE
        category = discord.utils.get(guild.categories, name="LOGS RP")
        if not category:
            category = await guild.create_category("LOGS RP")
        
        canal = discord.utils.get(guild.channels, name="logs-rp")
        if not canal:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            canal = await guild.create_text_channel("logs-rp", category=category, overwrites=overwrites)
        
        await canal.send("✅ Sistema de logs ativado! Todas as acoes vao aparecer aqui")
        
        embed = discord.Embed(title="SISTEMA DE LOGS ATIVADO", color=0x00ff00)
        embed.add_field(name="Categoria", value=category.name, inline=True)
        embed.add_field(name="Canal", value=canal.mention, inline=True)
        embed.add_field(name="URL PARA ROBLOX STUDIO", value=f"```{WEBHOOK_URL if WEBHOOK_URL else 'COLE SUA URL AQUI NO CODIGO'}```", inline=False)
        embed.add_field(name="Proximo passo", value="Copie a URL acima e envie para o dev colocar no Roblox Studio", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Use `!logs rp` para criar o sistema de logs do RP")

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
    if role: await member.add_roles(role)
    await enviar_log("WHITELIST", member, ctx.author, "Aprovado")
    await ctx.send(f"✅ {member.mention} recebeu whitelist")

bot.run(os.getenv("TOKEN"))
