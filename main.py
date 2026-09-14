import discord
from discord.ext import commands
import os, json, asyncio, io
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online V90"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ARQUIVO = 'botdata.json'
try: db = json.load(open(ARQUIVO,'r',encoding='utf-8'))
except: db = {"config":{}, "tickets":{}, "whitelist":{}, "warns":{}}
def save(): json.dump(db, open(ARQUIVO,'w',encoding='utf-8'), ensure_ascii=False, indent=4)

OWNER_ID = 1438010935783460954
BANNER_VERMELHO = "https://cdn.discordapp.com/attachments/1481856611587723295/1549067503588606033/file_00000136881f58a07836a66e4246c.png"
BANNER_BOT = "https://cdn.discordapp.com/attachments/1481856611587723295/1549067503890866176/IMG_20260914_111956.jpg"

# ============ TICKET COM BLOQUEIO ============
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Suporte", emoji="💬"), discord.SelectOption(label="Parcerias", emoji="🤝"),
            discord.SelectOption(label="Denúncias", emoji="🚨"), discord.SelectOption(label="Pagamentos", emoji="💰"),
            discord.SelectOption(label="Seja Staff", emoji="📞"), discord.SelectOption(label="Assumir Facção", emoji="🚩"),
            discord.SelectOption(label="Assumir Polícia", emoji="🚓"), discord.SelectOption(label="Outros", emoji="❓")
        ]
        super().__init__(placeholder="📩 Selecione o motivo do seu ticket", min_values=1, max_values=1, options=options)
    async def callback(self, i: discord.Interaction):
        tipo = self.values[0]; user_id = str(i.user.id)
        if db["tickets"].get(user_id, {}).get(tipo):
            canal_id = db["tickets"][user_id][tipo]
            canal = i.guild.get_channel(canal_id)
            if canal: return await i.response.send_message(f"❌ Você já tem um ticket aberto de **{tipo}**: {canal.mention}", ephemeral=True)
            else: db["tickets"][user_id].pop(tipo); save()
        await i.response.send_modal(TicketMotivo(tipo))

class TicketPainel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None); self.add_item(TicketSelect())

class TicketAcoes(discord.ui.View):
    def __init__(self, user_id, tipo): super().__init__(timeout=None); self.user_id = user_id; self.tipo = tipo
    @discord.ui.button(label="✅ Assumir", style=discord.ButtonStyle.green)
    async def assumir(self, i, b):
        if not any(r.id == db["config"].get("staff_cargo") for r in i.user.roles): return await i.response.send_message("❌ Só STAFF", ephemeral=True)
        db["tickets"][str(i.channel.id)]["staff"] = i.user.id; save()
        await i.channel.set_permissions(i.guild.default_role, send_messages=False)
        await i.channel.set_permissions(i.user, send_messages=True)
        await i.channel.set_permissions(await bot.fetch_user(self.user_id), send_messages=True)
        await i.response.send_message(f"✅ Assumido por {i.user.mention}")
    @discord.ui.button(label="🔒 Fechar", style=discord.ButtonStyle.red)
    async def fechar(self, i, b): await i.response.send_modal(FecharMotivo(self.user_id, i.channel.id, self.tipo))

class FecharMotivo(discord.ui.Modal, title="Fechar Ticket"):
    motivo = discord.ui.TextInput(label="Motivo")
    def __init__(self, user_id, cid, tipo): super().__init__(); self.user_id=user_id; self.cid=cid; self.tipo=tipo
    async def on_submit(self, i):
        user = await bot.fetch_user(self.user_id); await user.send(f"🔒 Ticket de **{self.tipo}** fechado.\nMotivo: {self.motivo.value}")
        db["tickets"][str(self.user_id)].pop(self.tipo, None); db["tickets"].pop(str(self.cid), None); save()
        msgs = [f"[{m.created_at.strftime('%d/%m %H:%M')}] {m.author.name}: {m.content}" async for m in i.channel.history(limit=500)]
        file = discord.File(io.BytesIO("\n".join(reversed(msgs)).encode()), filename=f"ticket-{self.cid}.txt")
        if db["config"].get("transcript_canal"): await bot.get_channel(db["config"]["transcript_canal"]).send(f"📁 Repositório", file=file)
        await i.response.send_message("Fechando..."); await asyncio.sleep(3); await i.channel.delete()

