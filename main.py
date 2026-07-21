import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import os, json, asyncio, datetime
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
STAFF_ROLE_ID = 1528409545439969433
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"tickets":{}, "servidores_permitidos": [], "logs": None, "logs_game": None, "logs_anti": None, "anti_bot": False}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

# ============ WL COM PAGINAS PQ SÓ ACEITA 5 PERGUNTAS ============
class ModalWL_Pag1(Modal, title="WL RP - Página 1/3"):
    def __init__(self): super().__init__()
    p1 = TextInput(label="1. Nome completo do personagem?", style=discord.TextStyle.short, required=True)
    p2 = TextInput(label="2. Idade e profissão?", style=discord.TextStyle.short, required=True)
    p3 = TextInput(label="3. História de vida. Min 5 linhas", style=discord.TextStyle.paragraph, required=True)
    p4 = TextInput(label="4. O que é RDM?", style=discord.TextStyle.short, required=True)
    p5 = TextInput(label="5. O que é VDM?", style=discord.TextStyle.short, required=True)
    async def on_submit(self, i): await i.response.send_modal(ModalWL_Pag2(self.children))

class ModalWL_Pag2(Modal, title="WL RP - Página 2/3"):
    def __init__(self, dados1): super().__init__(); self.dados1 = dados1
    p6 = TextInput(label="6. O que é Meta Gaming?", style=discord.TextStyle.short, required=True)
    p7 = TextInput(label="7. O que é Power Gaming?", style=discord.TextStyle.short, required=True)
    p8 = TextInput(label="8. Sendo assaltado, o que faz?", style=discord.TextStyle.paragraph, required=True)
    p9 = TextInput(label="9. Viu amigos fazendo RDM, o que faz?", style=discord.TextStyle.paragraph, required=True)
    p10 = TextInput(label="10. Viu staff abusando, o que faz?", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, i): await i.response.send_modal(ModalWL_Pag3(self.dados1, self.children))

class ModalWL_Pag3(Modal, title="WL RP - Página 3/3"):
    def __init__(self, dados1, dados2): super().__init__(); self.dados1 = dados1; self.dados2 = dados2
    p11 = TextInput(label="11. Descreva uma situação de RP", style=discord.TextStyle.paragraph, required=True)
    p12 = TextInput(label="12. Pode atirar sem motivo? Por que?", style=discord.TextStyle.short, required=True)
    p13 = TextInput(label="13. O que significa Fear RP?", style=discord.TextStyle.short, required=True)
    p14 = TextInput(label="14. Tem microfone? Vai usar?", style=discord.TextStyle.short, required=True)
    p15 = TextInput(label="15. Por que aprovar você?", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction):
        await interaction.response.send_message("✅ WL enviada! Aguarde análise.", ephemeral=True)
        guild = interaction.guild
        categoria = discord.utils.get(guild.categories, name="🎫 WHITELIST")
        if not categoria: categoria = await guild.create_category("🎫 WHITELIST")
        staff_role = discord.utils.get(guild.roles, id=STAFF_ROLE_ID)
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True), staff_role: discord.PermissionOverwrite(view_channel=True)}
        canal = await guild.create_text_channel(f"wl-{interaction.user.name}", category=categoria, overwrites=overwrites)
        db["tickets"][f"wl-{interaction.user.id}"] = {"canal": canal.id, "staff": None}
        save()
        tudo = list(self.dados1) + list(self.dados2) + list(self.children)
        respostas = "\n\n".join([f"**{i.label}**\n> {i.value}" for i in tudo])
        embed = discord.Embed(title=f"📋 WL de {interaction.user}", description=respostas, color=0x5865F2)
        await canal.send(content=f"{staff_role.mention}", embed=embed, view=BotoesWL(interaction.user.id))

class BotoesWL(View):
    def __init__(self, dono_id): super().__init__(timeout=None); self.dono_id = dono_id
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green, emoji="✅", custom_id="wl_aprovar")
    async def aprovar(self, interaction, button): await aprovar_wl(interaction, self.dono_id, True)
    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.red, emoji="❌", custom_id="wl_reprovar")
    async def reprovar(self, interaction, button): await aprovar_wl(interaction, self.dono_id, False)

class BotoesTicket(View):
    def __init__(self, dono_id, tipo): super().__init__(timeout=None); self.dono_id = dono_id; self.tipo = tipo
    @discord.ui.button(label="Assumir", style=discord.ButtonStyle.green, emoji="✅", custom_id="ticket_assumir")
    async def assumir(self, interaction, button): await assumir_ticket(interaction, self.dono_id, self.tipo)
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.red, emoji="🔒", custom_id="ticket_fechar")
    async def fechar(self, interaction, button): await fechar_ticket(interaction, self.dono_id, self.tipo)

