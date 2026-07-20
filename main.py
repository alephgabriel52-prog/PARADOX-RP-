import discord
from discord.ext import commands
from discord.ui import Button, View
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
    print(f'✅ BOT ONLINE TURBO: {bot.user}')

DONO_ID = 1438010935783460954
ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r', encoding='utf-8') as f: db = json.load(f)
except: db = {"corps":{}, "tickets":{}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

LOGOS = {
    "CV": "https://i.imgur.com/XXXXXX.png","PCCC": "https://i.imgur.com/XXXXXX.png","TCP": "https://i.imgur.com/XXXXXX.png",
    "BDM": "https://i.imgur.com/XXXXXX.png","RODO": "https://i.imgur.com/XXXXXX.png","PENHA": "https://i.imgur.com/XXXXXX.png","CDA": "https://i.imgur.com/XXXXXX.png",
    "PM": "https://i.imgur.com/XXXXXX.png","PC": "https://i.imgur.com/XXXXXX.png","PRF": "https://i.imgur.com/XXXXXX.png","SAMU": "https://i.imgur.com/XXXXXX.png","BOPE": "https://i.imgur.com/XXXXXX.png",
    "TRIBUNAL": "https://i.imgur.com/XXXXXX.png","CORREGEDORIA": "https://i.imgur.com/XXXXXX.png"
}

class TicketButton(View):
    def __init__(self, fac):
        super().__init__(timeout=None)
        self.fac = fac
    @discord.ui.button(label="ABRIR TICKET", style=discord.ButtonStyle.green, emoji="🎫")
    async def abrir(self, interaction: discord.Interaction, button: Button):
        user = interaction.user; guild = interaction.guild; fac = self.fac
        if str(user.id) in db.get("tickets", {}):
            return await interaction.response.send_message(f"❌ Você já tem um ticket aberto na {fac}", ephemeral=True)
        atendente = discord.utils.get(guild.roles, name="📞 Atendente Ticket")
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), user: discord.PermissionOverwrite(view_channel=True, send_messages=True), atendente: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        categoria = discord.utils.get(guild.categories, name=f"📞 ATENDIMENTO {fac}")
        ticket = await guild.create_text_channel(f"🎫│{user.name}", category=categoria, overwrites=overwrites)
        db["tickets"][str(user.id)] = {"id": ticket.id, "fac": fac}; save()
        embed = discord.Embed(title=f"Ticket {fac} - {user.name}", description=f"Aguarde um atendente...\n\nClique em ASSUMIR", color=discord.Color.green())
        await ticket.send(f"{atendente.mention}", embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket criado: {ticket.mention}", ephemeral=True)

class TicketControl(View):
    @discord.ui.button(label="ASSUMIR", style=discord.ButtonStyle.blurple, emoji="👮")
    async def assumir(self, interaction: discord.Interaction, button: Button):
        if not any(r.name == "📞 Atendente Ticket" for r in interaction.user.roles): return await interaction.response.send_message("❌ Sem permissão", ephemeral=True)
        for role in interaction.guild.roles:
            if role!= interaction.user: await interaction.channel.set_permissions(role, view_channel=True, send_messages=False)
        await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True, manage_channels=True)
        await interaction.response.send_message(f"🔒 Ticket assumido por {interaction.user.mention}. LOCK ATIVO")
    @discord.ui.button(label="FECHAR", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, interaction: discord.Interaction, button: Button):
        for user_id, data in db["tickets"].items():
            if data["id"] == interaction.channel.id: del db["tickets"][user_id]; break
        save(); await interaction.response.send_message("⏳ Fechando..."); await asyncio.sleep(0.1); await interaction.channel.delete()

