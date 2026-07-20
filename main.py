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
    # CARGOS REAIS DA VIDA REAL
    FAC_LISTA = {
        "PM": ["Civil","Aluno Soldado PM","Soldado 2ª Classe PM","Soldado 1ª Classe PM","Cabo PM","3º Sargento PM","2º Sargento PM","1º Sargento PM","Sub Tenente PM","Aspirante a Oficial PM","2º Tenente PM","1º Tenente PM","Capitão PM","Major PM","Tenente Coronel PM","Coronel PM","Comandante Geral PM"],
        "PC": ["Civil","Estagiário PC","Agente de Polícia PC","Escrivão PC","Investigador PC","Delegado PC","Delegado Titular PC","Delegado Geral PC","Chefe de Polícia"],
        "PRF": ["Civil","PRF Aluno","Policial Rodoviário Federal","PRF Classe Especial","Inspetor PRF","Chefe de Serviço PRF","Superintendente PRF"],
        "PF": ["Civil","Estagiário PF","Agente de Polícia Federal","Escrivão PF","Papiloscopista PF","Delegado PF","Delegado Titular PF","Superintendente PF","Diretor Geral PF"],
        "SAMU": ["Civil","Estagiário SAMU","Condutor Socorrista","Técnico de Enfermagem","Enfermeiro SAMU","Médico Residente","Médico Regulador","Coordenador SAMU","Diretor Médico SAMU"]
    }
    
    CARGOS_GERAIS = ["🏅 Medalha Mérito","🏅 Medalha Bravura","🏅 Medalha Tempo Serviço","📈 Comissão Promoção","📊 Estatística","👑 Alto Comando","🔧 Logística","💰 Finanças"]
    FAC_CORES = {"PM": discord.Color.blue(), "PC": discord.Color.dark_red(), "PRF": discord.Color.dark_green(), "PF": discord.Color.dark_blue(), "SAMU": discord.Color.red()}
    
    facs_para_criar = FAC_LISTA.keys() if fac is None or fac.upper() == "ALL" else [fac.upper()]
    
    if fac and fac.upper() not in FAC_LISTA:
        return await ctx.send("❌ Use: `!setup PM` `!setup PC` `!setup PRF` `!setup PF` `!setup SAMU` ou `!setup ALL`")
    
    msg = await ctx.send(f"⏳ Iniciando setup realista...")
    
    for f in facs_para_criar:
        info = FAC_LISTA[f] + CARGOS_GERAIS
        cor = FAC_CORES[f]
        cargo_ids = {}
        
        await msg.edit(content=f"⏳ {f}: Criando 45 cargos reais...")
        # 1. CRIA CARGOS REAIS
        for nome_cargo in info:
            cargo = await ctx.guild.create_role(name=nome_cargo, color=cor, mentionable=False)
            cargo_ids[nome_cargo] = cargo.id
            await asyncio.sleep(0.7)
        
        comando = ctx.guild.get_role(cargo_ids[info[16]])
        civil = ctx.guild.get_role(cargo_ids["Civil"])
        overwrites_staff = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), comando: discord.PermissionOverwrite(view_channel=True, manage_messages=True)}
        overwrites_publico = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), civil: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        
        # 2. CRIA CATEGORIA POR CATEGORIA - IGUAL VIDA REAL
        categorias_reais = {
            f"📋 ADMINISTRAÇÃO {f}": [
                "📢│avisos-comando", "📢│boletim-interno", "💬│chat-oficiais", "📊│relatorios-gerais",
                "📝│formulario-entrada", "📝│formulario-promocao", "📋│recrutamento-publico", "📋│entrevistas"
            ],
            f"🚨 OPERAÇÕES {f}": [
                "🚨│ocorrencias-ativas", "🚨│ocorrencias-arquivo", "📍│patrulhamento", "📍│pontos-criticos",
                "🕵️│inteligencia", "🕵️│arquivo-secreto", "⚖️│juridico", "⚖️│processos"
            ],
            f"🚔 LOGÍSTICA {f}": [
                "🚔│viaturas-disponiveis", "🚔│viaturas-manutencao", "⛽│abastecimento", "📦│armamento",
                "📦│pedido-armamento", "🔧│oficina", "💰│tesouraria", "💰│controle-gastos"
            ],
            f"📚 TREINAMENTO {f}": [
                "📚│academia", "📚│cursos", "🎯│estande-tiro", "🎯│simulado-tatico",
                "🏆│hall-fama", "📷│midia-operacional", "📷│evidencias"
            ],
            f"📞 COMUNICAÇÃO {f}": [
                "🔊│radio-central", "🔊│radio-tatica", "🚨│call-urgencia", "🎙️│sala-reuniao",
                "🎙️│briefing", "🤝│parcerias", "🤝│interforcas"
            ]
        }
        
        await msg.edit(content=f"⏳ {f}: Criando 5 Categorias e 50+ canais...")
        for nome_cat, canais in categorias_reais.items():
            categoria = await ctx.guild.create_category(nome_cat, overwrites=overwrites_staff)
            await asyncio.sleep(0.5)
            
            for nome_canal in canais:
                if "radio" in nome_canal or "call" in nome_canal or "reuniao" in nome_canal or "tiro" in nome_canal or "briefing" in nome_canal:
                    await ctx.guild.create_voice_channel(nome_canal, category=categoria, overwrites=overwrites_staff)
                elif "recrutamento" in nome_canal or "entrevistas" in nome_canal:
                    await ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=overwrites_publico)
                else:
                    await ctx.guild.create_text_channel(nome_canal, category=categoria, overwrites=overwrites_staff)
                await asyncio.sleep(0.4)
        
        db["corps"][f] = cargo_ids
    
    save()
    await msg.edit(content=f"✅ **SETUP REALISTA FINALIZADO**\n{len(facs_para_criar)} Corporação(ões)\n\n45 Cargos Reais + 50 Canais + 5 Categorias por FAC\nEstrutura igual RP profissional")

bot.run(os.getenv("TOKEN"))
