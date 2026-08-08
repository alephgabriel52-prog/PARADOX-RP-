import discord
from discord.ext import commands
from discord.ui import View, Button
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
except: db = {"tickets":{}, "economia": {}, "comandos_dinamicos": {}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    return commands.check(lambda ctx: ctx.author.id == DONO_ID)

TEMPLATES = {
    "pmrj": {
        "nome": "PMERJ", "cor": 0x1E3A8A,
        "cargos": [
            {"nome": "👑 Coronel PM", "permissoes": discord.Permissions(administrator=True)},
            {"nome": "⭐ Tenente-Coronel PM", "permissoes": discord.Permissions(manage_roles=True, manage_channels=True)},
            {"nome": "🎖️ Major PM", "permissoes": discord.Permissions(manage_roles=True)},
            {"nome": "⚔️ Capitão PM", "permissoes": discord.Permissions(ban_members=True, kick_members=True)},
            {"nome": "🚔 1º Tenente PM", "permissoes": discord.Permissions(kick_members=True, manage_messages=True)},
            {"nome": "🚓 2º Tenente PM", "permissoes": discord.Permissions(kick_members=True, manage_messages=True)},
            {"nome": "🪖 Aspirante-a-Oficial PM", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "🪖 Subtenente PM", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "🪖 1º Sargento PM", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "🪖 2º Sargento PM", "permissoes": discord.Permissions()},
            {"nome": "🪖 3º Sargento PM", "permissoes": discord.Permissions()},
            {"nome": "👮 Cabo PM", "permissoes": discord.Permissions(mute_members=True)},
            {"nome": "🚨 Soldado 1ª Classe PM", "permissoes": discord.Permissions(send_messages=True, connect=True)},
            {"nome": "🚨 Soldado 2ª Classe PM", "permissoes": discord.Permissions(send_messages=True, connect=True)},
            {"nome": "📋 Adj Comandamento", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "📋 Adj Operações", "permissoes": discord.Permissions(manage_messages=True)},
            {"nome": "📋 Adj Pessoal", "permissoes": discord.Permissions()},
            {"nome": "📋 Adj Logística", "permissoes": discord.Permissions()},
            {"nome": "📋 Adj Inteligência", "permissoes": discord.Permissions()},
            {"nome": "🎯 GATE", "permissoes": discord.Permissions()},
            {"nome": "🐕 K9", "permissoes": discord.Permissions()},
            {"nome": "🏍️ ROCAM", "permissoes": discord.Permissions()},
            {"nome": "🚁 AEROPOL", "permissoes": discord.Permissions()},
            {"nome": "🚤 GPAER", "permissoes": discord.Permissions()},
            {"nome": "🏥 SAÚDE PM", "permissoes": discord.Permissions()},
            {"nome": "⚖️ CORREGEDORIA", "permissoes": discord.Permissions(ban_members=True)},
            {"nome": "📚 INSTRUTOR", "permissoes": discord.Permissions()},
            {"nome": "📢 ASSESSORIA", "permissoes": discord.Permissions()},
            {"nome": "💰 FINANCEIRO", "permissoes": discord.Permissions()},
            {"nome": "🔧 MANUTENÇÃO", "permissoes": discord.Permissions()},
            {"nome": "📡 COMUNICAÇÕES", "permissoes": discord.Permissions()},
            {"nome": "👤 Civil", "permissoes": discord.Permissions(send_messages=True, connect=True)}
        ],
        "categorias": {
            "📢 PMERJ - INFORMAÇÕES": ["📜│regras-pm", "📣│avisos-gerais", "🎖️│promocoes", "📅│escala-servico", "📊│efetivo"],
            "🚓 PMERJ - COMANDO GERAL": ["📡│radio-coronel", "📡│radio-oficiais", "📋│bo-comando", "📑│portarias", "📊│relatorios"],
            "🚨 PMERJ - OPERAÇÕES": ["📡│radio-geral", "🚨│190", "🗺️│qth", "📋│bo", "📝│entrada-e-saida", "🎯│patrulhamento", "🚔│viaturas"],
            "🔒 PMERJ - ADMINISTRATIVO": ["🔒│arsenal", "🚗│garagem", "📚│doutrina", "🏥│saude-pm", "💰│folha-pagamento", "📋│processos"],
            "🎯 PMERJ - FORÇAS ESPECIAIS": ["🎯│gate", "🐕│k9", "🏍️│rocam", "🚁│aeropol", "🚤│gpaer"],
            "💬 PMERJ - GERAL": ["💬│chat-geral", "📸│midias", "🎮│sugestoes", "🎤│reunioes"]
        }
    },
    # COPIA OS OUTROS 12 AQUI... BOPE, PC, CV, TCP, ETC. DEIXEI SÓ PM PRA NAO FICAR GIGANTE
}

class PainelRegras(View):
    def __init__(self, cargo_civil):
        super().__init__(timeout=None)
        self.cargo_civil = cargo_civil
    @discord.ui.button(label="✅ Aceitar Regras", style=discord.ButtonStyle.green, emoji="✅", custom_id="aceitar_regras")
    async def aceitar(self, interaction: discord.Interaction, button: Button):
        await interaction.user.add_roles(self.cargo_civil)
        await interaction.response.send_message("✅ Você aceitou as regras! Cargo liberado.", ephemeral=True)

@bot.command()
async def painel(ctx):
    cargo_civil = discord.utils.get(ctx.guild.roles, name="👤 Civil")
    if not cargo_civil: return await ctx.send("❌ Cargo `👤 Civil` não encontrado. Rode o!setup primeiro.")
    embed = discord.Embed(title="📜 REGRAS DO SERVIDOR", description="**1.** Respeite todos\n**2.** Sem racismo/homofobia\n**3.** Sem divulgar\n**4.** RP sempre\n**5.** Siga a hierarquia\nClique no botão abaixo para liberar o acesso!", color=0x2B2D31)
    embed.set_footer(text="Bot Criado por Biel")
    await ctx.send(embed=embed, view=PainelRegras(cargo_civil))

@bot.command(name="dono")
@is_dono()
async def dono(ctx, *, descricao=None):
    if not isinstance(ctx.channel, discord.DMChannel): return await ctx.send("❌ Use no meu privado")
    if not descricao: return await ctx.send("❌ Ex: `!dono crie um comando de setup da pmrj`")
    await ctx.send("⚡ Criando em **3 segundos**...")
    await asyncio.sleep(3)
    nome = gerar_nome(descricao)
    encontrado = None
    for key in TEMPLATES:
        if key in descricao.lower(): encontrado = key; break
    if encontrado:
        db["comandos_dinamicos"][nome] = {"tipo": "setup", "template": encontrado}
        save()
        registrar_setup(nome, encontrado)
        t = TEMPLATES[encontrado]
        await ctx.send(embed=discord.Embed(title="✅ COMANDO CRIADO", description=f"Use: `!{nome}`\nOrg: {t['nome']}\n**{len(t['cargos'])} Cargos | {sum(len(c) for c in t['categorias'].values())} Canais**", color=t["cor"]))
    else: await ctx.send(f"❌ Org não encontrada. Temos: {', '.join(TEMPLATES.keys())}")

def gerar_nome(desc):
    for key in TEMPLATES:
        if key in desc.lower(): return "setup" + key
    return "setup" + str(random.randint(10,99))

def registrar_setup(nome, template_key):
    async def comando_setup(ctx, t=template_key): await criar_setup(ctx, t)
    bot.add_command(commands.Command(comando_setup, name=nome))

async def criar_setup(ctx, template_key):
    t = TEMPLATES[template_key]
    guild = ctx.guild
    me = guild.me

    # TESTE DE PERMISSAO ANTES DE APAGAR TUDO
    if not me.guild_permissions.administrator:
        return await ctx.send("❌ **SEM PERMISSÃO**\nMe dá cargo `Administrador` e me coloca no topo da lista de cargos!")

    msg = await ctx.send(f"🏗️ **Montando {t['nome']}**... `0%`")

    # DELETAR
    for role in guild.roles:
        if role.name!= "@everyone" and role.name!= me.name:
            try: await role.delete(reason="Setup")
            except: pass
    await asyncio.sleep(2)

    for channel in guild.channels:
        try: await channel.delete(reason="Setup")
        except: pass
    await asyncio.sleep(2)

    # CRIAR CARGOS
    for i, cargo in enumerate(t["cargos"]):
        try:
            await guild.create_role(name=cargo["nome"], permissions=cargo["permissoes"], color=discord.Color(t["cor"]), reason="Setup")
        except Exception as e:
            await ctx.send(f"❌ Erro ao criar cargo {cargo['nome']}: {e}")
        porcentagem = int(((i+1)/len(t["cargos"]))*50)
        await msg.edit(content=f"🏗️ **Montando {t['nome']}**... `{porcentagem}%`")
        await asyncio.sleep(0.5)

    # CRIAR CANAIS
    total = sum(len(c) for c in t["categorias"].values())
    feito = 0
    for cat_nome, canais in t["categorias"].items():
        try:
            categoria = await guild.create_category(cat_nome, reason="Setup")
        except Exception as e:
            await ctx.send(f"❌ Erro ao criar categoria {cat_nome}: {e}")
            continue
        for canal_nome in canais:
            try:
                await guild.create_text_channel(canal_nome, category=categoria, reason="Setup")
            except Exception as e:
                await ctx.send(f"❌ Erro ao criar canal {canal_nome}: {e}")
            feito += 1
            porcentagem = 50 + int((feito/total)*50)
            await msg.edit(content=f"🏗️ **Montando {t['nome']}**... `{porcentagem}%`")
            await asyncio.sleep(0.5)

    await msg.edit(content="", embed=discord.Embed(title=f"✅ {t['nome']} CONFIGURADO", description=f"**{len(t['cargos'])} Cargos** e **{total} Canais** criados\nUse `!painel`", color=t["cor"]))

@bot.event
async def on_ready():
    for nome, data in db["comandos_dinamicos"].items():
        if data["tipo"] == "setup": registrar_setup(nome, data["template"])
    print(f'✅ BOT V43 ONLINE')

bot.run(os.getenv("TOKEN"))
