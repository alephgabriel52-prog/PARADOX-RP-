import discord
from discord.ext import commands
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
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

DONO_ID = 1438010935783460954 # SÓ VOCÊ
STAFF_ROLE_ID = 1528409545439969433
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"tickets":{}, "servidores_permitidos": []}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

# ============ ANTI ROUBO TOTAL ============
@bot.event
async def on_guild_join(guild):
    # Pega quem adicionou o bot pelo audit log
    inviter = None
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
        inviter = entry.user
    
    # Se não foi você que adicionou
    if not inviter or inviter.id != DONO_ID:
        dono_servidor = guild.owner
        
        # 1. XINGA O DONO DO SERVER NO PV
        try:
            embed = discord.Embed(title="🚨 BOT PRIVADO", 
            description=f"Eai otario\nEsse bot é PRIVADO e só meu dono pode adicionar.\nServidor: **{guild.name}**\nQuem tentou: {inviter.mention if inviter else 'Desconhecido'}\n\nTira esse bot daqui antes que eu te denuncie", 
            color=0xFF0000)
            await dono_servidor.send(embed=embed)
        except: pass
        
        # 2. XINGA QUEM ADICIONOU NO PV TAMBÉM
        if inviter and inviter.id != dono_servidor.id:
            try:
                await inviter.send(f"Seu rato, tira esse bot do servidor {guild.name} agora. Ele é só do meu dono {DONO_ID}")
            except: pass
        
        # 3. SAI DO SERVIDOR NA HORA
        await guild.leave()
        
        # 4. AVISA VOCÊ
        dono = await bot.fetch_user(DONO_ID)
        await dono.send(f"🚨 **ANTI ROUBO**\nTentaram adicionar o bot no server: **{guild.name}**\nDono: {dono_servidor}\nQuem adicionou: {inviter}\nJá saí e xinguei os 2")

# ============ COMANDO PRA LIBERAR NOVO SERVIDOR ============
@bot.command()
@is_dono()
async def liberar(ctx):
    """Libera esse servidor pra usar o bot"""
    if ctx.guild.id not in db["servidores_permitidos"]:
        db["servidores_permitidos"].append(ctx.guild.id)
        save()
        await ctx.send(f"✅ Servidor **{ctx.guild.name}** liberado pra usar o bot")
    else:
        await ctx.send("✅ Esse servidor já está liberado")

@bot.command()
@is_dono()
async def desliberar(ctx):
    """Remove esse servidor da lista"""
    if ctx.guild.id in db["servidores_permitidos"]:
        db["servidores_permitidos"].remove(ctx.guild.id)
        save()
        await ctx.send(f"❌ Servidor removido")
        await ctx.guild.leave()

@bot.check
async def check_servidor(ctx):
    # Bloqueia comandos se não for servidor liberado
    if ctx.guild.id not in db["servidores_permitidos"] and ctx.author.id != DONO_ID:
        return False
    return True

# ============ TICKET COM ASSUMIR ============
class PainelTicket(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Suporte", style=discord.ButtonStyle.blurple, emoji="🎫", custom_id="ticket_suporte")
    async def suporte(self, interaction: discord.Interaction, button: Button):
        await abrir_ticket(interaction, "Suporte")
    @discord.ui.button(label="Denuncia", style=discord.ButtonStyle.red, emoji="🚨", custom_id="ticket_denuncia")
    async def denuncia(self, interaction: discord.Interaction, button: Button):
        await abrir_ticket(interaction, "Denuncia")
    @discord.ui.button(label="Loja VIP", style=discord.ButtonStyle.green, emoji="💎", custom_id="ticket_loja")
    async def loja(self, interaction: discord.Interaction, button: Button):
        await abrir_ticket(interaction, "Loja VIP")

class BotoesTicket(View):
    def __init__(self, dono_id):
        super().__init__(timeout=None)
        self.dono_id = dono_id
    @discord.ui.button(label="Assumir", style=discord.ButtonStyle.green, emoji="✅", custom_id="assumir_ticket")
    async def assumir(self, interaction: discord.Interaction, button: Button):
        await assumir_ticket(interaction, self.dono_id)
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.red, emoji="🔒", custom_id="fechar_ticket")
    async def fechar(self, interaction: discord.Interaction, button: Button):
        await fechar_ticket(interaction, self.dono_id)

async def abrir_ticket(interaction, tipo):
    guild = interaction.guild
    user = interaction.user
    if str(user.id) in db["tickets"]:
        return await interaction.response.send_message("❌ Você já tem um ticket aberto!", ephemeral=True)
    categoria = discord.utils.get(guild.categories, name="🎫 TICKETS")
    if not categoria:
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
        categoria = await guild.create_category("🎫 TICKETS", overwrites=overwrites)
    staff_role = discord.utils.get(guild.roles, id=STAFF_ROLE_ID)
    overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), user: discord.PermissionOverwrite(view_channel=True, send_messages=True), staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
    canal = await guild.create_text_channel(f"{tipo.lower()}-{user.name}", category=categoria, overwrites=overwrites)
    db["tickets"][str(user.id)] = {"canal": canal.id, "staff": None}
    save()
    embed = discord.Embed(title=f"🎫 Ticket {tipo}", description=f"Olá {user.mention}\nAguarde um staff assumir seu ticket.", color=0x5865F2)
    await canal.send(embed=embed, view=BotoesTicket(user.id))
    await interaction.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

async def assumir_ticket(interaction, dono_id):
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("❌ Só staff pode assumir", ephemeral=True)
    ticket = db["tickets"].get(str(dono_id))
    if not ticket: return await interaction.response.send_message("❌ Ticket não encontrado", ephemeral=True)
    if ticket["staff"] is not None:
        staff = interaction.guild.get_member(ticket["staff"])
        return await interaction.response.send_message(f"❌ Já foi assumido por {staff.mention}", ephemeral=True)
    ticket["staff"] = interaction.user.id
    save()
    canal = interaction.guild.get_channel(ticket["canal"])
    staff_role = discord.utils.get(interaction.guild.roles, id=STAFF_ROLE_ID)
    await canal.set_permissions(staff_role, view_channel=True, send_messages=False)
    await canal.set_permissions(interaction.user, view_channel=True, send_messages=True)
    embed = discord.Embed(title="✅ Ticket Assumido", description=f"{interaction.user.mention} assumiu.\nSó você e {interaction.guild.get_member(dono_id).mention} podem falar.", color=0x00FF00)
    await canal.send(embed=embed)
    await interaction.response.send_message("✅ Assumido!", ephemeral=True)

async def fechar_ticket(interaction, dono_id):
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles] and interaction.user.id != dono_id:
        return await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
    if str(dono_id) in db["tickets"]:
        del db["tickets"][str(dono_id)]
        save()
    await interaction.response.send_message("🔒 Fechando em 5s...")
    await asyncio.sleep(5)
    await interaction.channel.delete()

@bot.command()
@is_dono()
async def painel(ctx):
    embed = discord.Embed(title="🏠 Painel Principal", description="Abra um ticket para atendimento", color=0x5865F2)
    await ctx.send(embed=embed, view=PainelTicket())
    await ctx.message.delete()

@bot.event
async def on_ready():
    bot.add_view(PainelTicket())
    print(f'✅ BOT ONLINE V10 - SÓ DONO PODE ADICIONAR')

bot.run(os.getenv("TOKEN"))
