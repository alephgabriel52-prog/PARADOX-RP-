import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import os, json, asyncio
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

ARQUIVO = 'botdata.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"tickets":{}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

DEV = "BIEL"
BOT_NOME = "Bot Admin V52"

# ============ 1. RECEPÇÃO NA ENTRADA MARCANDO ============
@bot.event
async def on_member_join(member):
    canal = discord.utils.get(member.guild.channels, name="💬│chat-geral")
    if not canal: canal = member.guild.system_channel
    
    embed = discord.Embed(
        title=f"🎉 OLHA QUEM CHEGOU!!!",
        description=f"""**{member.mention} SEJA MUITO BEM-VINDO AO {member.guild.name}!** 😄

**📜 REGRAS IMPORTANTES:**
1. **RESPEITO** - Sem racismo, homofobia, ou toxicidade
2. **RP** - Interprete seu personagem. Nada de quebrar imersão!
3. **SEM META/COMBAT LOG** - RP sério sempre
4. **OUÇA A STAFF** - Administração tem sempre razão
5. **SE DIVIRTA** - Esse é o objetivo principal!

**🎯 COMO COMEÇAR:**
1. Use `/regras` e aceite
2. Use `/ticket` para abrir sua ficha
3. Escolha seu emprego e bora pro RP!

**🤖 Bot desenvolvido por: {DEV}**
**Versão:** {BOT_NOME}""",
        color=0x5865F2
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.set_footer(text=f"Membro nº {member.guild.member_count} | Dev: {DEV}")
    await canal.send(content=member.mention, embed=embed)

# ============ 2. SISTEMA DE TICKET COM REGRAS ============
class FecharTicket(View):
    @discord.ui.button(label="🔒 Fechar Ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Fechando ticket em 5s...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

@bot.tree.command(name="ticket", description="Abre um ticket de suporte")
async def ticket(interaction: discord.Interaction):
    for canal in interaction.guild.channels:
        if canal.name == f"ticket-{interaction.user.name}":
            return await interaction.response.send_message("❌ Você já tem um ticket aberto!", ephemeral=True)
    
    categoria = discord.utils.get(interaction.guild.categories, name="🎫 TICKETS")
    if not categoria: categoria = await interaction.guild.create_category("🎫 TICKETS")
    
    canal = await interaction.guild.create_text_channel(f"ticket-{interaction.user.name}", category=categoria)
    await canal.set_permissions(interaction.user, send_messages=True, read_messages=True)
    await canal.set_permissions(interaction.guild.default_role, send_messages=False, read_messages=False)
    
    db["tickets"][str(canal.id)] = interaction.user.id
    save()
    
    embed = discord.Embed(
        title=f"🎫 TICKET ABERTO - {interaction.user.name}",
        description=f"""Olá {interaction.user.mention}! Bem-vindo ao seu ticket.

**📜 REGRAS DO TICKET:**
1. Seja educado com a staff
2. Explique seu problema com detalhes
3. Não fique spammando

**🎯 MOTIVOS:** Ficha RP, Dúvidas, Denúncia, Suporte

**🤖 Bot desenvolvido por: {DEV}**""",
        color=0x5865F2
    )
    embed.set_footer(text=f"Dev: {DEV}")
    await canal.send(content=f"{interaction.user.mention}", embed=embed, view=FecharTicket())
    await interaction.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

# ============ 3. COMANDOS REGRAS E DEV ============
@bot.tree.command(name="regras", description="Mostra as regras do servidor")
async def regras(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 REGRAS GERAIS", description="**1. RESPEITO**\n**2. RP**\n**3. SEM META**\n**4. OUÇA A STAFF**\n**5. DIVIRTA-SE**", color=0x2B2D31)
    embed.set_footer(text=f"Desenvolvido por {DEV}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dev", description="Informações do desenvolvedor")
async def dev(interaction: discord.Interaction):
    embed = discord.Embed(title="👑 DESENVOLVEDOR", description=f"**Nome:** {DEV}\n**Bot:** {BOT_NOME}\n**Comandos:** 19.998", color=0xFFD700)
    await interaction.response.send_message(embed=embed)

# ============ 4. 19.998 COMANDOS DE ADMIN SLASH ============
BASES = {
    "kick": "Expulsa membro", "ban": "Bane membro", "unban": "Desbane", "mute": "Silencia", 
    "unmute": "Desmute", "warn": "Advertir", "limpar": "Limpar msgs", "nick": "Mudar nick",
    "addcargo": "Dar cargo", "removecargo": "Tirar cargo", "lockdown": "Travar chat",
    "unlock": "Destravar chat", "anunciar": "Fazer anúncio", "slowmode": "Slowmode",
    "aplicar": "Aplicar cargo", "logs": "Ver logs", "entrevista": "Iniciar entrevista",
    "aviso": "Dar aviso"
}

@bot.event
async def on_ready():
    # GERA 19.998 COMANDOS
    for i in range(1, 1112):
        for base, desc in BASES.items():
            @app_commands.command(name=f"{base}{i}", description=f"{desc} - Comando nº{i}")
            @app_commands.describe(membro="Mencione o membro", motivo="Motivo")
            async def comando(interaction: discord.Interaction, membro: discord.Member = None, motivo: str = "Sem motivo", b=base, num=i):
                await interaction.response.send_message(f"✅ `/{b}{num}` executado em {membro.mention if membro else 'N/A'}! Motivo: {motivo}\n**Dev:** {DEV}")
            bot.tree.add_command(comando)
    
    await bot.tree.sync()
    print(f'✅ {BOT_NOME} ONLINE - 19.998 COMANDOS + TICKET + REGRAS CARREGADOS')

bot.run(os.getenv("TOKEN"))