class TicketMotivo(discord.ui.Modal):
    def __init__(self, tipo): super().__init__(title=f"Ticket: {tipo}"); self.tipo=tipo
    motivo = discord.ui.TextInput(label="Descreva", style=discord.TextStyle.paragraph)
    async def on_submit(self, i):
        if not db["config"].get("ticket_categoria"): return await i.response.send_message("❌ Configure com `!botconfig`", ephemeral=True)
        cat = bot.get_channel(db["config"]["ticket_categoria"])
        canal = await i.guild.create_text_channel(f"ticket-{self.tipo}-{i.user.name}", category=cat)
        await canal.set_permissions(i.guild.default_role, read_messages=False)
        await canal.set_permissions(i.user, read_messages=True, send_messages=True)
        if str(i.user.id) not in db["tickets"]: db["tickets"][str(i.user.id)] = {}
        db["tickets"][str(i.user.id)][self.tipo] = canal.id
        db["tickets"][str(canal.id)] = {"user": i.user.id, "staff": None, "tipo": self.tipo}; save()
        await canal.send(f"{i.user.mention}\n**Tipo:** {self.tipo}\n**Motivo:** {self.motivo.value}", view=TicketAcoes(i.user.id, self.tipo))
        await i.response.send_message(f"✅ Ticket: {canal.mention}", ephemeral=True)

# ============ WHITELIST COM APROVAR/REPROVAR ============
class WhitelistPainel(discord.ui.View):
    @discord.ui.button(label="📝 Fazer Whitelist", style=discord.ButtonStyle.success)
    async def fazer(self, i, b):
        user_data = db["whitelist"].get(str(i.user.id), {})
        if user_data.get("status") == "aprovado":
            return await i.response.send_message("❌ Você já foi aprovado na whitelist. Não pode fazer novamente.", ephemeral=True)
        if user_data.get("status") == "em_analise":
            return await i.response.send_message("⏳ Sua whitelist já está em análise. Aguarde a STAFF.", ephemeral=True)
        await i.response.send_modal(WhitelistEtapa1())

class WhitelistAcoesStaff(discord.ui.View):
    def __init__(self, user_id): super().__init__(timeout=None); self.user_id = user_id
    @discord.ui.button(label="✅ Aprovar", style=discord.ButtonStyle.green)
    async def aprovar(self, i, b):
        if not any(r.id == db["config"].get("staff_cargo") for r in i.user.roles): return await i.response.send_message("❌ Só STAFF", ephemeral=True)
        db["whitelist"][str(self.user_id)]["status"] = "aprovado"; save()
        user = await bot.fetch_user(self.user_id)
        await user.send("🎉 **PARABÉNS!** Sua whitelist foi **APROVADA**!\nVocê já pode entrar no servidor.")
        await i.response.edit_message(content=f"✅ Whitelist de {user.mention} **APROVADA** por {i.user.mention}", view=None)
    
    @discord.ui.button(label="❌ Reprovar", style=discord.ButtonStyle.red)
    async def reprovar(self, i, b):
        if not any(r.id == db["config"].get("staff_cargo") for r in i.user.roles): return await i.response.send_message("❌ Só STAFF", ephemeral=True)
        db["whitelist"][str(self.user_id)]["status"] = "reprovado"; save() # Libera pra fazer de novo
        user = await bot.fetch_user(self.user_id)
        await user.send("❌ Sua whitelist foi **REPROVADA**.\nVocê pode fazer novamente quando quiser.")
        await i.response.edit_message(content=f"❌ Whitelist de {user.mention} **REPROVADA** por {i.user.mention}\nO player pode tentar novamente.", view=None)

class WhitelistEtapa1(discord.ui.Modal, title="Whitelist 1/4"):
    r1=discord.ui.TextInput(label="1. O que é RDM?"); r2=discord.ui.TextInput(label="2. O que é VDM?"); r3=discord.ui.TextInput(label="3. Meta Gaming?"); r4=discord.ui.TextInput(label="4. Power Gaming?"); r5=discord.ui.TextInput(label="5. Combat Log?")
    async def on_submit(self, i): db["whitelist"][str(i.user.id)]={"e1":[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]}; save(); await i.response.send_modal(WhitelistEtapa2(i.user.id))
