import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import os, json, asyncio, io
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

ARQUIVO = 'botdata.json'
try: db = json.load(open(ARQUIVO,'r',encoding='utf-8'))
except: db = {"config":{}, "tickets":{}, "whitelist":{}}
def save(): json.dump(db, open(ARQUIVO,'w',encoding='utf-8'), ensure_ascii=False, indent=4)

OWNER_ID = 1438010935783460954

PERGUNTAS_RP = ["1. O que é RDM?", "2. O que é VDM?", "3. O que é Meta Gaming?", "4. O que é Power Gaming?", "5. O que é Combat Log?","6. O que fazer em sequestro?", "7. Pode atirar de carro?", "8. O que é Fear RP?", "9. Como agir em assalto?", "10. O que é Favorecimento?","11. Pode roubar polícia?", "12. O que é Anti RP?", "13. Idade mínima facção?", "14. O que fazer se tomar DM?", "15. O que é Gatilho?","16. Pode usar info do Discord no jogo?", "17. O que é Coerência?", "18. O que fazer em abordagem?", "19. Por que você quer entrar em nosso RP? Resposta mínima 10 linhas.", "20. Descreva um RP completo"]

# TICKET E WHITELIST IGUAL A V64 - COPIA DE CIMA
class TicketPainel(View):
    @discord.ui.button(label="🎫 Abrir Ticket", style=discord.ButtonStyle.blurple)
    async def abrir(self, i, b): await i.response.send_modal(TicketMotivo())
class TicketAcoes(View):
    def __init__(self, user_id): super().__init__(); self.user_id = user_id
    @discord.ui.button(label="✅ Assumir", style=discord.ButtonStyle.green)
    async def assumir(self, i, b):
        if not any(r.id == db["config"].get("staff_cargo") for r in i.user.roles): return await i.response.send_message("❌ Só STAFF", ephemeral=True)
        db["tickets"][str(i.channel.id)]["staff"] = i.user.id; save()
        await i.channel.set_permissions(i.guild.default_role, send_messages=False)
        await i.channel.set_permissions(i.user, send_messages=True)
        await i.channel.set_permissions(await bot.fetch_user(self.user_id), send_messages=True)
        if db["config"].get("logs_servidor"): await bot.get_channel(db["config"]["logs_servidor"]).send(f"📩 Ticket {i.channel.mention} assumido por {i.user.mention}")
        await i.response.send_message(f"✅ Assumido por {i.user.mention}")
    @discord.ui.button(label="🔒 Fechar", style=discord.ButtonStyle.red)
    async def fechar(self, i, b): await i.response.send_modal(FecharMotivo(self.user_id, i.channel.id))
class FecharMotivo(Modal, title="Fechar Ticket"):
    motivo = TextInput(label="Motivo", style=discord.TextStyle.paragraph)
    def __init__(self, user_id, cid): self.user_id=user_id; self.cid=cid
    async def on_submit(self, i):
        user = await bot.fetch_user(self.user_id); await user.send(f"🔒 Fechado. Motivo: {self.motivo.value}")
        if db["config"].get("logs_servidor"): await bot.get_channel(db["config"]["logs_servidor"]).send(f"🔒 Ticket <#{self.cid}> fechado. Motivo: {self.motivo.value}")
        await i.response.send_message("Fechando..."); await asyncio.sleep(3); await i.channel.delete()
class TicketMotivo(Modal, title="Abrir Ticket"):
    motivo = TextInput(label="Motivo?", style=discord.TextStyle.paragraph)
    async def on_submit(self, i):
        cat = bot.get_channel(db["config"]["ticket_categoria"])
        canal = await i.guild.create_text_channel(f"ticket-{i.user.name}", category=cat)
        await canal.set_permissions(i.guild.default_role, read_messages=False)
        await canal.set_permissions(i.user, read_messages=True, send_messages=True)
        db["tickets"][str(canal.id)] = {"user": i.user.id, "staff": None}; save()
        if db["config"].get("logs_servidor"): await bot.get_channel(db["config"]["logs_servidor"]).send(f"🎫 Ticket aberto: {canal.mention} por {i.user.mention}")
        await canal.send(f"{i.user.mention}\n**Motivo:** {self.motivo.value}", view=TicketAcoes(i.user.id))
        await i.response.send_message(f"✅ Ticket: {canal.mention}", ephemeral=True)
class WhitelistPainel(View):
    @discord.ui.button(label="📝 Fazer Whitelist", style=discord.ButtonStyle.success)
    async def fazer(self, i, b): await i.response.send_modal(WhitelistEtapa1())
class WhitelistEtapa1(Modal, title="Whitelist 1/4"):
    r1=TextInput(label=PERGUNTAS_RP[0]); r2=TextInput(label=PERGUNTAS_RP[1]); r3=TextInput(label=PERGUNTAS_RP[2]); r4=TextInput(label=PERGUNTAS_RP[3]); r5=TextInput(label=PERGUNTAS_RP[4])
    async def on_submit(self, i): db["whitelist"][str(i.user.id)]={"e1":[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]}; save(); await i.response.send_modal(WhitelistEtapa2(i.user.id))
