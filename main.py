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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

DONO_ID = 1438010935783460954 # SEU ID
STAFF_ROLE_ID = 1528409545439969433 # ID DO CARGO EQUIPE STAFF
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"tickets":{}, "servidores_permitidos": []}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

# ============ TEMPLATES CORP ============
TEMPLATES = {
    "PM": ["Recruta", "Soldado", "Cabo", "Sargento", "Subtenente", "Tenente", "Capitão", "Major", "Coronel"],
    "PC": ["Estagiario", "Agente", "Escrivao", "Investigador", "Delegado"],
    "BOPE": ["Recruta", "Soldado", "Cabo", "Sargento", "Tenente", "Capitao"],
    "RP": ["Recruta", "Soldado", "Cabo", "Sargento", "Tenente", "Capitao"]
}
DIVISOES = ["ROTAM", "ROCAM", "GATE", "CHOQUE"]

# ============ ANTI ROUBO DE SERVIDOR ============
@bot.event
async def on_guild_join(guild):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
        inviter = entry.user
    if not inviter or inviter.id!= DONO_ID:
        try:
            await guild.owner.send(f"🚨 BOT PRIVADO\nSeu merda, esse bot é só do meu dono {DONO_ID}\nServidor: **{guild.name}**\nTira esse bot daqui")
        except: pass
        await guild.leave()
        dono = await bot.fetch_user(DONO_ID)
        await dono.send(f"🚨 **ANTI ROUBO**\nTentaram add no: **{guild.name}**\nJá saí e xinguei")

@bot.command()
@is_dono()
async def liberar(ctx):
    if ctx.guild.id not in db["servidores_permitidos"]:
        db["servidores_permitidos"].append(ctx.guild.id)
        save()
        await ctx.send(f"✅ Servidor **{ctx.guild.name}** liberado")

@bot.check
async def check_servidor(ctx):
    if ctx.guild.id not in db["servidores_permitidos"] and ctx.author.id!= DONO_ID:
        return False
    return True

# ============ SETUP CORP ============
@bot.command()
@is_dono()
async def setup(ctx, corp: str = "PM"):
    try:
        corp = corp.upper()
        if corp not in TEMPLATES:
            return await ctx.send("❌ Orgs: PM, PC, BOPE, RP")
        
        msg = await ctx.send(f"⚡ **INICIANDO SETUP DA {corp}**... Aguarde 1 min")
        guild = ctx.guild

        cargos_list = ["👑 Alto Comando", "DEV", "Equipe Staff", "Civil", "Staff", "Moderador", "Admin", "Mutado"]
        for patente in TEMPLATES[corp]:
            cargos_list.append(f"{patente} {corp}")
        for div in DIVISOES:
            cargos_list.append(f"{div} {corp}")

        roles = {}
        for nome in cargos_list:
            role = discord.utils.get(guild.roles, name=nome)
            if not role:
                role = await guild.create_role(name=nome)
                await asyncio.sleep(0.6) # Anti 429
            roles[nome] = role

        categoria = discord.utils.get(guild.categories, name=f"🏛️ {corp}")
        if not categoria: categoria = await guild.create_category(f"🏛️ {corp}")

        await msg.edit(content=f"✅ **SETUP DA {corp} CONCLUÍDO!** {len(cargos_list)} cargos criados")
    except Exception as e:
        await ctx.send(f"❌ ERRO NO SETUP: {e}")

# ============ PAINEIS ============
@bot.command()
@is_dono()
async def paineldono(ctx):
    embed = discord.Embed(title="👑 Painel do Dono", description="Controle total", color=0xFFD700)
    await ctx.author.send(embed=embed)
    await ctx.send("✅ Te mandei o painel no PV")

@bot.command()
async def painelstaff(ctx):
    if STAFF_ROLE_ID not in [r.id for r in ctx.author.roles]:
        return await ctx.send("❌ Você não tem permissão. Só quem tem `Equipe Staff` pode usar.")
    embed = discord.Embed(title="🛡️ Painel Staff", description="Painel da equipe", color=0x00FF00)
    await ctx.author.send(embed=embed)
    await ctx.send("✅ Te mandei o painel no PV")

# ============ TICKET ============
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
    embed = discord.Embed(title=f"🎫 Ticket {tipo}", description=f"Olá {user.mention}\nAguarde um staff assumir.", color=0x5865F2)
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
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles] and interaction.user.id!= dono_id:
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
    embed = discord.Embed(title="🏠 Painel Principal", description="Abra um ticket", color=0x5865F2)
    await ctx.send(embed=embed, view=PainelTicket())
    await ctx.message.delete()

@bot.command()
@is_dono()
async def setstaff(ctx, membro: discord.Member, *, cargo_nome):
    cargo = discord.utils.get(ctx.guild.roles, name=cargo_nome)
    if not cargo: cargo = await ctx.guild.create_role(name=cargo_nome)
    await membro.add_roles(cargo)
    await ctx.send(f"✅ {membro.mention} recebeu o cargo `{cargo_nome}`")

@bot.event
async def on_ready():
    bot.add_view(PainelTicket())
    print(f'✅ BOT ONLINE V10.1 PRONTO')

bot.run(os.getenv("TOKEN"))
