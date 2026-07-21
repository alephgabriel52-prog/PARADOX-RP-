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

async def enviar_log(guild, tipo, embed):
    canal_id = db.get(f"logs_{tipo}")
    if canal_id:
        canal = guild.get_channel(canal_id)
        if canal: await canal.send(embed=embed)

async def deletar_canal_vazio(categoria):
    if categoria and len(categoria.channels) == 0:
        await categoria.delete()

# ============ ANTI BOT ============
@bot.event
async def on_member_join(member):
    if member.bot and db["anti_bot"] and not member.public_flags.verified_bot:
        guild = member.guild
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
            if entry.target.id == member.id:
                invoker = entry.user
                break
        else: invoker = None
        perms = [p[0] for p in member.guild_permissions if p[1]]
        if invoker:
            mute_role = discord.utils.get(guild.roles, name="Mutado")
            if not mute_role: mute_role = await guild.create_role(name="Mutado", permissions=discord.Permissions(send_messages=False))
            await invoker.add_roles(mute_role)
            await asyncio.sleep(3600)
            await invoker.remove_roles(mute_role)
            await invoker.send(f"🚨 **PUNIÇÃO ANTI-BOT**\nVocê foi mutado por 1h por adicionar o bot não verificado: **{member.name}**")
        await member.kick(reason="Bot não verificado")
        embed = discord.Embed(title="🚨 ANTI-BOT ATIVADO", color=0xFF0000, timestamp=datetime.datetime.now())
        embed.add_field(name="Bot Expulso", value=f"{member.name}", inline=False)
        embed.add_field(name="Quem Adicionou", value=f"{invoker.mention if invoker else 'Não encontrado'}", inline=False)
        embed.add_field(name="Permissões", value=", ".join(perms[:10]) if perms else "Nenhuma", inline=False)
        await enviar_log(guild, "anti", embed)
        dono = await bot.fetch_user(DONO_ID)
        await dono.send(embed=embed)

@bot.command()
@is_dono()
async def painelanti(ctx):
    estado = "✅ ATIVADO" if db["anti_bot"] else "❌ DESATIVADO"
    embed = discord.Embed(title="🛡️ Painel Anti-Bot", description=f"Status: {estado}", color=0xFF0000)
    view = View()
    async def ativar(i): db["anti_bot"] = True; save(); await i.response.send_message("✅ Ativado", ephemeral=True)
    async def desativar(i): db["anti_bot"] = False; save(); await i.response.send_message("❌ Desativado", ephemeral=True)
    btn1 = Button(label="Ativar", style=discord.ButtonStyle.green); btn2 = Button(label="Desativar", style=discord.ButtonStyle.red)
    btn1.callback = ativar; btn2.callback = desativar
    view.add_item(btn1); view.add_item(btn2)
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

# ============ TICKET ATUALIZADO COM DM ============
class BotoesTicket(View):
    def __init__(self, dono_id, tipo): super().__init__(timeout=None); self.dono_id = dono_id; self.tipo = tipo
    @discord.ui.button(label="Assumir", style=discord.ButtonStyle.green, emoji="✅")
    async def assumir(self, interaction, button): await assumir_ticket(interaction, self.dono_id, self.tipo)
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, interaction, button): await fechar_ticket(interaction, self.dono_id, self.tipo)

class BotoesWL(View):
    def __init__(self, dono_id): super().__init__(timeout=None); self.dono_id = dono_id
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green, emoji="✅")
    async def aprovar(self, interaction, button): await aprovar_wl(interaction, self.dono_id, True)
    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.red, emoji="❌")
    async def reprovar(self, interaction, button): await aprovar_wl(interaction, self.dono_id, False)

async def assumir_ticket(interaction, dono_id, tipo):
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("❌ Só staff", ephemeral=True)
    key = f"{tipo}-{dono_id}" if tipo!= "WL" else f"wl-{dono_id}"
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
    try: await membro.send(f"✅ **TICKET ASSUMIDO**\nSeu ticket de **{tipo}** foi assumido por {interaction.user.mention}\nCanal: {canal.mention}")
    except: pass
    await interaction.response.send_message("✅ Assumido e DM enviada!", ephemeral=True)

async def aprovar_wl(interaction, dono_id, aprovado):
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("❌ Só staff", ephemeral=True)
    membro = interaction.guild.get_member(dono_id)
    canal = interaction.channel
    categoria = canal.category
    if aprovado:
        try: await membro.send(f"✅ **WL APROVADA**\nParabéns {membro.mention}! Você foi aprovado na WL da cidade.")
        except: pass
        await canal.send(f"✅ **APROVADO por {interaction.user.mention}**")
    else:
        try: await membro.send(f"❌ **WL REPROVADA**\n{membro.mention} sua WL foi reprovada.\nMotivo: Entre em contato com a staff para mais detalhes.")
        except: pass
        await canal.send(f"❌ **REPROVADO por {interaction.user.mention}**")
    await asyncio.sleep(3)
    await canal.delete()
    await deletar_canal_vazio(categoria)
    if f"wl-{dono_id}" in db["tickets"]: del db["tickets"][f"wl-{dono_id}"]
    save()

async def fechar_ticket(interaction, dono_id, tipo):
    key = f"{tipo}-{dono_id}" if tipo!= "WL" else f"wl-{dono_id}"
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles] and interaction.user.id!= dono_id:
        return await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
    membro = interaction.guild.get_member(dono_id)
    canal = interaction.channel
    categoria = canal.category
    try: await membro.send(f"🔒 **TICKET FECHADO**\nSeu ticket de **{tipo}** foi fechado por {interaction.user.mention}")
    except: pass
    if key in db["tickets"]: del db["tickets"][key]
    save()
    await interaction.response.send_message("🔒 Fechando em 3s...")
    await asyncio.sleep(3)
    await canal.delete()
    await deletar_canal_vazio(categoria)

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

# ============ PAINEIS ============
class PainelPrincipal(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Suporte", style=discord.ButtonStyle.blurple, emoji="🎫")
    async def suporte(self, i, b): await abrir_ticket(i, "Suporte")
    @discord.ui.button(label="Denuncia", style=discord.ButtonStyle.red, emoji="🚨")
    async def denuncia(self, i, b): await abrir_ticket(i, "Denuncia")

class PainelVIP(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="VIP Bronze", style=discord.ButtonStyle.secondary, emoji="🥉")
    async def bronze(self, i, b): await abrir_ticket(i, "VIP Bronze")
    @discord.ui.button(label="VIP Prata", style=discord.ButtonStyle.gray, emoji="🥈")
    async def prata(self, i, b): await abrir_ticket(i, "VIP Prata")
    @discord.ui.button(label="VIP Ouro", style=discord.ButtonStyle.green, emoji="🥇")
    async def ouro(self, i, b): await abrir_ticket(i, "VIP Ouro")

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

@bot.event
async def on_ready():
    bot.add_view(PainelPrincipal())
    bot.add_view(PainelVIP())
    print('✅ BOT V14 ONLINE')

bot.run(os.getenv("TOKEN"))
