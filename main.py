import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, Select
import os, json, asyncio, datetime, random
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
except: db = {"tickets":{}, "servidores_permitidos": [], "anti_bot": False, "economia": {}, "cpf": {}, "bancos": {}, "empresas": {}, "inventario": {}, "casamento": {}, "xp": {}, "casas": {}, "carros": {}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

def is_staff():
    def predicate(ctx): return STAFF_ROLE_ID in [r.id for r in ctx.author.roles] or ctx.author.id == DONO_ID
    return commands.check(predicate)

# ============ SELECT MENU IGUAL DA PRINT ============
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Suporte Geral", description="Dúvidas sobre o servidor, regras ou funcionamento", emoji="✉️", value="Suporte Geral"),
            discord.SelectOption(label="Denunciar", description="Denuncie jogadores que estejam infringindo as regras", emoji="🔨", value="Denunciar"),
            discord.SelectOption(label="Criador(a) de Conteúdo", description="Solicite parceria, divulgação ou candidate-se", emoji="📸", value="Criador"),
            discord.SelectOption(label="Solicitar Set", description="Peça sets in-game e/ou cargos no Discord", emoji="💎", value="Solicitar Set"),
            discord.SelectOption(label="Assumir Corp/Fac", description="Demonstre interesse em liderar uma corporação", emoji="✅", value="Assumir Corp/Fac"),
        ]
        super().__init__(placeholder="🎫 Selecione uma categoria de atendimento...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await abrir_ticket(interaction, self.values[0])

class PainelTicket(View):
    def __init__(self): super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ============ HELP ATUALIZADO ============
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📜 LISTA DE COMANDOS - PARADOX BOT", color=0x5865F2)
    embed.add_field(name="🏠 Ticket", value="`!painel` `!painelloja` `!painelwl` `!painelanti`", inline=False)
    embed.add_field(name="🛡️ Moderação", value="`!banir` `!expulsar` `!mutar` `!desmutar` `!limpar` `!avisar`", inline=False)
    embed.add_field(name="💰 Economia", value="`!saldo` `!pix` `!depositar` `!sacar` `!trabalhar` `!loja` `!comprar` `!vender`", inline=False)
    embed.add_field(name="🎒 Inventário", value="`!inventario` `!daritem` `!usar`", inline=False)
    embed.add_field(name="💍 Social", value="`!casar @membro` `!divorciar` `!casamento`", inline=False)
    embed.add_field(name="🏠 Bens", value="`!comprarcasa` `!minhacasa` `!comprarcarro` `!meucarro`", inline=False)
    embed.add_field(name="📊 XP", value="`!rank` `!nivel`", inline=False)
    embed.add_field(name="📱 Outros", value="`!celular` `!criarcpf` `!meucpf` `!infoserver`", inline=False)
    embed.add_field(name="👑 Dev", value="`!servers` `!liberar` `!addsaldo`", inline=False)
    await ctx.send(embed=embed)

# ============ XP E NIVEL ============
@bot.event
async def on_message(message):
    if message.author.bot: return
    uid = str(message.author.id)
    db["xp"][uid] = db["xp"].get(uid, {"xp":0, "lvl":1})
    db["xp"][uid]["xp"] += random.randint(1,5)
    if db["xp"][uid]["xp"] >= db["xp"][uid]["lvl"] * 100:
        db["xp"][uid]["xp"] = 0
        db["xp"][uid]["lvl"] += 1
        await message.channel.send(f"🎉 {message.author.mention} subiu para o nível **{db['xp'][uid]['lvl']}**!")
        save()
    await bot.process_commands(message)

@bot.command()
async def nivel(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    data = db["xp"].get(str(membro.id), {"xp":0, "lvl":1})
    await ctx.send(f"📊 {membro.name} - Nível **{data['lvl']}** | XP: {data['xp']}/{data['lvl']*100}")

@bot.command()
async def rank(ctx):
    top = sorted(db["xp"].items(), key=lambda x: x[1]["lvl"], reverse=True)[:10]
    txt = "\n".join([f"{i+1}. <@{u}> - Nv {d['lvl']}" for i,(u,d) in enumerate(top)])
    await ctx.send(f"**🏆 TOP 10 NÍVEIS**\n{txt}")

# ============ TRABALHO E LOJA ============
LOJA = {"Celular": 500, "Arma": 2000, "Kit Reparos": 300}

@bot.command()
@commands.cooldown(1, 300, commands.BucketType.user)
async def trabalhar(ctx):
    ganho = random.randint(100, 500)
    db["economia"][str(ctx.author.id)] = db["economia"].get(str(ctx.author.id), 0) + ganho
    save()
    await ctx.send(f"✅ Você trabalhou e ganhou **R$ {ganho}**")

@bot.command()
async def loja(ctx):
    txt = "\n".join([f"**{k}** - R$ {v}" for k,v in LOJA.items()])
    await ctx.send(f"**🛒 LOJA**\n{txt}")

@bot.command()
async def comprar(ctx, item: str):
    if item not in LOJA: return await ctx.send("❌ Item não existe")
    preco = LOJA[item]
    if db["economia"].get(str(ctx.author.id), 0) < preco: return await ctx.send("❌ Saldo insuficiente")
    db["economia"][str(ctx.author.id)] -= preco
    db["inventario"][str(ctx.author.id)] = db["inventario"].get(str(ctx.author.id), [])
    db["inventario"][str(ctx.author.id)].append(item)
    save()
    await ctx.send(f"✅ Você comprou **{item}** por R$ {preco}")

@bot.command()
async def inventario(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    itens = db["inventario"].get(str(membro.id), [])
    await ctx.send(f"🎒 Inventário de {membro.name}: {', '.join(itens) if itens else 'Vazio'}")

# ============ CASAMENTO ============
@bot.command()
async def casar(ctx, membro: discord.Member):
    if str(ctx.author.id) in db["casamento"]: return await ctx.send("❌ Você já é casado")
    db["casamento"][str(ctx.author.id)] = str(membro.id)
    db["casamento"][str(membro.id)] = str(ctx.author.id)
    save()
    await ctx.send(f"💍 {ctx.author.mention} e {membro.mention} agora são casados!")

@bot.command()
async def divorciar(ctx):
    if str(ctx.author.id) not in db["casamento"]: return await ctx.send("❌ Você não é casado")
    parceiro = db["casamento"][str(ctx.author.id)]
    del db["casamento"][str(ctx.author.id)]
    del db["casamento"][parceiro]
    save()
    await ctx.send("💔 Divórcio realizado")

@bot.command()
async def casamento(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    parceiro = db["casamento"].get(str(membro.id))
    if not parceiro: return await ctx.send("❌ Não é casado")
    await ctx.send(f"💍 {membro.name} é casado com <@{parceiro}>")

# ============ CASAS E CARROS ============
@bot.command()
async def comprarcasa(ctx):
    preco = 50000
    if db["economia"].get(str(ctx.author.id), 0) < preco: return await ctx.send("❌ Precisa de R$ 50000")
    db["economia"][str(ctx.author.id)] -= preco
    db["casas"][str(ctx.author.id)] = "Casa Simples"
    save()
    await ctx.send("🏠 Você comprou uma Casa Simples!")

@bot.command()
async def minhascasa(ctx):
    casa = db["casas"].get(str(ctx.author.id))
    await ctx.send(f"🏠 Sua casa: {casa if casa else 'Não tem casa'}")

@bot.command()
async def comprarcarro(ctx):
    preco = 30000
    if db["economia"].get(str(ctx.author.id), 0) < preco: return await ctx.send("❌ Precisa de R$ 30000")
    db["economia"][str(ctx.author.id)] -= preco
    db["carros"][str(ctx.author.id)] = "Fusca"
    save()
    await ctx.send("🚗 Você comprou um Fusca!")

@bot.command()
async def meucarro(ctx):
    carro = db["carros"].get(str(ctx.author.id))
    await ctx.send(f"🚗 Seu carro: {carro if carro else 'Não tem carro'}")

# ============ CELULAR ============
@bot.command()
async def celular(ctx):
    if "Celular" not in db["inventario"].get(str(ctx.author.id), []):
        return await ctx.send("❌ Você não tem um celular. Compre na `!loja`")
    embed = discord.Embed(title="📱 Celular", description="`!pix` `!saldo`", color=0x5865F2)
    await ctx.send(embed=embed)

# ============ MODERACAO ============
@bot.command()
@is_staff()
async def banir(ctx, membro: discord.Member, *, motivo="Sem motivo"):
    await membro.ban(reason=motivo)
    await ctx.send(f"🔨 {membro.mention} foi banido. Motivo: {motivo}")

@bot.command()
@is_staff()
async def expulsar(ctx, membro: discord.Member, *, motivo="Sem motivo"):
    await membro.kick(reason=motivo)
    await ctx.send(f"👢 {membro.mention} foi expulso. Motivo: {motivo}")

@bot.command()
@is_staff()
async def mutar(ctx, membro: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Mutado")
    if not role: role = await ctx.guild.create_role(name="Mutado", permissions=discord.Permissions(send_messages=False))
    await membro.add_roles(role)
    await ctx.send(f"🔇 {membro.mention} foi mutado")

@bot.command()
@is_staff()
async def desmutar(ctx, membro: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Mutado")
    await membro.remove_roles(role)
    await ctx.send(f"🔊 {membro.mention} foi desmutado")

@bot.command()
@is_staff()
async def limpar(ctx, qtd: int):
    await ctx.channel.purge(limit=qtd+1)
    await ctx.send(f"✅ {qtd} mensagens apagadas", delete_after=3)

# ============ ECONOMIA BASICA ============
@bot.command()
async def saldo(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    valor = db["economia"].get(str(membro.id), 0)
    await ctx.send(f"💰 Saldo de {membro.mention}: **R$ {valor}**")

@bot.command()
async def pix(ctx, membro: discord.Member, valor: int):
    if valor <= 0: return await ctx.send("❌ Valor inválido")
    if db["economia"].get(str(ctx.author.id), 0) < valor: return await ctx.send("❌ Saldo insuficiente")
    db["economia"][str(ctx.author.id)] -= valor
    db["economia"][str(membro.id)] = db["economia"].get(str(membro.id), 0) + valor
    save()
    await ctx.send(f"✅ Pix de R$ {valor} para {membro.mention}")

@bot.command()
@is_dono()
async def addsaldo(ctx, membro: discord.Member, valor: int):
    db["economia"][str(membro.id)] = db["economia"].get(str(membro.id), 0) + valor
    save()
    await ctx.send(f"✅ Adicionado R$ {valor} para {membro.mention}")

# ============ CPF ============
@bot.command()
async def criarcpf(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    cpf = f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}"
    db["cpf"][str(membro.id)] = {"cpf": cpf, "nome": membro.name}
    save()
    await ctx.send(f"✅ CPF de {membro.mention}: `{cpf}`")

@bot.command()
async def meucpf(ctx):
    cpf = db["cpf"].get(str(ctx.author.id))
    if not cpf: return await ctx.send("❌ Você não tem CPF. Use!criarcpf")
    await ctx.send(f"Seu CPF: `{cpf['cpf']}`")

# ============ TICKETS + WL ============
class ModalWL_Pag1(Modal, title="WL RP - Página 1/3"):
    p1 = TextInput(label="1. Nome completo?", style=discord.TextStyle.short, required=True)
    p2 = TextInput(label="2. Idade e profissão?", style=discord.TextStyle.short, required=True)
    p3 = TextInput(label="3. História de vida", style=discord.TextStyle.paragraph, required=True)
    p4 = TextInput(label="4. O que é RDM?", style=discord.TextStyle.short, required=True)
    p5 = TextInput(label="5. O que é VDM?", style=discord.TextStyle.short, required=True)
    async def on_submit(self, i): await i.response.send_modal(ModalWL_Pag2(self.children))

class ModalWL_Pag2(Modal, title="WL RP - Página 2/3"):
    def __init__(self, d1): super().__init__(); self.d1 = d1
    p6 = TextInput(label="6. Meta Gaming?", style=discord.TextStyle.short, required=True)
    p7 = TextInput(label="7. Power Gaming?", style=discord.TextStyle.short, required=True)
    p8 = TextInput(label="8. Sendo assaltado?", style=discord.TextStyle.paragraph, required=True)
    p9 = TextInput(label="9. Viu RDM?", style=discord.TextStyle.paragraph, required=True)
    p10 = TextInput(label="10. Staff abusando?", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, i): await i.response.send_modal(ModalWL_Pag3(self.d1, self.children))

class ModalWL_Pag3(Modal, title="WL RP - Página 3/3"):
    def __init__(self, d1, d2): super().__init__(); self.d1 = d1; self.d2 = d2
    p11 = TextInput(label="11. Situação de RP", style=discord.TextStyle.paragraph, required=True)
    p12 = TextInput(label="12. Atirar sem motivo?", style=discord.TextStyle.short, required=True)
    p13 = TextInput(label="13. Fear RP?", style=discord.TextStyle.short, required=True)
    p14 = TextInput(label="14. Tem microfone?", style=discord.TextStyle.short, required=True)
    p15 = TextInput(label="15. Por que aprovar?", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction):
        await interaction.response.send_message("✅ WL enviada!", ephemeral=True)
        guild = interaction.guild; categoria = discord.utils.get(guild.categories, name="🎫 WHITELIST")
        if not categoria: categoria = await guild.create_category("🎫 WHITELIST")
        staff_role = discord.utils.get(guild.roles, id=STAFF_ROLE_ID)
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True), staff_role: discord.PermissionOverwrite(view_channel=True)}
        canal = await guild.create_text_channel(f"wl-{interaction.user.name}", category=categoria, overwrites=overwrites)
        db["tickets"][f"wl-{interaction.user.id}"] = {"canal": canal.id, "staff": None}; save()
        tudo = list(self.d1) + list(self.d2) + list(self.children)
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
    if key in db["tickets"]: return await interaction.response.send_message("❌ Você já tem um ticket aberto!", ephemeral=True)
    categoria = discord.utils.get(interaction.guild.categories, name=f"🎫 {tipo.upper()}")
    if not categoria: categoria = await interaction.guild.create_category(f"🎫 {tipo.upper()}")
    staff_role = discord.utils.get(interaction.guild.roles, id=STAFF_ROLE_ID)
    overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True), staff_role: discord.PermissionOverwrite(view_channel=True)}
    canal = await interaction.guild.create_text_channel(f"{tipo.lower()}-{interaction.user.name}", category=categoria, overwrites=overwrites)
    db["tickets"][key] = {"canal": canal.id, "staff": None}; save()
    embed = discord.Embed(title=f"🎫 Ticket {tipo}", description=f"Olá {interaction.user.mention}\nAguarde um staff assumir.", color=0x5865F2)
    await canal.send(embed=embed, view=BotoesTicket(interaction.user.id, tipo))
    await interaction.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

async def assumir_ticket(interaction, dono_id, tipo):
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]: return await interaction.response.send_message("❌ Só staff", ephemeral=True)
    key = f"{tipo}-{dono_id}"
    ticket = db["tickets"].get(key)
    if not ticket or ticket["staff"]: return await interaction.response.send_message("❌ Já foi assumido", ephemeral=True)
    ticket["staff"] = interaction.user.id; save()
    canal = interaction.guild.get_channel(ticket["canal"]); membro = interaction.guild.get_member(dono_id)
    await canal.set_permissions(interaction.guild.default_role, send_messages=False)
    await canal.set_permissions(interaction.user, send_messages=True); await canal.set_permissions(membro, send_messages=True)
    await canal.send(f"✅ **Assumido por {interaction.user.mention}**\n🔒 Só vocês 2 podem falar.")
    try: await membro.send(f"✅ **TICKET ASSUMIDO**\nSeu ticket de **{tipo}** foi assumido por {interaction.user.mention}")
    except: pass
    await interaction.response.send_message("✅ Assumido!", ephemeral=True)

async def aprovar_wl(interaction, dono_id, aprovado):
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]: return await interaction.response.send_message("❌ Só staff", ephemeral=True)
    membro = interaction.guild.get_member(dono_id); canal = interaction.channel; categoria = canal.category
    if aprovado:
        try: await membro.send(f"✅ **WL APROVADA**\nParabéns {membro.mention}! Você foi aprovado.")
        except: pass
        await canal.send(f"✅ **APROVADO por {interaction.user.mention}**")
    else:
        try: await membro.send(f"❌ **WL REPROVADA**\n{membro.mention} sua WL foi reprovada.")
        except: pass
        await canal.send(f"❌ **REPROVADO por {interaction.user.mention}**")
    await asyncio.sleep(3); await canal.delete()
    if categoria and len(categoria.channels) == 0: await categoria.delete()
    if f"wl-{dono_id}" in db["tickets"]: del db["tickets"][f"wl-{dono_id}"]; save()

async def fechar_ticket(interaction, dono_id, tipo):
    key = f"{tipo}-{dono_id}"
    if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles] and interaction.user.id!= dono_id:
        return await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
    membro = interaction.guild.get_member(dono_id); canal = interaction.channel; categoria = canal.category
    try: await membro.send(f"🔒 **TICKET FECHADO**\nSeu ticket de **{tipo}** foi fechado.")
    except: pass
    if key in db["tickets"]: del db["tickets"][key]; save()
    await interaction.response.send_message("🔒 Fechando em 3s...")
    await asyncio.sleep(3); await canal.delete()
    if categoria and len(categoria.channels) == 0: await categoria.delete()

@bot.command()
@is_dono()
async def painel(ctx):
    embed = discord.Embed(
        title="🎫 Suporte & Atendimento",
        description="""Oiii! Precisando de uma força? Você chegou no lugar certo.
Aqui nossa equipe cuida de cada atendimento com calma e atenção.

**Como funciona:**
Escolha ali embaixo a categoria que mais combina com o seu caso e a gente já abre um canal só seu para resolvermos.

-----------------------------

🕐 **Dias Úteis**
Segunda a Sexta
12:00h às 23:00h

📅 **Fins de Semana**
Sábados, Domingos e Feriados
12:00h às 18:00h

⚡ **Tempo de Resposta**
Até 2h úteis""",
        color=0x5865F2
    )
    await ctx.send(embed=embed, view=PainelTicket())
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
    bot.add_view(PainelTicket()); bot.add_view(PainelVIP()); bot.add_view(PainelWL())
    await bot.change_presence(activity=discord.Game(name="Use!help"))
    print('✅ BOT V18.1 ONLINE SEM ERRO')

bot.run(os.getenv("TOKEN"))
