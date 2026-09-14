import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Modal, TextInput
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

# LINKS DAS SUAS IMAGENS
BANNER_SUPORTE = "https://cdn.discordapp.com/attachments/1481856611587723295/1549067503588606033/file_00000000136881f58a07836a66e4246c.png?ex=6aa95909&is=6aa80789&hm=bdc18d543ecb36c4417854a67c81826d27438297b74e41549a177b1843797a43"
BANNER_BOT = "https://cdn.discordapp.com/attachments/1481856611587723295/1549067503890866176/IMG_20260914_111956.jpg?ex=6aa95909&is=6aa80789&hm=e56e7317913f32b44715d63482cabc005132d429ed7e0eb7a61f7ab3c2e56181"

# ============ TICKET COM SELECT ============
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Suporte", emoji="💬", description="Erros ou pedidos de ajuda"),
            discord.SelectOption(label="Parceria", emoji="🤝", description="Propostas e colaborações"),
            discord.SelectOption(label="Denúncia", emoji="🚨", description="Usuários ou comportamentos"),
            discord.SelectOption(label="Pagamento", emoji="💰", description="Dúvidas sobre compras"),
            discord.SelectOption(label="Seja Staff", emoji="📞", description="Quer entrar pra staff"),
            discord.SelectOption(label="Assumir Facção", emoji="🚩", description="Assumir facção no RP"),
            discord.SelectOption(label="Assumir Polícia", emoji="🚓", description="Assumir polícia no RP"),
            discord.SelectOption(label="Outros", emoji="❓", description="Assunto não listado")
        ]
        super().__init__(placeholder="Selecione o motivo do seu ticket", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketMotivo(self.values[0]))

