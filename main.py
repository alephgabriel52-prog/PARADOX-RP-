import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import os, json, asyncio, aiohttp
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

# MODAL DE PORTE DE ARMA - SÓ DELEGADO+
class PorteModal(Modal, title="Emitir Porte de Arma - PC"):
    nome = TextInput(label="Nome do Civil", required=True)
    cpf = TextInput(label="CPF/RG", required=True)
    motivo = TextInput(label="Motivo", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        db["portes"][self.nome.value] = {"cpf": self.cpf.value, "motivo": self.motivo.value, "delegado": interaction.user.name}
        save()
        canal = discord.utils.get(interaction.guild.channels, name="📦│armamento")
        await canal.send(f"✅ **PORTE EMITIDO**\nNome: {self.nome.value}\nCPF: {self.cpf.value}\nDelegado: {interaction.user.mention}\nMotivo: {self.motivo.value}")
        await interaction.response.send_message(f"✅ Porte emitido para {self.nome.value}", ephemeral=True)

class TicketButton(View):
    def __init__(self, fac): super().__init__(timeout=None); self.fac = fac
    @discord.ui.button(label="ABRIR TICKET", style=discord.ButtonStyle.green, emoji="🎫")
    async def abrir(self, interaction: discord.Interaction, button: Button):
        user = interaction.user; guild = interaction.guild; fac = self.fac
        if str(user.id) in db.get("tickets", {}): return await interaction.response.send_message(f"❌ Já tem ticket", ephemeral=True)
        atendente = discord.utils.get(guild.roles, name="📞 Atendente Ticket")
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), user: discord.PermissionOverwrite(view_channel=True, send_messages=True), atendente: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)}
        categoria = discord.utils.get(guild.categories, name=f"📞 ATENDIMENTO {fac}")
        ticket = await guild.create_text_channel(f"🎫│{user.name}", category=categoria, overwrites=overwrites)
        db["tickets"][str(user.id)] = {"id": ticket.id, "fac": fac}; save()
        embed = discord.Embed(title=f"Ticket {fac}", description="Aguarde...", color=discord.Color.green())
        await ticket.send(f"{atendente.mention}", embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket: {ticket.mention}", ephemeral=True)

class TicketControl(View):
    @discord.ui.button(label="ASSUMIR", style=discord.ButtonStyle.blurple, emoji="👮")
    async def assumir(self, interaction: discord.Interaction, button: Button):
        if not any(r.name == "📞 Atendente Ticket" for r in interaction.user.roles): return await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
        dono_ticket = interaction.channel.name.split("│")[1]
        membro = discord.utils.get(interaction.guild.members, name=dono_ticket)
        for role in interaction.guild.roles:
            await interaction.channel.set_permissions(role, view_channel=False)
        await interaction.channel.set_permissions(membro, view_channel=True, send_messages=True)
        await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True, manage_channels=True)
        await interaction.response.send_message(f"🔒 LOCK. Só {interaction.user.mention} + {membro.mention}")

    @discord.ui.button(label="FECHAR", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, interaction: discord.Interaction, button: Button):
        for user_id, data in db["tickets"].items():
            if data["id"] == interaction.channel.id: del db["tickets"][user_id]; break
        save(); await interaction.channel.delete()

@bot.command()
@is_dono()
async def promover(ctx, membro: discord.Member, *, cargo_novo: str):
    cargo = discord.utils.get(ctx.guild.roles, name=cargo_novo)
    if not cargo: return await ctx.send("❌ Cargo não existe")
    if not is_comando(ctx.guild, ctx.author, "PM"): return await ctx.send("❌ Só Alto Comando")
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
    await ctx.send(f"✅ {membro.mention} **EXONERADO**. Voltou pra Civil")

@bot.command()
async def porte(ctx):
    if not pode_fazer_porte(ctx.guild, ctx.author):
        return await ctx.send("❌ **Acesso Negado**\nSó `Delegado PC` pra cima pode emitir porte")
    await ctx.send_modal(PorteModal())

