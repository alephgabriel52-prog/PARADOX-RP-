import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
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

@bot.event
async def on_ready():
    print(f'✅ BOT ONLINE: {bot.user}')

DONO_ID = 1438010935783460954
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"corps":{}, "tickets":{}, "portes":{}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

def is_comando(guild, user, org):
    cargos_comando = [f"👑 Alto Comando", f"Comandante Geral {org}", f"Dono {org}"]
    return any(discord.utils.get(guild.roles, name=c) in user.roles for c in cargos_comando)

def pode_fazer_porte(guild, user):
    cargos_delegado = ["Delegado PC", "Delegado Titular PC", "Delegado Geral PC", "Chefe de Polícia"]
    return any(discord.utils.get(guild.roles, name=c) in user.roles for c in cargos_delegado)

class PorteModal(Modal, title="Emitir Porte de Arma - PC"):
    nome = TextInput(label="Nome do Civil", required=True)
    cpf = TextInput(label="CPF/RG", required=True)
    motivo = TextInput(label="Motivo", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        if not pode_fazer_porte(interaction.guild, interaction.user):
            return await interaction.response.send_message("❌ Só Delegado+", ephemeral=True)
        db["portes"][self.nome.value] = {"cpf": self.cpf.value, "motivo": self.motivo.value, "delegado": interaction.user.name}
        save()
        canal = discord.utils.get(interaction.guild.channels, name="📦│armamento")
        if canal: await canal.send(f"✅ **PORTE EMITIDO**\nNome: {self.nome.value}\nCPF: {self.cpf.value}\nDelegado: {interaction.user.mention}")
        await interaction.response.send_message(f"✅ Porte emitido", ephemeral=True)

class TicketButton(View):
    def __init__(self, fac): super().__init__(timeout=None); self.fac = fac
    @discord.ui.button(label="ABRIR TICKET", style=discord.ButtonStyle.green, emoji="🎫")
    async def abrir(self, interaction: discord.Interaction, button: Button):
        user = interaction.user; guild = interaction.guild; fac = self.fac
        if str(user.id) in db.get("tickets", {}): return await interaction.response.send_message(f"❌ Já tem ticket", ephemeral=True)
        atendente = discord.utils.get(guild.roles, name="📞 Atendente Ticket")
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), user: discord.PermissionOverwrite(view_channel=True, send_messages=True), atendente: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        categoria = discord.utils.get(guild.categories, name=f"📞 ATENDIMENTO {fac}")
        ticket = await guild.create_text_channel(f"🎫│{user.name}", category=categoria, overwrites=overwrites)
        db["tickets"][str(user.id)] = {"id": ticket.id, "fac": fac}; save()
        await ticket.send(f"{atendente.mention}", embed=discord.Embed(title=f"Ticket {fac}"), view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket: {ticket.mention}", ephemeral=True)

class TicketControl(View):
    @discord.ui.button(label="ASSUMIR", style=discord.ButtonStyle.blurple, emoji="👮")
    async def assumir(self, interaction: discord.Interaction, button: Button):
        if not any(r.name == "📞 Atendente Ticket" for r in interaction.user.roles): return await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
        dono_ticket = interaction.channel.name.split("│")[1]
        membro = discord.utils.get(interaction.guild.members, name=dono_ticket)
        for role in interaction.guild.roles: await interaction.channel.set_permissions(role, view_channel=False)
        await interaction.channel.set_permissions(membro, view_channel=True, send_messages=True)
        await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True, manage_channels=True)
        await interaction.response.send_message(f"🔒 LOCK ATIVO")
    @discord.ui.button(label="FECHAR", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, interaction: discord.Interaction, button: Button):
        for user_id, data in db["tickets"].items():
            if data["id"] == interaction.channel.id: del db["tickets"][user_id]; break
        save(); await interaction.channel.delete()

@bot.command()
@is_dono()
async def promover(ctx, membro: discord.Member, *, cargo_novo: str):
    if not is_comando(ctx.guild, ctx.author, "PM"): return await ctx.send("❌ Só Alto Comando")
    cargo = discord.utils.get(ctx.guild.roles, name=cargo_novo)
    if not cargo: return await ctx.send("❌ Cargo não existe")
    for c in membro.roles:
        if "PM" in c.name or "PC" in c.name or "CV" in c.name: await membro.remove_roles(c)
    await membro.add_roles(cargo)
    await ctx.send(f"✅ {membro.mention} promovido para **{cargo_novo}**")

@bot.command()
@is_dono()
async def rebaixar(ctx, membro: discord.Member, *, cargo_novo: str):
    if not is_comando(ctx.guild, ctx.author, "PM"): return await ctx.send("❌ Só Alto Comando")
    cargo = discord.utils.get(ctx.guild.roles, name=cargo_novo)
    for c in membro.roles:
        if "PM" in c.name or "PC" in c.name or "CV" in c.name: await membro.remove_roles(c)
    await membro.add_roles(cargo)
    await ctx.send(f"✅ {membro.mention} rebaixado para **{cargo_novo}**")

@bot.command()
@is_dono()
async def exonerar(ctx, membro: discord.Member):
    if not is_comando(ctx.guild, ctx.author, "PM"): return await ctx.send("❌ Só Alto Comando")
    for c in membro.roles:
        if "PM" in c.name or "PC" in c.name or "CV" in c.name: await membro.remove_roles(c)
    civil = discord.utils.get(ctx.guild.roles, name="Civil")
    await membro.add_roles(civil)
    await ctx.send(f"✅ {membro.mention} **EXONERADO**")

@bot.command()
async def porte(ctx):
    if not pode_fazer_porte(ctx.guild, ctx.author):
        return await ctx.send("❌ **Acesso Negado**\nSó `Delegado PC` pra cima")
    await ctx.send_modal(PorteModal())

