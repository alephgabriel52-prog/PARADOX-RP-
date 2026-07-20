import discord
from discord.ext import commands
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
except: db = {"corps":{}}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

@bot.command()
@is_dono()
async def setup(ctx, fac=None):
    FAC_LISTA = {
        "PM": ["Civil","Recruta PM","Soldado 2ª PM","Soldado 1ª PM","Cabo PM","3º Sargento PM","2º Sargento PM","1º Sargento PM","Sub Tenente PM","Aspirante PM","2º Tenente PM","1º Tenente PM","Capitão PM","Major PM","Tenente Coronel PM","Coronel PM","Comandante Geral PM"],
        "PC": ["Civil","Estagiário PC","Agente PC Classe 3","Agente PC Classe 2","Agente PC Classe 1","Inspetor PC","Delegado PC","Delegado PC Especial","Delegado Geral PC","Chefe PC"],
        "PRF": ["Civil","PRF Aluno","PRF 3ª Classe","PRF 2ª Classe","PRF 1ª Classe","PRF Classe Especial","Inspetor PRF","Chefe PRF","Superintendente PRF"],
        "PF": ["Civil","Estagiário PF","Agente PF","Escrivão PF","Papiloscopista PF","Delegado PF","Delegado PF Especial","Superintendente PF","Diretor Geral PF"],
        "SAMU": ["Civil","Estagiário SAMU","Condutor SAMU","Téc. Enfermagem SAMU","Enfermeiro SAMU","Médico Residente","Médico SAMU","Coordenador SAMU","Diretor SAMU"]
    }
    
    # + CARGOS GERAIS PRA BATER 45
    CARGOS_EXTRAS = ["🏅 Medalha Destaque","🏅 Medalha Bravura","📈 Promoção Mês","📊 Estatísticas","👑 Comando","🔧 Logística","💰 Tesouraria"]
    FAC_CORES = {"PM": discord.Color.blue(), "PC": discord.Color.dark_red(), "PRF": discord.Color.dark_green(), "PF": discord.Color.dark_blue(), "SAMU": discord.Color.red()}
    
    facs_para_criar = FAC_LISTA.keys() if fac is None or fac.upper() == "ALL" else [fac.upper()]
    
    if fac and fac.upper() not in FAC_LISTA:
        return await ctx.send("❌ Use: `!setup PM` `!setup PC` `!setup PRF` `!setup PF` `!setup SAMU` ou `!setup ALL`")
    
    msg = await ctx.send(f"⏳ Criando {len(facs_para_criar)} corporação(ões)... Isso vai demorar 3-5min")
    
    for f in facs_para_criar:
        info = FAC_LISTA[f] + CARGOS_EXTRAS
        cor = FAC_CORES[f]
        cargo_ids = {}
        
        await msg.edit(content=f"⏳ Criando cargos da {f}... 45 cargos")
        # 1. CRIA 45 CARGOS
        for nome_cargo in info:
            cargo = await ctx.guild.create_role(name=nome_cargo, color=cor)
            cargo_ids[nome_cargo] = cargo.id
            await asyncio.sleep(0.6)
        
        # 2. PERMISSÕES
        comando = ctx.guild.get_role(cargo_ids[info[16]])
        civil = ctx.guild.get_role(cargo_ids["Civil"])
        overwrites_staff = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), comando: discord.PermissionOverwrite(view_channel=True, manage_channels=True)}
        overwrites_civil = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), civil: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        
        await msg.edit(content=f"⏳ Criando canais da {f}... 50+ canais")
        # 3. CATEGORIA
        categoria = await ctx.guild.create_category(f"🚨 {f}", overwrites=overwrites_staff)
        
        # 4. CRIA 50+ CANAIS
        canais = [
            # GERAL
            "📢│avisos-geral","📢│avisos-comando","💬│chat-geral","💬│chat-comando","📊│relatorios",
            # ADMIN
            "📝│formulario-entrada","📝│formulario-promocao","📋│recrutamento","📋│entrevistas","📑│documentos",
            # OPERACIONAL
            "🚨│ocorrencias-ativas","🚨│ocorrencias-arquivo","🚔│viaturas","🚔│viaturas-manutencao","📦│armamento","📦│armamento-pedido",
            # INTEL
            "🕵️│intel","🕵️│intel-arquivo","📍│patrulhamento","📍│pontos-quentes",
            # VOZ
            "🔊│radio-principal","🔊│radio-tatica","🚨│call-urgencia","🎙️│reuniao-comando","🎙️│reuniao-geral",
            # TREINAMENTO
            "📚│treinamento","📚│cursos","🎯│campo-tiro","🎯│simulado",
            # LOGISTICA
            "💰│tesouraria","💰│gastos","🔧│logistica","🔧│oficina","⛽│combustivel",
            # EXTRA
            "📷│midia","📷│evidencias","⚖️│juridico","⚖️│processos","🤝│parcerias","🏆│hall-fama"
        ]
        
        for nome in canais:
            if "radio" in nome or "call" in nome or "reuniao" in nome or "tiro" in nome:
                await ctx.guild.create_voice_channel(nome, category=categoria, overwrites=overwrites_staff)
            elif "recrutamento" in nome or "entrevistas" in nome:
                await ctx.guild.create_text_channel(nome, category=categoria, overwrites=overwrites_civil)
            else:
                await ctx.guild.create_text_channel(nome, category=categoria, overwrites=overwrites_staff)
            await asyncio.sleep(0.4)
        
        db["corps"][f] = cargo_ids
    
    save()
    await msg.edit(content=f"✅ **SETUP MEGA COMPLETO FINALIZADO**\n{len(facs_para_criar)} Corps criadas\n45+ Cargos e 50+ Canais cada\nUse `!setup ALL` pra criar todas de uma vez")

bot.run(os.getenv("TOKEN"))
