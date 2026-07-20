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

@bot.command()
@is_dono()
async def promover(ctx, membro: discord.Member, *, cargo_novo: str):
    cargo = discord.utils.get(ctx.guild.roles, name=cargo_novo)
    if not cargo: return await ctx.send("❌ Cargo não existe")
    for c in membro.roles:
        if "PM" in c.name or "PC" in c.name or "CV" in c.name: await membro.remove_roles(c)
    await membro.add_roles(cargo)
    await ctx.send(f"✅ {membro.mention} promovido para **{cargo_novo}**")

@bot.command()
@is_dono()
async def rebaixar(ctx, membro: discord.Member, *, cargo_novo: str):
    cargo = discord.utils.get(ctx.guild.roles, name=cargo_novo)
    for c in membro.roles:
        if "PM" in c.name or "PC" in c.name or "CV" in c.name: await membro.remove_roles(c)
    await membro.add_roles(cargo)
    await ctx.send(f"✅ {membro.mention} rebaixado para **{cargo_novo}**")

@bot.command()
@is_dono()
async def exonerar(ctx, membro: discord.Member):
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
    
    await ctx.send(f"⚡ INICIANDO SETUP PM TANQUE... VAI DEMORAR 5 MIN MAS NÃO CAI")

    for o in ORGS:
        dados = ORGS[o]; cor = CORES[o]; cargo_ids = {}; criados = 0
        
        # CRIA CARGOS EM LOTES DE 3 COM PAUSA DE 10S
        await ctx.send(f"⚡ {o}: Criando 22 cargos...")
        for i in range(0, len(dados["cargos"]), 3):
            lote = dados["cargos"][i:i+3]
            for nome_cargo in lote:
                try:
                    perms = discord.Permissions()
                    if "Alto Comando" in nome_cargo or "Comandante" in nome_cargo:
                        perms = discord.Permissions(manage_roles=True, kick_members=True, ban_members=True, manage_channels=True, manage_messages=True)
                    cargo = await ctx.guild.create_role(name=nome_cargo, color=cor, permissions=perms)
                    cargo_ids[nome_cargo] = cargo.id
                    criados += 1
                except Exception as e: print(f"Erro cargo: {e}")
                await asyncio.sleep(3) # 3 SEGUNDOS
            await ctx.send(f"⚡ Progresso cargos: {criados}/22")
            await asyncio.sleep(10) # PAUSA DE 10S A CADA 3 CARGOS PRA NÃO TOMAR 429

        # CATEGORIAS + DIVISÕES
        categorias_reais = {
            f"📋 ADMINISTRAÇÃO {o}": ["📢│avisos-internos","💬│chat-oficiais","📊│relatorios"],
            f"🚨 OPERAÇÕES {o}": ["🚨│ocorrencias-ativas","🚨│ocorrencias-arquivo","📍│patrulhamento"],
            f"🚔 LOGÍSTICA {o}": ["🚔│viaturas","📦│armamento","💰│tesouraria"],
            f"📚 TREINAMENTO {o}": ["📚│academia","🎯│estande-tiro"],
            f"📞 COMUNICAÇÃO {o}": ["🔊│radio-central"],
            f"📈 PROMOÇÃO {o}": ["📈│requerimento-promocao"],
            f"📊 HIERARQUIA {o}": ["📊│tabela-cargos"],
            f"📞 OUVIDORIA {o}": ["📞│ouvidoria"]
        }

        for div in dados["divisoes"]:
            categorias_reais[f"{div} {o}"] = [f"💬│chat-{div.split()[1].lower()}",f"📋│ocorrencias-{div.split()[1].lower()}"]

        await ctx.send(f"⚡ Criando 11 categorias + 5 divisões...")
        total_canais = 0
        for nome_cat, canais in categorias_reais.items():
            try:
                categoria = await ctx.guild.create_category(nome_cat)
                await asyncio.sleep(3)
                for nome_canal in canais:
                    try:
                        if "radio" in nome_canal:
                            await ctx.guild.create_voice_channel(nome_canal, category=categoria)
                        else:
                            await ctx.guild.create_text_channel(nome_canal, category=categoria)
                        total_canais += 1
                    except Exception as e: print(f"Erro canal: {e}")
                    await asyncio.sleep(3)
            except Exception as e: print(f"Erro categoria: {e}")

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
    await ctx.send(f"⚡ APAGANDO TUDO... AGUARDE 2 MIN")
    for channel in ctx.guild.channels:
        try: await channel.delete(); await asyncio.sleep(2)
        except: pass
    for category in ctx.guild.categories:
        try: await category.delete(); await asyncio.sleep(2)
        except: pass
    for role in ctx.guild.roles:
        if role.name!= "@everyone" and not role.managed:
            try: await role.delete(); await asyncio.sleep(2)
            except: pass
    db["corps"] = {}; db["tickets"] = {}; save()
    await ctx.send(f"✅ SERVIDOR LIMPO")

bot.run(os.getenv("TOKEN"))