class PainelPrincipal(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Suporte", style=discord.ButtonStyle.blurple, emoji="🎫", custom_id="painel_suporte")
    async def suporte(self, i, b): await abrir_ticket(i, "Suporte")
    @discord.ui.button(label="Denuncia", style=discord.ButtonStyle.red, emoji="🚨", custom_id="painel_denuncia")
    async def denuncia(self, i, b): await abrir_ticket(i, "Denuncia")

class PainelVIP(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="VIP Bronze", style=discord.ButtonStyle.secondary, emoji="🥉", custom_id="vip_bronze")
    async def bronze(self, i, b): await abrir_ticket(i, "VIP Bronze")
    @discord.ui.button(label="VIP Prata", style=discord.ButtonStyle.gray, emoji="🥈", custom_id="vip_prata")
    async def prata(self, i, b): await abrir_ticket(i, "VIP Prata")
    @discord.ui.button(label="VIP Ouro", style=discord.ButtonStyle.green, emoji="🥇", custom_id="vip_ouro")
    async def ouro(self, i, b): await abrir_ticket(i, "VIP Ouro")

class PainelWL(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Fazer WL", style=discord.ButtonStyle.green, emoji="📋", custom_id="painel_wl")
    async def fazerwl(self, interaction, button):
        if f"wl-{interaction.user.id}" in db["tickets"]:
            return await interaction.response.send_message("❌ Você já tem uma WL aberta!", ephemeral=True)
        await interaction.response.send_modal(ModalWL_Pag1())

async def abrir_ticket(interaction, tipo):
    key = f"{tipo}-{interaction.user.id}"
    if key in db["tickets"]:
        return await interaction.response.send_message("❌ Você já tem um ticket aberto desse tipo!", ephemeral=True)
    categoria = discord.utils.get(interaction.guild.categories, name=f"🎫 {tipo.upper()}")
    if not categoria: categoria = await interaction.guild.create_category(f"🎫 {tipo.upper()}")
    staff_role = discord.utils.get(interaction.guild.roles, id=STAFF_ROLE_ID)
    overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True), staff_role: discord.PermissionOverwrite(view_channel=True)}
    canal = await interaction.guild.create_text_channel(f"{tipo.lower()}-{interaction.user.name}", category=categoria, overwrites=overwrites)
    db["tickets"][key] = {"canal": canal.id, "staff": None}
    save()
    embed = discord.Embed(title=f"🎫 Ticket {tipo}", description=f"Olá {interaction.user.mention}\nAguarde um staff assumir.", color=0x5865F2)
    await canal.send(embed=embed, view=BotoesTicket(interaction.user.id, tipo))
    await interaction.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

async def assumir_ticket(interaction, dono_id, tipo):
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("❌ Só staff", ephemeral=True)
    key = f"{tipo}-{dono_id}"
    ticket = db["tickets"].get(key)
    if not ticket or ticket["staff"]: return await interaction.response.send_message("❌ Já foi assumido", ephemeral=True)
    ticket["staff"] = interaction.user.id
    save()
    canal = interaction.guild.get_channel(ticket["canal"])
    membro = interaction.guild.get_member(dono_id)
    await canal.set_permissions(interaction.guild.default_role, send_messages=False)
    await canal.set_permissions(interaction.user, send_messages=True)
    await canal.set_permissions(membro, send_messages=True)
    await canal.send(f"✅ **Assumido por {interaction.user.mention}**\n🔒 Só vocês 2 podem falar.")
    try: await membro.send(f"✅ **TICKET ASSUMIDO**\nSeu ticket de **{tipo}** foi assumido por {interaction.user.mention}")
    except: pass
    await interaction.response.send_message("✅ Assumido!", ephemeral=True)

async def aprovar_wl(interaction, dono_id, aprovado):
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("❌ Só staff", ephemeral=True)
    membro = interaction.guild.get_member(dono_id)
    canal = interaction.channel
    categoria = canal.category
    if aprovado:
        try: await membro.send(f"✅ **WL APROVADA**\nParabéns {membro.mention}! Você foi aprovado.")
        except: pass
        await canal.send(f"✅ **APROVADO por {interaction.user.mention}**")
    else:
        try: await membro.send(f"❌ **WL REPROVADA**\n{membro.mention} sua WL foi reprovada.")
        except: pass
        await canal.send(f"❌ **REPROVADO por {interaction.user.mention}**")
    await asyncio.sleep(3)
    await canal.delete()
    if categoria and len(categoria.channels) == 0: await categoria.delete()
    if f"wl-{dono_id}" in db["tickets"]: del db["tickets"][f"wl-{dono_id}"]
    save()

async def fechar_ticket(interaction, dono_id, tipo):
    key = f"{tipo}-{dono_id}"
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles] and interaction.user.id!= dono_id:
        return await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
    membro = interaction.guild.get_member(dono_id)
    canal = interaction.channel
    categoria = canal.category
    try: await membro.send(f"🔒 **TICKET FECHADO**\nSeu ticket de **{tipo}** foi fechado.")
    except: pass
    if key in db["tickets"]: del db["tickets"][key]
    save()
    await interaction.response.send_message("🔒 Fechando em 3s...")
    await asyncio.sleep(3)
    await canal.delete()
    if categoria and len(categoria.channels) == 0: await categoria.delete()

@bot.command()
@is_dono()
async def painel(ctx):
    await ctx.send(embed=discord.Embed(title="🏠 Painel Principal", description="Suporte e Denuncia", color=0x5865F2), view=PainelPrincipal())
    await ctx.message.delete()

@bot.command()
@is_dono()
async def painelloja(ctx):
    await ctx.send(embed=discord.Embed(title="💎 Painel Loja VIP", description="Escolha seu VIP", color=0xFFD700), view=PainelVIP())
    await ctx.message.delete()

@bot.command()
@is_dono()
async def painelwl(ctx):
    await ctx.send(embed=discord.Embed(title="📋 Painel WL", description="Clique para fazer sua Whitelist", color=0x5865F2), view=PainelWL())
    await ctx.message.delete()

@bot.event
async def on_ready():
    bot.add_view(PainelPrincipal())
    bot.add_view(PainelVIP())
    bot.add_view(PainelWL())
    print('✅ BOT V14.1 ONLINE')

bot.run(os.getenv("TOKEN"))
