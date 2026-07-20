import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import os, json, asyncio, random
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

DONO_ID = 1438010935783460954
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"economia":{}, "warns":{}, "corps":{}, "hierarquia":{}, "tickets":{}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

def is_staff(guild, user):
    cargos_staff = ["👑 Alto Comando", "Admin", "Moderador", "Staff", "Comandante Geral PM"]
    return any(discord.utils.get(guild.roles, name=c) in user.roles for c in cargos_staff)

# ============ SISTEMA DE TICKET ============
class PainelTicket(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Suporte", style=discord.ButtonStyle.blurple, emoji="🎫")
    async def suporte(self, i, b):
        await criar_ticket(i, "suporte")

    @discord.ui.button(label="Denuncia", style=discord.ButtonStyle.danger, emoji="🚨")
    async def denuncia(self, i, b):
        await criar_ticket(i, "denuncia")

    @discord.ui.button(label="Whitelist", style=discord.ButtonStyle.green, emoji="✅")
    async def whitelist(self, i, b):
        await criar_ticket(i, "whitelist")

    @discord.ui.button(label="Loja VIP", style=discord.ButtonStyle.success, emoji="💎")
    async def loja(self, i, b):
        await criar_ticket(i, "loja")

class PainelStaffTicket(View):
    def __init__(self, dono_id):
        super().__init__(timeout=None)
        self.dono_id = dono_id

    @discord.ui.button(label="Assumir", style=discord.ButtonStyle.green, emoji="👮")
    async def assumir(self, i, b):
        if not is_staff(i.guild, i.user):
            return await i.response.send_message("❌ Só Staff pode assumir", ephemeral=True)

        channel = i.channel
        await channel.set_permissions(i.user, send_messages=True, view_channel=True)
        await channel.set_permissions(i.guild.default_role, send_messages=False)
        await channel.set_permissions(i.guild.get_member(self.dono_id), send_messages=True)

        db["tickets"][str(channel.id)] = {"dono": self.dono_id, "staff": i.user.id}
        save()

        await i.response.send_message(f"✅ Ticket assumido por {i.user.mention}", ephemeral=False)

    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, i, b):
        if not is_staff(i.guild, i.user):
            return await i.response.send_message("❌ Só Staff pode fechar", ephemeral=True)
        await i.response.send_message("⚠️ Fechando ticket em 5s...")
        await asyncio.sleep(5)
        await i.channel.delete()
        if str(i.channel.id) in db["tickets"]: del db["tickets"][str(i.channel.id)]; save()

async def criar_ticket(interaction, tipo):
    guild = interaction.guild
    user = interaction.user

    # 1 TICKET POR PESSOA
    for ch_id, data in db["tickets"].items():
        if data["dono"] == user.id:
            return await interaction.response.send_message("❌ Você já tem um ticket aberto. Feche ele primeiro.", ephemeral=True)

    category = discord.utils.get(guild.categories, name="🎫 TICKETS")
    if not category:
        category = await guild.create_category("🎫 TICKETS")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        discord.utils.get(guild.roles, name="Staff"): discord.PermissionOverwrite(view_channel=True),
        discord.utils.get(guild.roles, name="Admin"): discord.PermissionOverwrite(view_channel=True),
    }

    channel = await guild.create_text_channel(f"ticket-{user.name}", overwrites=overwrites, category=category)

    db["tickets"][str(channel.id)] = {"dono": user.id, "tipo": tipo, "staff": None}
    save()

    embed = discord.Embed(title=f"🎫 Ticket {tipo.upper()}", description=f"Olá {user.mention}\nUm Staff irá te atender em breve.", color=discord.Color.blue())
    await channel.send(content=user.mention, embed=embed, view=PainelStaffTicket(user.id))
    await interaction.response.send_message(f"✅ Ticket criado: {channel.mention}", ephemeral=True)

@bot.command()
@is_dono()
async def setupticket(ctx):
    embed = discord.Embed(title="🏠 Painel Principal", description="Clique no botão abaixo para abrir um ticket", color=discord.Color.purple())
    await ctx.send(embed=embed, view=PainelTicket())
    await ctx.send("✅ Painel de Ticket criado!")