@bot.command()
@is_dono()
async def setup(ctx, org=None):
    ORGS = {
        "PM": {
            "tipo": "CORPORACAO",
            "cargos": [
                "Civil","Recruta PM","Soldado PM","Cabo PM","3º Sgt PM","2º Sgt PM","1º Sgt PM",
                "Sub Ten PM","Asp Oficial PM","2º Ten PM","1º Ten PM","Cap PM","Major PM",
                "Ten Cel PM","Cel PM","Sub Comandante Geral PM","Comandante Geral PM",
                "🏅 Medalha","📊 Estatística","👑 Alto Comando","🔧 Logística","💰 Finanças"
            ],
            "divisoes": ["🚔 1º BATALHÃO", "⚡ ROTA", "🛡️ BOP", "🚨 CHOQUE", "🚁 AEROPOL"]
        }
    }
    CORES = {"PM": discord.Color.blue()}
    orgs_para_criar = ORGS.keys() if org is None or org.upper() == "ALL" else [org.upper()]
    
    # CORRIGIDO: Não usa msg.edit pra não dar erro 404
    await ctx.send(f"⚡ INICIANDO SETUP PM... ISSO VAI DEMORAR 3 MIN")

    for o in orgs_para_criar:
        dados = ORGS[o]; cor = CORES[o]; cargo_ids = {}; criados = 0
        status_msg = await ctx.send(f"⚡ {o}: Criando 22 cargos... 0/22")

        for i, nome_cargo in enumerate(dados["cargos"]):
            try:
                perms = discord.Permissions()
                if "Alto Comando" in nome_cargo or "Comandante" in nome_cargo:
                    perms = discord.Permissions(manage_roles=True, kick_members=True, ban_members=True, manage_channels=True, manage_messages=True)
                cargo = await ctx.guild.create_role(name=nome_cargo, color=cor, permissions=perms)
                cargo_ids[nome_cargo] = cargo.id
                criados += 1
                try: await status_msg.edit(content=f"⚡ {o}: Criando cargos... {criados}/22")
                except: pass # IGNORA ERRO SE MENSAGEM SUMIR
            except Exception as e: print(f"Erro cargo {nome_cargo}: {e}")
            await asyncio.sleep(2) # 2 SEGUNDOS = ANTI RATE LIMIT

        # CATEGORIAS + DIVISÕES
        categorias_reais = {
            f"📋 ADMINISTRAÇÃO {o}": ["📢│avisos-internos","💬│chat-oficiais","📊│relatorios","📑│documentos"],
            f"🚨 OPERAÇÕES {o}": ["🚨│ocorrencias-ativas","🚨│ocorrencias-arquivo","📍│patrulhamento","📹│evidencias"],
            f"🚔 LOGÍSTICA {o}": ["🚔│viaturas","📦│armamento","💰│tesouraria"],
            f"📚 TREINAMENTO {o}": ["📚│academia","🎯│estande-tiro"],
            f"📞 COMUNICAÇÃO {o}": ["🔊│radio-central","🎙️│sala-reuniao"],
            f"📈 PROMOÇÃO {o}": ["📈│requerimento-promocao"],
            f"📊 HIERARQUIA {o}": ["📊│tabela-cargos"],
            f"📞 OUVIDORIA {o}": ["📞│ouvidoria","📋│denuncias"]
        }

        for div in dados["divisoes"]:
            categorias_reais[f"{div} {o}"] = [f"💬│chat-{div.split()[1].lower()}",f"📋│ocorrencias-{div.split()[1].lower()}",f"🔊│radio-{div.split()[1].lower()}"]

        await ctx.send(f"⚡ {o}: Criando 11 categorias + 5 divisões...")
        total_canais = 0
        for nome_cat, canais in categorias_reais.items():
            try:
                categoria = await ctx.guild.create_category(nome_cat)
                await asyncio.sleep(2)
                for nome_canal in canais:
                    try:
                        if "radio" in nome_canal:
                            await ctx.guild.create_voice_channel(nome_canal, category=categoria)
                        else:
                            await ctx.guild.create_text_channel(nome_canal, category=categoria)
                        total_canais += 1
                    except Exception as e: print(f"Erro canal {nome_canal}: {e}")
                    await asyncio.sleep(2)
            except Exception as e: print(f"Erro categoria {nome_cat}: {e}")

        canal_hierarquia = discord.utils.get(ctx.guild.channels, name=f"📊│tabela-cargos")
        if canal_hierarquia:
            texto = f"**HIERARQUIA {o}**\n\n" + "\n".join([f"{i+1}. {cargo}" for i,cargo in enumerate(dados["cargos"])])
            await canal_hierarquia.send(texto)
        db["corps"][o] = cargo_ids

    save()
    await ctx.send(f"✅ **SETUP PM FINALIZADO**\n{total_canais} Canais | {criados}/22 Cargos | 5 Divisões")

@bot.command()
@is_dono()
async def limpar(ctx):
    await ctx.send(f"⚡ APAGANDO TUDO... AGUARDE 1 MIN")
    for channel in ctx.guild.channels:
        try: await channel.delete(); await asyncio.sleep(1.5)
        except: pass
    for category in ctx.guild.categories:
        try: await category.delete(); await asyncio.sleep(1.5)
        except: pass
    for role in ctx.guild.roles:
        if role.name!= "@everyone" and not role.managed:
            try: await role.delete(); await asyncio.sleep(1.5)
            except: pass
    db["corps"] = {}; db["tickets"] = {}; save()
    await ctx.send(f"✅ SERVIDOR LIMPO")

bot.run(os.getenv("TOKEN"))