@bot.command()
@is_dono()
async def setup(ctx, org=None):
    ORGS = {
        "CV": {"tipo": "FACCAO","cargos": ["Civil","Membro CV","Soldado CV","Cabo CV","3º Gerente CV","2º Gerente CV","1º Gerente CV","Gerente Geral CV","Dono CV","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças","📞 Atendente Ticket"],"divisoes": ["🏘️ BOCA 1", "🏘️ BOCA 2", "🏘️ BOCA 3", "🚚 LOGISTICA", "🔫 ARMAMENTO"]},
        "PCCC": {"tipo": "FACCAO","cargos": ["Civil","Membro PCCC","Soldado PCCC","Cabo PCCC","3º Gerente PCCC","2º Gerente PCCC","1º Gerente PCCC","Gerente Geral PCCC","Dono PCCC","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças","📞 Atendente Ticket"],"divisoes": ["🏘️ BOCA 1", "🏘️ BOCA 2", "🚚 LOGISTICA", "🔫 ARMAMENTO"]},
        "TCP": {"tipo": "FACCAO","cargos": ["Civil","Membro TCP","Soldado TCP","Cabo TCP","3º Gerente TCP","2º Gerente TCP","1º Gerente TCP","Gerente Geral TCP","Dono TCP","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças","📞 Atendente Ticket"],"divisoes": ["🏘️ BOCA 1", "🏘️ BOCA 2", "🚚 LOGISTICA"]},
        "BDM": {"tipo": "FACCAO","cargos": ["Civil","Membro BDM","Soldado BDM","Cabo BDM","3º Gerente BDM","2º Gerente BDM","1º Gerente BDM","Gerente Geral BDM","Dono BDM","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças","📞 Atendente Ticket"],"divisoes": ["🏘️ BOCA 1", "🚚 LOGISTICA"]},
        "RODO": {"tipo": "FACCAO","cargos": ["Civil","Membro RODO","Soldado RODO","Cabo RODO","3º Gerente RODO","2º Gerente RODO","1º Gerente RODO","Gerente Geral RODO","Dono RODO","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças","📞 Atendente Ticket"],"divisoes": ["🏘️ BOCA 1", "🚚 LOGISTICA"]},
        "PENHA": {"tipo": "FACCAO","cargos": ["Civil","Membro PENHA","Soldado PENHA","Cabo PENHA","3º Gerente PENHA","2º Gerente PENHA","1º Gerente PENHA","Gerente Geral PENHA","Dono PENHA","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças","📞 Atendente Ticket"],"divisoes": ["🏘️ BOCA 1", "🚚 LOGISTICA"]},
        "CDA": {"tipo": "FACCAO","cargos": ["Civil","Membro CDA","Soldado CDA","Cabo CDA","3º Gerente CDA","2º Gerente CDA","1º Gerente CDA","Gerente Geral CDA","Dono CDA","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças","📞 Atendente Ticket"],"divisoes": ["🏘️ BOCA 1", "🚚 LOGISTICA"]},
        "PM": {"tipo": "CORPORACAO","cargos": ["Civil","Recruta PM","Soldado PM","Cabo PM","3º Sgt PM","2º Sgt PM","1º Sgt PM","Sub Ten PM","Asp Oficial PM","2º Ten PM","1º Ten PM","Cap PM","Major PM","Ten Cel PM","Cel PM","Sub Comandante Geral PM","Comandante Geral PM","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças"],"divisoes": ["🚔 1º BATALHÃO", "⚡ ROTA", "🛡️ BOP", "🚨 CHOQUE", "🚁 AEROPOL"]},
        "PC": {"tipo": "CORPORACAO","cargos": ["Civil","Estagiário PC","Agente PC","Agente Especial PC","Escrivão PC","Investigador PC","Delegado PC","Delegado Titular PC","Delegado Geral PC","Chefe de Polícia","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças"],"divisoes": ["🔍 DHPP", "💰 DEIC", "🕵️ DEAM", "💊 DENARC", "🚔 DP Geral"]},
        "PRF": {"tipo": "CORPORACAO","cargos": ["Civil","PRF Aluno","PRF 3ª Classe","PRF 2ª Classe","PRF 1ª Classe","PRF Classe Especial","Inspetor PRF","Chefe de Núcleo PRF","Chefe Regional PRF","Superintendente PRF","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças"],"divisoes": ["🛣️ Patrulhamento", "📦 Fiscalização", "🚨 Operações", "📊 Educação"]},
        "SAMU": {"tipo": "CORPORACAO","cargos": ["Civil","Estagiário SAMU","Condutor Socorrista","Téc Enfermagem SAMU","Enfermeiro SAMU","Médico Plantonista","Médico Regulador","Coordenador Regional SAMU","Diretor Médico SAMU","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças"],"divisoes": ["🚑 USB", "🚑 USA", "🏥 Regulação", "📞 192"]},
        "BOPE": {"tipo": "CORPORACAO","cargos": ["Civil","Recruta BOPE","Soldado BOPE","Cabo BOPE","Sargento BOPE","Sub Ten BOPE","Oficial BOPE","Cap BOPE","Major BOPE","Ten Cel BOPE","Cel BOPE","Comandante BOPE","🏅 Medalha","📊 Estatística","👑 Comando","💰 Finanças"],"divisoes": ["⚡ TÁTICO", "🚨 OPERAÇÕES", "🎯 SNIPER"]},
        "TRIBUNAL": {"tipo": "ORGAO","cargos": ["Civil","Assessor Jurídico","Advogado","Promotor","Juiz","Desembargador","Ministro","Presidente Tribunal"],"divisoes": ["⚖️ Vara Criminal", "⚖️ Vara Civil"]},
        "CORREGEDORIA": {"tipo": "ORGAO","cargos": ["Civil","Corregedor Adjunto","Corregedor Geral","Ouvidor Geral"],"divisoes": ["📁 Processos PM", "📁 Processos PC", "📁 Processos PRF", "📁 Processos SAMU", "📁 Processos BOPE"]}
    }

    CORES = {"CV": discord.Color.dark_red(),"PCCC": discord.Color.dark_green(),"TCP": discord.Color.purple(),"BDM": discord.Color.orange(),"RODO": discord.Color.blue(),"PENHA": discord.Color.teal(),"CDA": discord.Color.greyple(),"PM": discord.Color.blue(),"PC": discord.Color.dark_red(),"PRF": discord.Color.dark_green(),"SAMU": discord.Color.red(),"BOPE": discord.Color.black(),"TRIBUNAL": discord.Color.gold(),"CORREGEDORIA": discord.Color.dark_purple()}

    orgs_para_criar = ORGS.keys() if org is None or org.upper() == "ALL" else [org.upper()]
    msg = await ctx.send(f"⚡ MODO TURBO 0.1s ATIVADO")

    # MUDA FOTO TURBO
    if org and org.upper() in LOGOS:
        async with aiohttp.ClientSession() as session:
            async with session.get(LOGOS[org.upper()]) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    await ctx.guild.edit(icon=data)

    civil_cat = await ctx.guild.create_category("🏙️ ÁREA CIVIL")
    for c in ["📢│anuncios-cidade","💬│chat-civil","📷│midias-civis","📋│recrutamento-geral","📝│formulario-entrada","❓│duvidas-suporte","📜│regras-cidade","💰│comercio-civil"]:
        await ctx.guild.create_text_channel(c, category=civil_cat); await asyncio.sleep(0.1)

    total_canais = 0
    for o in orgs_para_criar:
        dados = ORGS[o]; cor = CORES[o]; cargo_ids = {}
        await msg.edit(content=f"⚡ {o}: Criando {len(dados['cargos'])} cargos TURBO...")

        # CRIA 50+ CARGOS SEM DELAY
        tasks = []
        for nome_cargo in dados["cargos"]:
            tasks.append(ctx.guild.create_role(name=nome_cargo, color=cor, hoist="Comandante" in nome_cargo or "Dono" in nome_cargo or "Presidente" in nome_cargo))
        cargos = await asyncio.gather(*tasks)
        for i, cargo in enumerate(cargos): cargo_ids[dados["cargos"][i]] = cargo.id

        comando = ctx.guild.get_role(cargo_ids[dados["cargos"][-4]]); oficial = ctx.guild.get_role(cargo_ids[dados["cargos"][6]]); praça = ctx.guild.get_role(cargo_ids[dados["cargos"][2]]); civil = ctx.guild.get_role(cargo_ids["Civil"]); atendente = ctx.guild.get_role(cargo_ids["📞 Atendente Ticket"]) if "📞 Atendente Ticket" in cargo_ids else None

        perm_comando = discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_messages=True, manage_roles=True)
        perm_oficial = discord.PermissionOverwrite(view_channel=True, manage_messages=True, kick_members=True)
        perm_praça = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
        perm_civil = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)

        categorias_reais = {
            f"📋 ADMINISTRAÇÃO {o}": ["📢│avisos-internos","💬│chat-oficiais","📊│relatorios","📝│formulario-entrada","📝│formulario-promocao","📑│documentos","📈│estatisticas","📜│leis-internas","🏆│hall-fama"],
            f"🚨 OPERAÇÕES {o}": ["🚨│ocorrencias-ativas","🚨│ocorrencias-arquivo","📍│patrulhamento","📍│pontos-criticos","🕵️│inteligencia","🕵️│arquivo-secreto","⚖️│corregedoria-interna","📹│evidencias","📸│fotos-ocorrencia"],
            f"🚔 LOGÍSTICA {o}": ["🚔│viaturas","🚔│viaturas-manutencao","⛽│abastecimento","📦│armamento","📦│pedido-material","🔧│oficina","💰│tesouraria","💰│controle-gastos","📊│inventario"],
            f"📚 TREINAMENTO {o}": ["📚│academia","📚│cursos","🎯│estande-tiro","🎯│simulado-tatico","🏆│hall-fama","📷│midia-interna","📷│evidencias","📚│manual","🎓│certificados"],
            f"📞 COMUNICAÇÃO {o}": ["🔊│radio-central","🔊│radio-tatica","🚨│call-urgencia","🎙️│sala-reuniao","🎙️│briefing","🤝│interforcas"],
            f"📈 PROMOÇÃO {o}": ["📈│requerimento-promocao","📈│analise-comando","📈│resultado-promocao"],
            f"📊 HIERARQUIA {o}": ["📊│tabela-cargos","📊│requisitos-promocao","📊│organograma"]
        }

        if dados["tipo"] == "FACCAO":
            categorias_reais[f"📞 ATENDIMENTO {o}"] = ["🎫│abrir-ticket","📞│ouvidoria","📋│faq"]
        elif dados["tipo"] == "CORPORACAO":
            categorias_reais[f"📞 OUVIDORIA {o}"] = ["📞│ouvidoria","📋│denuncias","📋│sugestoes","📋│faq"]

        if o == "TRIBUNAL":
            categorias_reais[f"⚖️ JULGAMENTOS {o}"] = ["⚖️│audiencias","⚖️│processos","⚖️│sentenças","⚖️│juri","⚖️│arquivo-processual"]
        if o == "CORREGEDORIA":
            categorias_reais[f"📁 INVESTIGAÇÕES {o}"] = ["📁│denuncias","📁│sindicancias","📁│processos-administrativos","📁│arquivo-corregedoria"]

        for div in dados["divisoes"]:
            nome_div = div.split()[1].lower()
            categorias_reais[f"{div} {o}"] = [f"💬│chat-{nome_div}",f"📋│ocorrencias-{nome_div}",f"🔊│radio-{nome_div}",f"📊│relatorio-{nome_div}"]

        await msg.edit(content=f"⚡ {o}: Criando 12 categorias TURBO...")
        # CRIA TUDO JUNTO SEM DELAY
        for nome_cat, canais in categorias_reais.items():
            categoria = await ctx.guild.create_category(nome_cat); await asyncio.sleep(0.1)
            tasks = []
            for nome_canal in canais:
                if "radio" in nome_canal or "call" in nome_canal or "reuniao" in nome_canal or "tiro" in nome_canal:
                    tasks.append(ctx.guild.create_voice_channel(nome_canal, category=categoria))
                elif "abrir-ticket" in nome_canal and dados["tipo"] == "FACCAO":
                    canal = await ctx.guild.create_text_channel(nome_canal, category=categoria)
                    embed = discord.Embed(title=f"SISTEMA DE TICKET {o}", description="Clique no botão para abrir atendimento", color=cor)
                    await canal.send(embed=embed, view=TicketButton(o))
                    total_canais += 1
                else:
                    tasks.append(ctx.guild.create_text_channel(nome_canal, category=categoria))
                    total_canais += 1
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.1)

        canal_hierarquia = discord.utils.get(ctx.guild.channels, name=f"📊│tabela-cargos")
        if canal_hierarquia:
            texto = f"**HIERARQUIA {o}**\n\n" + "\n".join([f"{i+1}. {cargo}" for i,cargo in enumerate(dados["cargos"])])
            await canal_hierarquia.send(texto)

        db["corps"][o] = cargo_ids

    save()
    await msg.edit(content=f"✅ **SETUP TURBO FINALIZADO**\n{total_canais}+ Canais | 50+ Cargos | 0.1s por item")