# ============ SETUP COMPLETO + TICKET ============
@bot.command()
@is_dono()
async def setup(ctx, corp: str = "PM"):
    corp = corp.upper()
    await ctx.send(f"⚡ **INICIANDO SETUP DA {corp}**...")
    guild = ctx.guild

    for channel in guild.channels:
        try: await channel.delete()
        except: pass
        await asyncio.sleep(0.1)

    everyone = guild.default_role
    cargos_list = [
        "👑 Alto Comando", f"Comandante Geral {corp}", f"Coronel {corp}", f"Major {corp}", f"Capitão {corp}",
        f"Tenente {corp}", f"Sargento {corp}", f"Cabo {corp}", f"Soldado {corp}", f"Recruta {corp}",
        f"ROTAM {corp}", f"ROCAM {corp}", f"CHOQUE {corp}", f"TRÂNSITO {corp}",
        "Civil", "Staff", "Moderador", "Admin", "Mutado"
    ]

    roles = {}
    for nome in cargos_list:
        role = await guild.create_role(name=nome)
        roles[nome] = role

    await roles["👑 Alto Comando"].edit(permissions=discord.Permissions(administrator=True))
    await roles["Admin"].edit(permissions=discord.Permissions(administrator=True))
    await roles["Moderador"].edit(permissions=discord.Permissions(manage_messages=True, kick_members=True))
    await roles["Staff"].edit(permissions=discord.Permissions(manage_messages=True))
    await roles["Mutado"].edit(permissions=discord.Permissions(send_messages=False))

    db["hierarquia"] = {nome: i for i, nome in enumerate(cargos_list[:10])}; save()

    overw_corp = {everyone: discord.PermissionOverwrite(view_channel=False), roles[f"Recruta {corp}"]: discord.PermissionOverwrite(view_channel=True)}
    overw_civil = {everyone: discord.PermissionOverwrite(view_channel=True)}

    cat_corp = await guild.create_category(f"🚔 {corp}", overwrites=overw_corp)
    await guild.create_text_channel("📋│boletim", category=cat_corp)

    cat_ticket = await guild.create_category("🎫 TICKETS")
    await guild.create_text_channel("📢│painel-ticket", category=cat_ticket)

    cat_civil = await guild.create_category("👤 CIVIL", overwrites=overw_civil)
    await guild.create_text_channel("💬│geral", category=cat_civil)

    db["corps"][str(guild.id)] = corp; save()
    await ctx.send(f"✅ **SETUP CONCLUÍDO!**\nUse `!setupticket` no canal pra criar o painel")

# ============ COMANDOS SETSTAFF ============
@bot.command()
@is_dono()
async def setstaff(ctx, membro: discord.Member, *, cargo: str):
    cargo_obj = discord.utils.get(ctx.guild.roles, name=cargo)
    if not cargo_obj: return await ctx.send(f"❌ Cargo `{cargo}` não existe")
    await membro.add_roles(cargo_obj)
    await ctx.send(f"✅ {membro.mention} agora é **{cargo}**")

# ============ PAINEL STAFF ============
class PainelStaff(View):
    @discord.ui.button(label="PROMOVER", style=discord.ButtonStyle.green, emoji="📈")
    async def promover(self, i, b):
        if not is_staff(i.guild, i.user): return await i.response.send_message("❌ Sem permissão", ephemeral=True)
        await i.response.send_message("Use: `!promover @membro Cargo`", ephemeral=True)

@bot.command()
async def painelstaff(ctx):
    if not is_staff(ctx.guild, ctx.author): return await ctx.send("❌ Só Staff")
    embed = discord.Embed(title="👮 PAINEL STAFF", color=discord.Color.dark_blue())
    await ctx.send(embed=embed, view=PainelStaff())

# ============ HIERARQUIA ============
def tem_permissao_promover(cargo_nome):
    return any(x in cargo_nome for x in ["👑 Alto Comando", "Comandante", "Coronel", "Major", "Capitão"])

def pegar_maior_cargo(membro, corp):
    for role in membro.roles:
        if corp in role.name: return role.name
    return "Civil"

@bot.command()
async def promover(ctx, membro: discord.Member, *, cargo_novo: str):
    corp = db["corps"].get(str(ctx.guild.id), "PM")
    cargo_autor = pegar_maior_cargo(ctx.author, corp)
    if not tem_permissao_promover(cargo_autor): return await ctx.send("❌ Só Capitão pra cima")
    cargo_obj = discord.utils.get(ctx.guild.roles, name=cargo_novo)
    for c in membro.roles:
        if corp in c.name: await membro.remove_roles(c)
    await membro.add_roles(cargo_obj)
    await ctx.send(f"✅ {membro.mention} promovido para **{cargo_novo}**")

@bot.command()
async def exonerar(ctx, membro: discord.Member):
    corp = db["corps"].get(str(ctx.guild.id), "PM")
    cargo_autor = pegar_maior_cargo(ctx.author, corp)
    if not tem_permissao_promover(cargo_autor): return await ctx.send("❌ Só Capitão pra cima")
    for c in membro.roles:
        if corp in c.name: await membro.remove_roles(c)
    civil = discord.utils.get(ctx.guild.roles, name="Civil")
    await membro.add_roles(civil)
    await ctx.send(f"✅ {membro.mention} foi exonerado")

@bot.command()
async def ban(ctx, membro: discord.Member, *, motivo="Sem motivo"):
    if not is_staff(ctx.guild, ctx.author): return await ctx.send("❌ Sem permissão")
    await membro.ban(reason=motivo); await ctx.send(f"🔨 {membro.mention} banido")

for i in range(1, 401):
    def make_cmd(num):
        async def cmd(ctx): await ctx.send(f"✅!cmd{num} funcionando!")
        return cmd
    bot.add_command(commands.Command(make_cmd(i), name=f"cmd{i}"))

@bot.event
async def on_ready():
    print(f'✅ MASTER BOT ONLINE COM TICKET')
    bot.add_view(PainelTicket())

bot.run(os.getenv("TOKEN"))