class TicketPainel(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class TicketAcoes(View):
    def __init__(self, user_id, tipo): super().__init__(timeout=None); self.user_id = user_id; self.tipo = tipo
    @discord.ui.button(label="✅ Assumir", style=discord.ButtonStyle.green)
    async def assumir(self, i, b):
        if not any(r.id == db["config"].get("staff_cargo") for r in i.user.roles): return await i.response.send_message("❌ Só STAFF", ephemeral=True)
        db["tickets"][str(i.channel.id)]["staff"] = i.user.id; save()
        await i.channel.set_permissions(i.guild.default_role, send_messages=False)
        await i.channel.set_permissions(i.user, send_messages=True)
        await i.channel.set_permissions(await bot.fetch_user(self.user_id), send_messages=True)
        await i.response.send_message(f"✅ Ticket assumido por {i.user.mention} | Tipo: **{self.tipo}**")
    @discord.ui.button(label="🔒 Fechar", style=discord.ButtonStyle.red)
    async def fechar(self, i, b): await i.response.send_modal(FecharMotivo(self.user_id, i.channel.id, self.tipo))

class FecharMotivo(Modal, title="Fechar Ticket"):
    motivo = TextInput(label="Motivo do fechamento", style=discord.TextStyle.paragraph)
    def __init__(self, user_id, cid, tipo): self.user_id=user_id; self.cid=cid; self.tipo=tipo
    async def on_submit(self, i):
        user = await bot.fetch_user(self.user_id); await user.send(f"🔒 Ticket de {self.tipo} fechado. Motivo: {self.motivo.value}")
        msgs = [f"[{m.created_at.strftime('%d/%m %H:%M')}] {m.author.name}: {m.content}" async for m in i.channel.history(limit=500)]
        file = discord.File(io.BytesIO("\n".join(reversed(msgs)).encode()), filename=f"ticket-{self.cid}.txt")
        if db["config"].get("transcript_canal"): await bot.get_channel(db["config"]["transcript_canal"]).send(f"📁 Repositório - {self.tipo} <#{self.cid}>", file=file)
        await i.response.send_message("Fechando..."); await asyncio.sleep(3); await i.channel.delete()

class TicketMotivo(Modal):
    def __init__(self, tipo): super().__init__(title=f"Ticket: {tipo}"); self.tipo=tipo
    motivo = TextInput(label="Descreva seu motivo", style=discord.TextStyle.paragraph)
    async def on_submit(self, i):
        if not db["config"].get("ticket_categoria"): return await i.response.send_message("❌ Configure primeiro usando /config", ephemeral=True)
        cat = bot.get_channel(db["config"]["ticket_categoria"])
        canal = await i.guild.create_text_channel(f"ticket-{self.tipo}-{i.user.name}", category=cat)
        await canal.set_permissions(i.guild.default_role, read_messages=False)
        await canal.set_permissions(i.user, read_messages=True, send_messages=True)
        db["tickets"][str(canal.id)] = {"user": i.user.id, "staff": None, "tipo": self.tipo}; save()
        await canal.send(f"{i.user.mention}\n**Tipo:** {self.tipo}\n**Motivo:** {self.motivo.value}", view=TicketAcoes(i.user.id, self.tipo))
        await i.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

# ============ WHITELIST ============
class WhitelistPainel(View):
    @discord.ui.button(label="📝 Fazer Whitelist", style=discord.ButtonStyle.success)
    async def fazer(self, i, b): await i.response.send_modal(WhitelistEtapa1())
class WhitelistEtapa1(Modal, title="Whitelist 1/4"):
    r1=TextInput(label="1. O que é RDM?"); r2=TextInput(label="2. O que é VDM?"); r3=TextInput(label="3. O que é Meta Gaming?"); r4=TextInput(label="4. O que é Power Gaming?"); r5=TextInput(label="5. O que é Combat Log?")
    async def on_submit(self, i): db["whitelist"][str(i.user.id)]={"e1":[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]}; save(); await i.response.send_modal(WhitelistEtapa2(i.user.id))
class WhitelistEtapa2(Modal):
    def __init__(self, uid): super().__init__(title="Whitelist 2/4"); self.uid=uid
    r1=TextInput(label="6. O que fazer em sequestro?"); r2=TextInput(label="7. Pode atirar de carro?"); r3=TextInput(label="8. O que é Fear RP?"); r4=TextInput(label="9. Como agir em assalto?"); r5=TextInput(label="10. O que é Favorecimento?")
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e2"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa3(self.uid))
class WhitelistEtapa3(Modal):
    def __init__(self, uid): super().__init__(title="Whitelist 3/4"); self.uid=uid
    r1=TextInput(label="11. Pode roubar polícia?"); r2=TextInput(label="12. O que é Anti RP?"); r3=TextInput(label="13. Idade mínima facção?"); r4=TextInput(label="14. O que fazer se tomar DM?"); r5=TextInput(label="15. O que é Gatilho?")
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e3"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa4(self.uid))
class WhitelistEtapa4(Modal):
    def __init__(self, uid): super().__init__(title="Whitelist 4/4"); self.uid=uid
    r1=TextInput(label="16. Pode usar info do Discord no jogo?"); r2=TextInput(label="17. O que é Coerência?"); r3=TextInput(label="18. O que fazer em abordagem?"); r4=TextInput(label="19. Por que entrar no RP? Mín 10 linhas."); r5=TextInput(label="20. Descreva um RP completo")
    async def on_submit(self, i):
        db["whitelist"][str(self.uid)]["e4"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save()
        if db["config"].get("whitelist_canal"): await bot.get_channel(db["config"]["whitelist_canal"]).send(f"📝 Nova Whitelist: {i.user.mention}")
        await i.response.send_message("✅ Enviada para análise!", ephemeral=True)

class ConfigModal(Modal, title="⚙️ Configurar Bot"):
    ticket_cat = TextInput(label="ID da Categoria de Ticket")
    staff_cargo = TextInput(label="ID do Cargo da Staff")
    whitelist_canal = TextInput(label="ID do Canal de Whitelist")
    transcript_canal = TextInput(label="ID do Canal de Repositório", required=False)
    
    async def on_submit(self, i):
        db["config"]["ticket_categoria"]=int(self.ticket_cat.value)
        db["config"]["staff_cargo"]=int(self.staff_cargo.value)
        db["config"]["whitelist_canal"]=int(self.whitelist_canal.value)
        if self.transcript_canal.value: db["config"]["transcript_canal"]=int(self.transcript_canal.value)
        save()
        await i.response.send_message("✅ Bot configurado!", ephemeral=True)

# ============ COMANDOS ============
@bot.tree.command(name="ticket", description="Painel de ticket")
async def ticket(i: discord.Interaction):
    embed = discord.Embed(title="🎫 CENTRAL DE ATENDIMENTO", description="""
💬 **Suporte:** erros ou pedidos de ajuda.
🤝 **Parcerias:** propostas e colaborações entre servidores.
🚨 **Denúncias:** usuários, mensagens ou comportamentos indevidos.
💰 **Pagamentos:** informações, dúvidas ou problemas com compras.
📞 **Seja Staff:** quer entrar para nossa equipe.
🚩 **Assumir Facção:** pedidos para liderar facções.
🚓 **Assumir Polícia:** pedidos para entrar na polícia.
❓ **Outros:** qualquer assunto não listado acima.

🕐 **Depois de abrir seu ticket, aguarde com paciência.**
""", color=0xFF0000)
    embed.set_image(url=BANNER_SUPORTE) # SUA BANNER DE SUPORTE
    embed.set_footer(text=bot.user.name, icon_url=BANNER_BOT) # FOTO DO BOT
    await i.channel.send(embed=embed, view=TicketPainel())
    await i.response.send_message("✅ Painel enviado", ephemeral=True)

@bot.tree.command(name="whitelist", description="Painel de whitelist")
async def whitelist(i: discord.Interaction):
    embed = discord.Embed(title="📝 WHITELIST", description="Clique no botão abaixo para fazer sua whitelist", color=0x57F287)
    embed.set_image(url=BANNER_BOT)
    await i.channel.send(embed=embed, view=WhitelistPainel())
    await i.response.send_message("✅ Enviado", ephemeral=True)

@bot.tree.command(name="logs", description="Criar canais de log")
async def logs(i: discord.Interaction):
    if i.user.id!= OWNER_ID: return await i.response.send_message("❌ Só o dono", ephemeral=True)
    cat1 = await i.guild.create_category("📁 LOGS RP")
    cat2 = await i.guild.create_category("📁 LOGS SERVIDOR")
    ch1 = await i.guild.create_text_channel("📜・rp", category=cat1)
    ch2 = await i.guild.create_text_channel("🛡️・servidor", category=cat2)
    db["config"]["logs_rp"]=ch1.id; db["config"]["logs_servidor"]=ch2.id; save()
    await i.response.send_message(f"✅ Logs criadas", ephemeral=True)

@bot.tree.command(name="config", description="Abrir painel de configuração")
async def config(i: discord.Interaction):
    if i.user.id!= OWNER_ID: return await i.response.send_message("❌ Só o dono", ephemeral=True)
    await i.response.send_modal(ConfigModal())

@bot.tree.command(name="antiraid", description="Ativar/Desativar anti-raid")
async def antiraid(i: discord.Interaction, ativo: bool):
    if i.user.id!= OWNER_ID: return await i.response.send_message("❌ Só o dono", ephemeral=True)
    db["config"]["antiraid"]=ativo; save()
    await i.response.send_message(f"✅ Anti-Raid: {'ATIVADO' if ativo else 'DESATIVADO'}", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ V70 ONLINE - COM BANNERS')

bot.run(os.getenv("TOKEN"))