@bot.command()
@is_dono()
async def setup(ctx, org=None):
    ORGS = {
        "CV": {"tipo": "FACCAO","cargos": ["Civil","Membro CV","Soldado CV","Cabo CV","3º Gerente CV","2º Gerente CV","1º Gerente CV","Gerente Geral CV","Dono CV","🏅 Medalha","📊 Estatística","👑 Alto Comando","🔧 Logística","💰 Finanças","📞 Atendente Ticket"],"divisoes": ["🏘️ BOCA 1", "🏘️ BOCA 2", "🏘️ BOCA 3", "🚚 LOGISTICA", "🔫 ARMAMENTO"]},
        "PM": {"tipo": "CORPORACAO","cargos": ["Civil","Recruta PM","Soldado PM","Cabo PM","3º Sgt PM","2º Sgt PM","1º Sgt PM","Sub Ten PM","Asp Oficial PM","2º Ten PM","1º Ten PM","Cap PM","Major PM","Ten Cel PM","Cel PM","Sub Comandante Geral PM","Comandante Geral PM","🏅 Medalha","📊 Estatística","👑 Alto Comando","🔧 Logística","💰 Finanças"],"divisoes": ["🚔 1º BATALHÃO", "⚡ ROTA", "🛡️ BOP", "🚨 CHOQUE", "🚁 AEROPOL"]},
        "PC": {"tipo": "CORPORACAO","cargos": ["Civil","Estagiário PC","Agente PC","Agente Especial PC","Escrivão PC","Investigador PC","Delegado PC","Delegado Titular PC","Delegado Geral PC","Chefe de Polícia","🏅 Medalha","📊 Estatística","👑 Alto Comando","💰 Finanças"],"divisoes": ["🔍 DHPP", "💰 DEIC", "🕵️ DEAM", "💊 DENARC", "🚔 DP Geral"]}
    }
    CORES = {"CV": discord.Color.dark_red(),"PM": discord.Color.blue(),"PC": discord.Color.dark_red()}
    orgs_para_criar = ORGS.keys() if org is None or org.upper() == "ALL" else [org.upper()]
    msg = await ctx.send(f"⚡ CRIANDO COM DIVISÕES E PERMISSÕES...")

    civil_cat = await ctx.guild.create_category("🏙️ ÁREA CIVIL")
    for c in ["📢│anuncios-cidade","💬│chat-civil","📝│formulario-entrada","📜│regras-cidade"]:
        await ctx.guild.create_text_channel(c, category=civil_cat); await asyncio.sleep(0.5)

    for o in orgs_para_criar:
        dados = ORGS[o]; cor = CORES[o]; cargo_ids = {}
        await msg.edit(content=f"⚡ {o}: Criando {len(dados['cargos'])} cargos...")

        for nome_cargo in dados["cargos"]:
            perms = discord.Permissions()
            if "Alto Comando" in nome_cargo or "Comandante" in nome_cargo or "Dono" in nome_cargo:
                perms = discord.Permissions(manage_roles=True, kick_members=True, ban_members=True, manage_channels=True, manage_messages=True)
            elif "Atendente Ticket" in nome_cargo:
                perms = discord.Permissions(manage_messages=True, manage_channels=True)
            cargo = await ctx.guild.create_role(name=nome_cargo, color=cor, permissions=perms, hoist="Alto Comando" in nome_cargo)
            cargo_ids[nome_cargo] = cargo.id; await asyncio.sleep(0.5)

        comando = ctx.guild.get_role(cargo_ids[dados["cargos"][-3]])
        oficial = ctx.guild.get_role(cargo_ids[dados["cargos"][6]])
        praça = ctx.guild.get_role(cargo_ids[dados["cargos"][2]])
        civil = ctx.guild.get_role(cargo_ids["Civil"])

        perm_comando = {comando: discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_messages=True)}
        perm_oficial = {oficial: discord.PermissionOverwrite(view_channel=True, manage_messages=True)}
        perm_praça = {praça: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        perm_civil = {civil: discord.PermissionOverwrite(view_channel=True, send_messages=True)}

        # 12 CATEGORIAS + DIVISÕES
        categorias_reais = {
            f"📋 ADMINISTRAÇÃO {o}": ["📢│avisos-internos","💬│chat-oficiais","📊│relatorios","📝│formulario-promocao","📑│documentos","📈│estatisticas"],
            f"🚨 OPERAÇÕES {o}": ["🚨│ocorrencias-ativas","🚨│ocorrencias-arquivo","📍│patrulhamento","🕵️│inteligencia","📹│evidencias"],
            f"🚔 LOGÍSTICA {o}": ["🚔│viaturas","📦│armamento","💰│tesouraria","📊│inventario"],
            f"📚 TREINAMENTO {o}": ["📚│academia","🎯│estande-tiro","📚│manual"],
            f"📞 COMUNICAÇÃO {o}": ["🔊│radio-central","🎙️│sala-reuniao"],
            f"📈 PROMOÇÃO {o}": ["📈│requerimento-promocao","📈│analise-comando"],
            f"📊 HIERARQUIA {o}": ["📊│tabela-cargos"]
        }

        if dados["tipo"] == "FACCAO":
            categorias_reais[f"📞 ATENDIMENTO {o}"] = ["🎫│abrir-ticket","📞│ouvidoria"]
        else:
            categorias_reais[f"📞 OUVIDORIA {o}"] = ["📞│ouvidoria","📋│denuncias"]

        # CRIA DIVISÕES COM PERMISSÃO
        for div in dados["divisoes"]:
            nome_div = div.split()[1].lower()
            categorias_reais[f"{div} {o}"] = [f"💬│chat-{nome_div}",f"📋│ocorrencias-{nome_div}",f"🔊│radio-{nome_div}",f"📦│material-{nome_div}"]

        await msg.edit(content=f"⚡ {o}: Criando categorias e divisões...")
        for nome_cat, canais in categorias_reais.items():
            categoria = await ctx.guild.create_category(nome_cat); await asyncio.sleep(0.5)
            for nome_canal in canais:
                if "radio" in nome_canal:
                    await ctx.guild.create_voice_channel(nome_canal, category=categoria)
                elif "abrir-ticket" in nome_canal and dados["tipo"] == "FACCAO":
                    canal = await ctx.guild.create_text_channel(nome_canal, category=categoria)
                    embed = discord.Embed(title=f"TICKET {o}", description="Clique", color=cor)
                    await canal.send(embed=embed, view=TicketButton(o))
                else:
                    await ctx.guild.create_text_channel(nome_canal, category=categoria)
                await asyncio.sleep(0.5)

        canal_hierarquia = discord.utils.get(ctx.guild.channels, name=f"📊│tabela-cargos")
        if canal_hierarquia:
            texto = f"**HIERARQUIA {o}**\n\n" + "\n".join([f"{i+1}. {cargo}" for i,cargo in enumerate(dados["cargos"])])
            await canal_hierarquia.send(texto)
        db["corps"][o] = cargo_ids

    save()
    await msg.edit(content=f"✅ **SETUP COMPLETO COM DIVISÕES**")

bot.run(os.getenv("TOKEN"))
