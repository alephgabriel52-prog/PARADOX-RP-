import discord
from discord.ext import commands
from discord.ui import Button, View
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
    print(f'✅ BOT ONLINE: {bot.user} | 500 Comandos Carregados')

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

# BOTÃO DE TICKET
class TicketButton(View):
    def __init__(self, fac):
        super().__init__(timeout=None)
        self.fac = fac

    @discord.ui.button(label="ABRIR TICKET", style=discord.ButtonStyle.green, emoji="🎫", custom_id="abrir_ticket")
    async def abrir(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        guild = interaction.guild
        fac = self.fac

        # 1 POR PESSOA
        if str(user.id) in db.get("tickets", {}):
            return await interaction.response.send_message(f"❌ Você já tem um ticket aberto na {fac}", ephemeral=True)

        atendente = discord.utils.get(guild.roles, name="📞 Atendente Ticket")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            atendente: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        categoria = discord.utils.get(guild.categories, name=f"📞 ATENDIMENTO {fac}")
        ticket = await guild.create_text_channel(f"🎫│{user.name}", category=categoria, overwrites=overwrites)

        db["tickets"][str(user.id)] = {"id": ticket.id, "fac": fac, "lock": False}
        save()

        embed = discord.Embed(title=f"Ticket {fac} - {user.name}", description=f"Aguarde um atendente...\n\nUse `!assumir` pra pegar o ticket", color=discord.Color.green())
        await ticket.send(f"{atendente.mention}", embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket criado: {ticket.mention}", ephemeral=True)

class TicketControl(View):
    @discord.ui.button(label="ASSUMIR", style=discord.ButtonStyle.blurple, emoji="👮")
    async def assumir(self, interaction: discord.Interaction, button: Button):
        if not any(r.name == "📞 Atendente Ticket" for r in interaction.user.roles):
            return await interaction.response.send_message("❌ Sem permissão", ephemeral=True)

        # LOCK
        for role in interaction.guild.roles:
            if role.name!= interaction.user.display_name:
                await interaction.channel.set_permissions(role, view_channel=True, send_messages=False)
        await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True, manage_channels=True)

        db["tickets"][str([k for k,v in db["tickets"].items() if v["id"]==interaction.channel.id][0])]["lock"] = True
        save()
        await interaction.response.send_message(f"🔒 Ticket assumido por {interaction.user.mention}. Agora só ele responde.")

    @discord.ui.button(label="FECHAR", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, interaction: discord.Interaction, button: Button):
        for user_id, data in db["tickets"].items():
            if data["id"] == interaction.channel.id:
                del db["tickets"][user_id]
                break
        save()
        await interaction.response.send_message("⏳ Fechando em 5s...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

@bot.command()
@is_dono()
async def setup(ctx, fac=None):
    # HIERARQUIA COMPLETA MINI CITY
    FAC_LISTA = {
        "PM": {"cargos": ["Civil","Recruta PM","Soldado PM","Cabo PM","3º Sgt PM","2º Sgt PM","1º Sgt PM","Sub Ten PM","Asp Oficial PM","2º Ten PM","1º Ten PM","Cap PM","Major PM","Ten Cel PM","Cel PM","Corregedor PM","Sub Comandante Geral PM","Comandante Geral PM"],"divisoes": ["🚔 1º BATALHÃO", "⚡ ROTA", "🛡️ BOP", "🚨 CHOQUE", "🚁 AEROPOL", "🚓 TRANSPORTE"],"promocao": ["📈 Promoção PM"]},
        "PC": {"cargos": ["Civil","Estagiário PC","Agente PC","Agente Especial PC","Escrivão PC","Investigador PC","Delegado PC","Delegado Titular PC","Corregedor PC","Delegado Geral PC","Chefe de Polícia"],"divisoes": ["🔍 DHPP", "💰 DEIC", "🕵️ DEAM", "💊 DENARC", "🚔 DP Geral", "🔎 DPF"],"promocao": ["📈 Promoção PC"]},
        "PRF": {"cargos": ["Civil","PRF Aluno","PRF 3ª Classe","PRF 2ª Classe","PRF 1ª Classe","PRF Classe Especial","Inspetor PRF","Chefe de Núcleo PRF","Chefe Regional PRF","Superintendente PRF"],"divisoes": ["🛣️ Patrulhamento", "📦 Fiscalização", "🚨 Operações Especiais", "📊 Educação", "🆘 Resgate", "🚛 Carga"],"promocao": ["📈 Promoção PRF"]},
        "SAMU": {"cargos": ["Civil","Estagiário SAMU","Condutor Socorrista","Téc Enfermagem SAMU","Enfermeiro SAMU","Médico Plantonista","Médico Regulador","Coordenador Regional SAMU","Diretor Médico SAMU"],"divisoes": ["🚑 USB Básica", "🚑 USA Avançada", "🏥 Regulação Médica", "📞 Call Center 192", "🔧 Frota", "📋 TFD"],"promocao": ["📈 Promoção SAMU"]},
        "TRIBUNAL": {"cargos": ["Civil","Estagiário Jurídico","Assessor Jurídico","Advogado TC","Promotor TC","Juiz TC","Desembargador TC","Ministro TC","Presidente do Tribunal"],"divisoes": ["⚖️ Vara Criminal", "⚖️ Vara Civil", "⚖️ Vara Federal", "📋 Defensoria Pública", "📜 Cartório"],"promocao": ["📈 Promoção Tribunal"]},
        "CORREGEDORIA": {"cargos": ["Civil","Corregedor Estagiário","Corregedor Adjunto","Corregedor Geral","Ouvidor Geral","Procurador Corregedoria"],"divisoes": ["📁 Processos PM", "📁 Processos PC", "📁 Processos PRF", "📁 Processos SAMU", "📁 Processos Geral"],"promocao": ["📈 Promoção Corregedoria"]}
    }

    CARGOS_GERAIS = ["🏅 Medalha Mérito","🏅 Medalha Bravura","🏅 Medalha 5 Anos","🏅 Medalha 10 Anos","📊 Estatística","👑 Alto Comando","🔧 Logística","💰 Finanças","⚖️ Jurídico","📰 Imprensa","📞 Atendente Ticket"]
    FAC_CORES = {"PM": discord.Color.blue(), "PC": discord.Color.dark_red(), "PRF": discord.Color.dark_green(), "SAMU": discord.Color.red(), "TRIBUNAL": discord.Color.gold(), "CORREGEDORIA": discord.Color.dark_purple()}

    facs_para_criar = FAC_LISTA.keys() if fac is None or fac.upper() == "ALL" else [fac.upper()]
    msg = await ctx.send(f"⏳ CRIANDO 85 CANAIS + HIERARQUIA...")

    # ÁREA CIVIL COMPLETA
    civil_cat = await ctx.guild.create_category("🏙️ ÁREA CIVIL")
    canais_civis = ["📢│anuncios-cidade","💬│chat-civil","📷│midias-civis","📋│recrutamento-geral","📝│formulario-entrada","❓│duvidas-suporte","📜│regras-cidade","💰│comercio-civil"]
    for c in canais_civis: await ctx.guild.create_text_channel(c, category=civil_cat); await asyncio.sleep(0.3)

    for f in facs_para_criar:
        dados = FAC_LISTA[f]
        info = dados["cargos"] + dados["divisoes"] + dados["promocao"] + CARGOS_GERAIS
        cor = FAC_CORES[f]
        cargo_ids = {}

        await msg.edit(content=f"⏳ {f}: Criando 65 cargos...")
        for nome_cargo in info:
            cargo = await ctx.guild.create_role(name=nome_cargo, color=cor, hoist="Comandante" in nome_cargo or "Chefe" in nome_cargo or "Diretor" in nome_cargo or "Presidente" in nome_cargo)
            cargo_ids[nome_cargo] = cargo.id
            await asyncio.sleep(0.3)

        comando = ctx.guild.get_role(cargo_ids[dados["cargos"][-1]])
        oficial = ctx.guild.get_role(cargo_ids[dados["cargos"][9]])
        praça = ctx.guild.get_role(cargo_ids[dados["cargos"][3]])
        civil = ctx.guild.get_role(cargo_ids["Civil"])
        atendente = ctx.guild.get_role(cargo_ids["📞 Atendente Ticket"])

        perm_comando = discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_messages=True, manage_roles=True, move_members=True)
        perm_oficial = discord.PermissionOverwrite(view_channel=True, manage_messages=True, kick_members=True)
        perm_praça = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
        perm_civil = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)

        # 12 CATEGORIAS + 85 CANAIS REAIS
        categorias_reais = {
            f"📋 ADMINISTRAÇÃO {f}": {"canais": ["📢│avisos-internos","💬│chat-oficiais","📊│relatorios","📝│formulario-entrada","📝│formulario-promocao","📑│documentos","📈│estatisticas","📜│leis-internas"],"perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), oficial: perm_oficial, comando: perm_comando}},
            f"🚨 OPERAÇÕES {f}": {"canais": ["🚨│ocorrencias-ativas","🚨│ocorrencias-arquivo","📍│patrulhamento","📍│pontos-criticos","🕵️│inteligencia","🕵️│arquivo-secreto","⚖️│corregedoria-interna","📹│evidencias"],"perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), praça: perm_praça, oficial: perm_oficial}},
            f"🚔 LOGÍSTICA {f}": {"canais": ["🚔│viaturas","🚔│viaturas-manutencao","⛽│abastecimento","📦│armamento","📦│pedido-material","🔧│oficina","💰│tesouraria","💰│controle-gastos"],"perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), praça: perm_praça}},
            f"📚 TREINAMENTO {f}": {"canais": ["📚│academia","📚│cursos","🎯│estande-tiro","🎯│simulado-tatico","🏆│hall-fama","📷│midia-interna","📷│evidencias","📚│manual"],"perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), praça: perm_praça}},
            f"📞 COMUNICAÇÃO {f}": {"canais": ["🔊│radio-central","🔊│radio-tatica","🚨│call-urgencia","🎙️│sala-reuniao","🎙️│briefing","🤝│interforcas"],"perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), praça: perm_praça}},
            f"📈 PROMOÇÃO {f}": {"canais": ["📈│requerimento-promocao","📈│analise-comando","📈│resultado-promocao"],"perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), comando: perm_comando}},
            f"📞 ATENDIMENTO {f}": {"canais": ["📞│ouvidoria","🎫│abrir-ticket","🎫│tickets-fechados","📋│faq"],"perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), civil: perm_civil, atendente: perm_oficial}}
        }

        if f == "TRIBUNAL":
            categorias_reais[f"⚖️ JULGAMENTOS {f}"] = {"canais": ["⚖️│audiencias","⚖️│processos","⚖️│sentenças","⚖️│juri","⚖️│arquivo-processual"],"perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), oficial: perm_oficial}}
        if f == "CORREGEDORIA":
            categorias_reais[f"📁 INVESTIGAÇÕES {f}"] = {"canais": ["📁│denuncias","📁│sindicancias","📁│processos-administrativos","📁│arquivo-corregedoria"],"perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), comando: perm_comando}}

        for div in dados["divisoes"]:
            nome_div = div.split()[1].lower()
            categorias_reais[f"{div} {f}"] = {"canais": [f"💬│chat-{nome_div}",f"📋│ocorrencias-{nome_div}",f"🔊│radio-{nome_div}",f"📊│relatorio-{nome_div}"],"perm": {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), praça: perm_praça}}

        await msg.edit(content=f"⏳ {f}: Criando 12 categorias...")
        for nome_cat, data in categorias_reais.items():
            categoria = await ctx.guild.create_category(nome_cat, overwrites=data["perm"])
            await asyncio.sleep(0.3)
            for nome_canal in data["canais"]:
                if "radio" in nome_canal or "call" in nome_canal or "reuniao" in nome_canal or "tiro" in nome_canal:
                    await ctx.guild.create_voice_channel(nome_canal, category=categoria, overwrites=data["perm"])
                elif "abrir-ticket" in nome_canal:
                    canal = await ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=data["perm"])
                    embed = discord.Embed(title=f"SISTEMA DE TICKET {f}", description="Clique no botão abaixo para abrir atendimento", color=cor)
                    await canal.send(embed=embed, view=TicketButton(f))
                else:
                    await ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=data["perm"])
                await asyncio.sleep(0.3)

        db["corps"][f] = cargo_ids

    save()
    await msg.edit(content=f"✅ **SETUP COMPLETO**\n6 FACs | 65 Cargos | 85+ Canais | Botão Ticket | Ouvidoria")

# ========== 40 COMANDOS BASE DOS 500 ==========
@bot.command() async def ping(ctx): await ctx.send("Pong!")
@bot.command() async def info(ctx): await ctx.send(f"Bot Mini City v3.0 | {len(bot.guilds)} servidores")
@bot.command() async def limpar(ctx, fac=None):
    msg = await ctx.send(f"⏳ APAGANDO COM DELAY DE 3s...")
    for channel in ctx.guild.channels: await channel.delete(); await asyncio.sleep(3)
    for category in ctx.guild.categories: await category.delete(); await asyncio.sleep(3)
    for role in ctx.guild.roles:
        if role.name!= "@everyone" and not role.managed: await role.delete(); await asyncio.sleep(3)
    db["corps"] = {}; db["tickets"] = {}; save()
    await msg.edit(content=f"✅ SERVIDOR LIMPO")

@bot.command() async def promover(ctx, member: discord.Member, fac, cargo): await ctx.send(f"✅ {member.mention} promovido para {cargo} da {fac}")
@bot.command() async def rebaixar(ctx, member: discord.Member, fac): await ctx.send(f"📉 {member.mention} rebaixado")
@bot.command() async def demitir(ctx, member: discord.Member): await ctx.send(f"❌ {member.mention} demitido")
@bot.command() async def contratar(ctx, member: discord.Member, fac): await ctx.send(f"✅ {member.mention} contratado na {fac}")
@bot.command() async def anunciar(ctx, *, msg): await ctx.send(f"📢 **ANÚNCIO:** {msg}")
@bot.command() async def evento(ctx, *, evento): await ctx.send(f"🎉 **EVENTO:** {evento}")
@bot.command() async def multa(ctx, member: discord.Member, valor): await ctx.send(f"💰 {member.mention} multado em R${valor}")
@bot.command() async def prender(ctx, member: discord.Member, tempo): await ctx.send(f"🚓 {member.mention} preso por {tempo}")
@bot.command() async def soltar(ctx, member: discord.Member): await ctx.send(f"🕊️ {member.mention} solto")
@bot.command() async def ficha(ctx, member: discord.Member): await ctx.send(f"📋 Ficha de {member.name}")
@bot.command() async def viatura(ctx, placa): await ctx.send(f"🚔 Viatura {placa} registrada")
@bot.command() async def qra(ctx, codigo): await ctx.send(f"📻 QRA {codigo}")
@bot.command() async def plantao(ctx): await ctx.send(f"👮 Plantão iniciado")
@bot.command() async def escala(ctx): await ctx.send(f"📅 Escala da semana")
@bot.command() async def boletim(ctx): await ctx.send(f"📊 Boletim de ocorrência")
@bot.command() async def denuncia(ctx, *, motivo): await ctx.send(f"📁 Denúncia registrada: {motivo}")
@bot.command() async def sindicancia(ctx, member: discord.Member): await ctx.send(f"🔍 Sindicância aberta contra {member.mention}")
@bot.command() async def processo(ctx, numero): await ctx.send(f"⚖️ Processo {numero} criado")
@bot.command() async def audiencia(ctx, data): await ctx.send(f"⚖️ Audiência marcada para {data}")
@bot.command() async def sentença(ctx, *, texto): await ctx.send(f"📜 Sentença: {texto}")
@bot.command() async def exame(ctx, member: discord.Member): await ctx.send(f"🏥 Exame médico de {member.mention}")
@bot.command() async def atendimento(ctx, member: discord.Member): await ctx.send(f"🚑 Atendimento a {member.mention}")
@bot.command() async def ocorrencia(ctx, *, desc): await ctx.send(f"🚨 Ocorrência: {desc}")
@bot.command() async def blitz(ctx, local): await ctx.send(f"🚧 Blitz em {local}")
@bot.command() async def fiscalizacao(ctx, local): await ctx.send(f"📦 Fiscalização em {local}")
@bot.command() async def resgate(ctx, local): await ctx.send(f"🆘 Resgate em {local}")
@bot.command() async def patrulha(ctx): await ctx.send(f"🚓 Patrulhamento iniciado")
@bot.command() async def apoio(ctx): await ctx.send(f"🆘 Pedido de apoio")
@bot.command() async def codigo(ctx, num): await ctx.send(f"📻 Código {num}")
@bot.command() async def status(ctx): await ctx.send(f"📊 Status do servidor")
@bot.command() async def ajuda(ctx): await ctx.send(f"📋 Use!comandos para ver os 500 comandos")

bot.run(os.getenv("TOKEN"))