@bot.command()
@is_dono()
async def setupstaff(ctx):
    msg = await ctx.send("⚡ CRIANDO STAFF TURBO...")
    cargos_staff = ["👑 Dono do Servidor","🛡️ Administrador Geral","👮 Administrador","🔧 Moderador","📞 Suporte","🎨 Designer","🤖 Bot Dev"]
    cores_staff = [discord.Color.gold(), discord.Color.red(), discord.Color.orange(), discord.Color.blue(), discord.Color.green(), discord.Color.purple(), discord.Color.dark_grey()]
    tasks = [ctx.guild.create_role(name=nome, color=cores_staff[i]) for i,nome in enumerate(cargos_staff)]
    await asyncio.gather(*tasks)
    staff_cat = await ctx.guild.create_category("👑 STAFF")
    canais = ["📢│avisos-staff","💬│chat-staff","📋│reunioes-staff","📊│relatorios-staff","🎫│tickets-staff","📁│arquivos-staff"]
    tasks = [ctx.guild.create_text_channel(c, category=staff_cat) for c in canais]
    await asyncio.gather(*tasks)
    await ctx.guild.create_voice_channel("🎙️│sala-staff", category=staff_cat)
    await msg.edit(content="✅ **STAFF CRIADA TURBO**")

@bot.command()
@is_dono()
async def limpar(ctx):
    msg = await ctx.send(f"⚡ APAGANDO TURBO 0.1s...")
    # APAGA TUDO JUNTO
    tasks = [channel.delete() for channel in ctx.guild.channels]
    await asyncio.gather(*tasks)
    tasks = [category.delete() for category in ctx.guild.categories]
    await asyncio.gather(*tasks)
    tasks = [role.delete() for role in ctx.guild.roles if role.name!= "@everyone" and not role.managed]
    await asyncio.gather(*tasks)
    db["corps"] = {}; db["tickets"] = {}; save()
    await msg.edit(content=f"✅ SERVIDOR LIMPO EM 2 SEGUNDOS")

bot.run(os.getenv("TOKEN"))
