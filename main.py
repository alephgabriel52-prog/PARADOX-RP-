import discord
from discord.ext import commands
import os
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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None) # DESATIVEI O HELP PADRAO

@bot.event
async def on_ready():
    print(f'{bot.user} Online 24h')
    await bot.change_presence(activity=discord.Game(name="!comandos"))

@bot.command()
async def ping(ctx): 
    await ctx.send("Pong! Bot 24h ON")

@bot.command(name="comandos") # MUDEI DE help PARA comandos
async def help_command(ctx):
    embed = discord.Embed(title="COMANDOS PARADOX RP", color=0x00ff00)
    embed.add_field(name="!ping", value="Testa se o bot ta online", inline=False)
    embed.add_field(name="!ticketsetup @cargo #canal", value="Cria painel de ticket", inline=False)
    embed.add_field(name="!ban @user motivo", value="Bane usuario", inline=False)
    embed.add_field(name="!kick @user motivo", value="Expulsa usuario", inline=False)
    embed.add_field(name="!clear 10", value="Apaga mensagens", inline=False)
    await ctx.send(embed=embed)

class TicketButton(discord.ui.View):
    @discord.ui.button(label="ABRIR TICKET", style=discord.ButtonStyle.green, emoji="🎫")
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name="equipe staff")
        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}")
        await channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
        if role:
            await channel.set_permissions(role, view_channel=True, send_messages=True)
        await channel.send(f"{interaction.user.mention} {role.mention if role else ''} Ticket aberto! Aguarde a equipe staff")
        await interaction.response.send_message("Ticket criado! Verifique seu canal", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def ticketsetup(ctx, cargo: discord.Role, canal: discord.TextChannel):
    embed = discord.Embed(title="CENTRAL DE SUPORTE PARADOX RP", description="Clique no botao abaixo para abrir um ticket e falar com a equipe staff", color=0x5865F2)
    await canal.send(embed=embed, view=TicketButton())
    await ctx.send(f"Painel criado no {canal.mention}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} foi expulso. Motivo: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} foi banido. Motivo: {reason}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"Apaguei {amount} mensagens", delete_after=3)

bot.run(os.getenv("TOKEN"))