class WhitelistEtapa2(discord.ui.Modal, title="Whitelist 2/4"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=discord.ui.TextInput(label="6. Sequestro?"); r2=discord.ui.TextInput(label="7. Atirar de carro?"); r3=discord.ui.TextInput(label="8. Fear RP?"); r4=discord.ui.TextInput(label="9. Assalto?"); r5=discord.ui.TextInput(label="10. Favorecimento?")
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e2"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa3(self.uid))
class WhitelistEtapa3(discord.ui.Modal, title="Whitelist 3/4"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=discord.ui.TextInput(label="11. Roubar polícia?"); r2=discord.ui.TextInput(label="12. Anti RP?"); r3=discord.ui.TextInput(label="13. Idade facção?"); r4=discord.ui.TextInput(label="14. Tomar DM?"); r5=discord.ui.TextInput(label="15. Gatilho?")
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e3"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa4(self.uid))
class WhitelistEtapa4(discord.ui.Modal, title="Whitelist 4/4"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=discord.ui.TextInput(label="16. Info Discord?"); r2=discord.ui.TextInput(label="17. Coerência?"); r3=discord.ui.TextInput(label="18. Abordagem?"); r4=discord.ui.TextInput(label="19. Por que entrar? 10 linhas", style=discord.TextStyle.paragraph); r5=discord.ui.TextInput(label="20. RP completo", style=discord.TextStyle.paragraph)
    async def on_submit(self, i):
        uid = str(self.uid)
        db["whitelist"][uid]["e4"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]
        db["whitelist"][uid]["status"] = "em_analise"
        save()
        if db["config"].get("whitelist_canal"):
            canal = bot.get_channel(db["config"]["whitelist_canal"])
            embed = discord.Embed(title=f"📝 Nova Whitelist - {i.user.name}", color=0xFEE75C)
            embed.add_field(name="Status", value="Em análise", inline=False)
            await canal.send(f"{i.user.mention}", embed=embed, view=WhitelistAcoesStaff(uid))
        await i.response.send_message("✅ Whitelist enviada para análise da STAFF!", ephemeral=True)

# ============ COMANDOS ============
@bot.command(name="ticket")
async def ticket(ctx):
    embed = discord.Embed(
        title="🎫 Painel de Atendimento",
        description=(
            "Bem-vindo ao painel de suporte. Escolha abaixo o caminho que trouxe você até aqui:\n\n"
            "💬 **Suporte:** dúvidas, erros ou pedidos de ajuda.\n"
            "🤝 **Parcerias:** propostas e colaborações.\n"
            "🚨 **Denúncias:** usuários ou comportamentos indevidos.\n"
            "💰 **Pagamentos:** dúvidas ou problemas com compras.\n"
            "❓ **Outros:** qualquer assunto não listado.\n\n"
            "🕐 **Depois de abrir seu ticket, aguarde com paciência.**\n"
            "⚠️ **Você só pode ter 1 ticket aberto por categoria.**"
        ),
        color=0xFF0000
    )
    embed.set_image(url=BANNER_VERMELHO)
    embed.set_footer(text="PARADOXO ROLEPLAY")
    await ctx.send(embed=embed, view=TicketPainel())

@bot.command(name="whitelist")
async def whitelist(ctx):
    embed = discord.Embed(
        title="📝 WHITELIST PARADOXO RP",
        description="Clique no botão abaixo para iniciar sua whitelist.\n\n**Regras:**\n✅ Se for **APROVADO** não poderá fazer mais.\n🔄 Se for **REPROVADO** poderá tentar novamente.",
        color=0x57F287
    )
    embed.set_image(url=BANNER_BOT)
    await ctx.send(embed=embed, view=WhitelistPainel())

@bot.command(name="botconfig")
@commands.check(lambda ctx: ctx.author.id == OWNER_ID)
async def botconfig(ctx):
    msg = await ctx.send("⚙️ Manda os 3 IDs:\n1. Categoria Ticket\n2. Cargo Staff\n3. Canal Whitelist")
    def check(m): return m.author.id == OWNER_ID and m.channel == ctx.channel
    try:
        cat = await bot.wait_for('message', timeout=60.0, check=check); db["config"]["ticket_categoria"] = int(cat.content)
        staff = await bot.wait_for('message', timeout=60.0, check=check); db["config"]["staff_cargo"] = int(staff.content)
        wl = await bot.wait_for('message', timeout=60.0, check=check); db["config"]["whitelist_canal"] = int(wl.content)
        save(); await ctx.send("✅ Configurado!")
    except: await ctx.send("❌ Tempo acabou ou ID inválido")

@bot.event
async def on_ready(): print(f'✅ V90 ONLINE')

bot.run(os.getenv("TOKEN"))