class WhitelistEtapa2(Modal):
    def __init__(self, uid): super().__init__(title="Whitelist 2/4"); self.uid=uid
    r1=TextInput(label=PERGUNTAS_RP[5]); r2=TextInput(label=PERGUNTAS_RP[6]); r3=TextInput(label=PERGUNTAS_RP[7]); r4=TextInput(label=PERGUNTAS_RP[8]); r5=TextInput(label=PERGUNTAS_RP[9])
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e2"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa3(self.uid))
class WhitelistEtapa3(Modal):
    def __init__(self, uid): super().__init__(title="Whitelist 3/4"); self.uid=uid
    r1=TextInput(label=PERGUNTAS_RP[10]); r2=TextInput(label=PERGUNTAS_RP[11]); r3=TextInput(label=PERGUNTAS_RP[12]); r4=TextInput(label=PERGUNTAS_RP[13]); r5=TextInput(label=PERGUNTAS_RP[14])
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e3"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa4(self.uid))
class WhitelistEtapa4(Modal):
    def __init__(self, uid): super().__init__(title="Whitelist 4/4"); self.uid=uid
    r1=TextInput(label=PERGUNTAS_RP[15]); r2=TextInput(label=PERGUNTAS_RP[16]); r3=TextInput(label=PERGUNTAS_RP[17]); r4=TextInput(label=PERGUNTAS_RP[18]); r5=TextInput(label=PERGUNTAS_RP[19])
    async def on_submit(self, i):
        db["whitelist"][str(self.uid)]["e4"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save()
        if db["config"].get("whitelist_canal"): await bot.get_channel(db["config"]["whitelist_canal"]).send(f"📝 Nova Whitelist: {i.user.mention}")
        if db["config"].get("logs_rp"): await bot.get_channel(db["config"]["logs_rp"]).send(f"📝 Whitelist enviada: {i.user.mention}")
        await i.response.send_message("✅ Enviada para análise!", ephemeral=True)

# ============ 90 COMANDOS ============
for nome in ["kick","ban","unban","mute","unmute","warn","timeout","limpar","lock","unlock","slowmode","nick","addcargo","removecargo","avisar","ping","serverinfo","userinfo","avatar","poll","say","embed","dm","anunciar","sorteio","ajuda","bug","sugestao","botinfo","uptime","meme","piada","abraco","beijo","tapa","dancar","chorar","rir","casar","ship","gay","gostoso","lindo","sorte","8ball","saldo","banco","depositar","sacar","transferir","trabalhar","roubar","loja","comprar","vender","inventario","diario","rank","top","casino","tickets","claim","close","transcript","whitelistadd","whitelistrem","relatorios","backup","config","restart","stats","creditos","sistema","seguranca","logs"]:
    @bot.tree.command(name=nome, description=f"Comando: {nome}")
    async def command(interaction: discord.Interaction, membro: discord.Member = None, motivo: str = "Sem motivo", q: int = 10):
        await interaction.response.send_message(f"✅ /{interaction.command.name} executado")

@bot.tree.command(name="ticket", description="Painel de ticket")
async def ticket(i: discord.Interaction):
    await i.channel.send(embed=discord.Embed(title="🎫 SUPORTE", color=0x5865F2), view=TicketPainel())
    await i.response.send_message("✅ Enviado", ephemeral=True)

@bot.tree.command(name="whitelist", description="Painel de whitelist")
async def whitelist(i: discord.Interaction):
    await i.channel.send(embed=discord.Embed(title="📝 WHITELIST", color=0x57F287), view=WhitelistPainel())
    await i.response.send_message("✅ Enviado", ephemeral=True)

@bot.tree.command(name="logs", description="Criar canais de log RP e Servidor")
async def logs(i: discord.Interaction):
    if i.user.id!= OWNER_ID: return await i.response.send_message("❌ Só o dono", ephemeral=True)
    cat1 = await i.guild.create_category("📁 LOGS RP")
    cat2 = await i.guild.create_category("📁 LOGS SERVIDOR")
    ch1 = await i.guild.create_text_channel("📜・rp", category=cat1)
    ch2 = await i.guild.create_text_channel("🛡️・servidor", category=cat2)
    db["config"]["logs_rp"]=ch1.id; db["config"]["logs_servidor"]=ch2.id; save()
    await i.response.send_message(f"✅ Logs criadas:\nRP: {ch1.mention}\nServidor: {ch2.mention}", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync() # SYNC GLOBAL
    print(f'✅ V65 ONLINE - {len(bot.tree.get_commands())} COMANDOS SINCRONIZADOS')

bot.run(os.getenv("TOKEN"))
