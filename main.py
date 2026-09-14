import discord
from discord.ext import commands, tasks
import os, json, asyncio, io, datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online V96"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ARQUIVO = 'botdata.json'
try: db = json.load(open(ARQUIVO,'r',encoding='utf-8'))
except: db = {"config":{}, "tickets":{}, "whitelist":{}, "warns":{}, "anuncios":[]}
def save(): json.dump(db, open(ARQUIVO,'w',encoding='utf-8'), ensure_ascii=False, indent=4)

OWNER_ID = 1438010935783460954
BANNER_FAIXA = "https://cdn.discordapp.com/attachments/1527669780364918925/1549093554960474243/file_0005a0820e8df98c1974ab6ecc.png"

def is_staff():
    async def predicate(ctx):
        return any(r.id == db["config"].get("staff_cargo") for r in ctx.author.roles) or ctx.author.id == OWNER_ID
    return commands.check(predicate)

def is_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator or ctx.author.id == OWNER_ID
    return commands.check(predicate)

@tasks.loop(minutes=1)
async def verificar_anuncios():
    agora = datetime.datetime.now().strftime("%H:%M")
    for anuncio in db["anuncios"][:]:
        if anuncio["hora"] == agora:
            canal = bot.get_channel(anuncio["canal"])
            if canal:
                embed = discord.Embed(title="📢 ANÚNCIO", description=anuncio["mensagem"], color=0xFF0000)
                embed.set_image(url=BANNER_FAIXA)
                embed.set_footer(text=f"Agendado por {anuncio['autor']} • ID: {anuncio['id']}")
                await canal.send("@everyone", embed=embed)
            db["anuncios"].remove(anuncio); save()

@verificar_anuncios.before_loop
async def before(): await bot.wait_until_ready()

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
            if canal: return await i.response.send_message(f"❌ Você já tem um ticket aberto: {canal.mention}", ephemeral=True)
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
        await i.response.send_message(f"✅ Ticket assumido por {i.user.mention} <@&{db['config']['staff_cargo']}>")
    @discord.ui.button(label="🔒 Fechar", style=discord.ButtonStyle.red)
    async def fechar(self, i, b):
        if not any(r.id == db["config"].get("staff_cargo") for r in i.user.roles): return await i.response.send_message("❌ **SÓ STAFF PODE FECHAR**", ephemeral=True)
        await i.response.send_modal(FecharMotivo(self.user_id, i.channel.id, self.tipo))

class FecharMotivo(discord.ui.Modal, title="Fechar Ticket"):
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph)
    def __init__(self, user_id, cid, tipo): super().__init__(); self.user_id=user_id; self.cid=cid; self.tipo=tipo
    async def on_submit(self, i):
        user = await bot.fetch_user(self.user_id); await user.send(f"🔒 Ticket de **{self.tipo}** fechado.\nMotivo: {self.motivo.value}")
        msgs = [f"[{m.created_at.strftime('%d/%m %H:%M')}] {m.author.name}: {m.content}" async for m in i.channel.history(limit=500)]
        file = discord.File(io.BytesIO("\n".join(reversed(msgs)).encode('utf-8')), filename=f"transcript-{self.cid}.txt")
        embed = discord.Embed(title=f"📁 Transcript - {self.tipo}", color=0xFF0000)
        embed.set_image(url=BANNER_FAIXA)
        if db["config"].get("transcript_canal"): await bot.get_channel(db["config"]["transcript_canal"]).send(embed=embed, file=file)
        db["tickets"][str(self.user_id)].pop(self.tipo, None); db["tickets"].pop(str(self.cid), None); save()
        await i.response.send_message("🔒 Fechando..."); await asyncio.sleep(3); await i.channel.delete()

class TicketMotivo(discord.ui.Modal):
    def __init__(self, tipo): super().__init__(title=f"Ticket: {tipo}"); self.tipo=tipo
    motivo = discord.ui.TextInput(label="Descreva", style=discord.TextStyle.paragraph)
    async def on_submit(self, i):
        cat = bot.get_channel(db["config"]["ticket_categoria"])
        canal = await i.guild.create_text_channel(f"ticket-{self.tipo}-{i.user.name}", category=cat)
        await canal.set_permissions(i.guild.default_role, read_messages=False)
        await canal.set_permissions(i.user, read_messages=True, send_messages=True)
        if str(i.user.id) not in db["tickets"]: db["tickets"][str(i.user.id)] = {}
        db["tickets"][str(i.user.id)][self.tipo] = canal.id
        db["tickets"][str(canal.id)] = {"user": i.user.id, "staff": None, "tipo": self.tipo}; save()
        embed = discord.Embed(title=f"🎫 Ticket de {self.tipo}", description=f"{i.user.mention}\n**Tipo:** {self.tipo}\n**Motivo:** {self.motivo.value}\n\n<@&{db['config']['staff_cargo']}>", color=0xFF0000)
        embed.set_image(url=BANNER_FAIXA)
        await canal.send(content=f"{i.user.mention} <@&{db['config']['staff_cargo']}>", embed=embed, view=TicketAcoes(i.user.id, self.tipo))
        await i.response.send_message(f"✅ Ticket: {canal.mention}", ephemeral=True)

class WhitelistPainel(discord.ui.View):
    @discord.ui.button(label="📝 Fazer Whitelist", style=discord.ButtonStyle.success)
    async def fazer(self, i, b):
        if db["whitelist"].get(str(i.user.id), {}).get("status") == "aprovado": return await i.response.send_message("❌ Já aprovado.", ephemeral=True)
        if db["whitelist"].get(str(i.user.id), {}).get("status") == "em_analise": return await i.response.send_message("⏳ Em análise.", ephemeral=True)
        await i.response.send_modal(WhitelistEtapa1())

class WhitelistAcoesStaff(discord.ui.View):
    def __init__(self, user_id): super().__init__(timeout=None); self.user_id = user_id
    @discord.ui.button(label="✅ Aprovar", style=discord.ButtonStyle.green)
    async def aprovar(self, i, b):
        if not any(r.id == db["config"].get("staff_cargo") for r in i.user.roles): return await i.response.send_message("❌ Só STAFF", ephemeral=True)
        db["whitelist"][str(self.user_id)]["status"] = "aprovado"; save()
        await (await bot.fetch_user(self.user_id)).send("🎉 **APROVADO!**")
        await i.response.edit_message(content=f"✅ Aprovada por {i.user.mention}", view=None)
    @discord.ui.button(label="❌ Reprovar", style=discord.ButtonStyle.red)
    async def reprovar(self, i, b):
        if not any(r.id == db["config"].get("staff_cargo") for r in i.user.roles): return await i.response.send_message("❌ Só STAFF", ephemeral=True)
        db["whitelist"][str(self.user_id)]["status"] = "reprovado"; save()
        await (await bot.fetch_user(self.user_id)).send("❌ **REPROVADO!**")
        await i.response.edit_message(content=f"❌ Reprovada por {i.user.mention}", view=None)

class WhitelistEtapa1(discord.ui.Modal, title="Whitelist 1/4"):
    r1=discord.ui.TextInput(label="1. RDM?", required=True); r2=discord.ui.TextInput(label="2. VDM?", required=True); r3=discord.ui.TextInput(label="3. Meta Gaming?", required=True); r4=discord.ui.TextInput(label="4. Power Gaming?", required=True); r5=discord.ui.TextInput(label="5. Combat Log?", required=True)
    async def on_submit(self, i): db["whitelist"][str(i.user.id)]={"e1":[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]}; save(); await i.response.send_modal(WhitelistEtapa2(i.user.id))
class WhitelistEtapa2(discord.ui.Modal, title="Whitelist 2/4"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=discord.ui.TextInput(label="6. Sequestro?", required=True); r2=discord.ui.TextInput(label="7. Atirar de carro?", required=True); r3=discord.ui.TextInput(label="8. Fear RP?", required=True); r4=discord.ui.TextInput(label="9. Assalto?", required=True); r5=discord.ui.TextInput(label="10. Favorecimento?", required=True)
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e2"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa3(self.uid))
class WhitelistEtapa3(discord.ui.Modal, title="Whitelist 3/4"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=discord.ui.TextInput(label="11. Roubar polícia?", required=True); r2=discord.ui.TextInput(label="12. Anti RP?", required=True); r3=discord.ui.TextInput(label="13. Idade facção?", required=True); r4=discord.ui.TextInput(label="14. Tomar DM?", required=True); r5=discord.ui.TextInput(label="15. Gatilho?", required=True)
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e3"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa4(self.uid))
class WhitelistEtapa4(discord.ui.Modal, title="Whitelist 4/4"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=discord.ui.TextInput(label="16. Info Discord?", required=True); r2=discord.ui.TextInput(label="17. Coerência?", required=True); r3=discord.ui.TextInput(label="18. Abordagem?", required=True); r4=discord.ui.TextInput(label="19. Por que entrar? 10 linhas", style=discord.TextStyle.paragraph, required=True); r5=discord.ui.TextInput(label="20. RP completo", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, i):
        uid = str(self.uid)
        db["whitelist"][uid]["e4"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]
        db["whitelist"][uid]["status"] = "em_analise"; save()
        if db["config"].get("whitelist_canal"):
            canal = bot.get_channel(db["config"]["whitelist_canal"])
            embed = discord.Embed(title=f"📝 Nova Whitelist - {i.user.name}", color=0xFF0000)
            embed.set_image(url=BANNER_FAIXA)
            await canal.send(f"<@&{db['config']['staff_cargo']}>", embed=embed, view=WhitelistAcoesStaff(uid))
        await i.response.send_message("✅ Enviada!", ephemeral=True)

@bot.command(name="ticket")
async def ticket(ctx):
    embed = discord.Embed(title="🎫 Painel de Atendimento", description="Escolha o motivo abaixo.", color=0xFF0000)
    embed.set_image(url=BANNER_FAIXA)
    await ctx.send(embed=embed, view=TicketPainel())

@bot.command(name="whitelist")
async def whitelist(ctx):
    embed = discord.Embed(title="📝 WHITELIST PARADOXO RP", description="Clique para iniciar.\n✅ APROVADO = não faz mais\n🔄 REPROVADO = pode tentar", color=0xFF0000)
    embed.set_image(url=BANNER_FAIXA)
    await ctx.send(embed=embed, view=WhitelistPainel())

@bot.command(name="anuncio")
@is_admin()
async def anuncio(ctx):
    await ctx.send("📢 **Sistema de Anúncio**\n1. Manda o ID do CANAL")
    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    try:
        canal_msg = await bot.wait_for('message', timeout=60.0, check=check)
        canal_id = int(canal_msg.content)
        await ctx.send("2. Manda a MENSAGEM do anúncio")
        msg = await bot.wait_for('message', timeout=120.0, check=check)
        await ctx.send("3. Manda o HORÁRIO no formato HH:MM ex: 12:30")
        hora = await bot.wait_for('message', timeout=60.0, check=check)
        novo_id = len(db["anuncios"]) + 1
        db["anuncios"].append({"id": novo_id, "canal": canal_id, "mensagem": msg.content, "hora": hora.content, "autor": ctx.author.name})
        save()
        await ctx.send(f"✅ Anúncio **ID: {novo_id}** agendado para `{hora.content}` no canal <#{canal_id}>")
    except: await ctx.send("❌ Tempo acabou ou ID inválido")

@bot.command(name="anuncios")
@is_admin()
async def anuncios(ctx):
    if not db["anuncios"]: return await ctx.send("📭 Não tem nenhum anúncio agendado.")
    embed = discord.Embed(title="📢 Anúncios Agendados", color=0xFF0000)
    for a in db["anuncios"]:
        embed.add_field(name=f"ID: {a['id']} | ⏰ {a['hora']}", value=f"Canal: <#{a['canal']}>\nAutor: {a['autor']}\nMsg: {a['mensagem'][:50]}...", inline=False)
    embed.set_footer(text="Use!cancelaranuncio ID ou!adiaranuncio ID HH:MM")
    await ctx.send(embed=embed)

@bot.command(name="cancelaranuncio")
@is_admin()
async def cancelaranuncio(ctx, id: int):
    for a in db["anuncios"]:
        if a["id"] == id:
            db["anuncios"].remove(a); save()
            return await ctx.send(f"✅ Anúncio **ID: {id}** cancelado.")
    await ctx.send("❌ ID não encontrado.")

@bot.command(name="adiaranuncio")
@is_admin()
async def adiaranuncio(ctx, id: int, nova_hora: str):
    for a in db["anuncios"]:
        if a["id"] == id:
            hora_antiga = a["hora"]
            a["hora"] = nova_hora; save()
            return await ctx.send(f"✅ Anúncio **ID: {id}** adiado de `{hora_antiga}` para `{nova_hora}`")
    await ctx.send("❌ ID não encontrado.")

@bot.command(name="botconfig")
@commands.check(lambda ctx: ctx.author.id == OWNER_ID)
async def botconfig(ctx):
    await ctx.send("⚙️ Manda os 4 IDs:\n1. CATEGORIA Ticket\n2. CARGO Staff\n3. CANAL Whitelist\n4. CANAL Transcript")
    def check(m): return m.author.id == OWNER_ID and m.channel == ctx.channel
    try:
        cat = await bot.wait_for('message', timeout=60.0, check=check); db["config"]["ticket_categoria"] = int(cat.content)
        staff = await bot.wait_for('message', timeout=60.0, check=check); db["config"]["staff_cargo"] = int(staff.content)
        wl = await bot.wait_for('message', timeout=60.0, check=check); db["config"]["whitelist_canal"] = int(wl.content)
        trans = await bot.wait_for('message', timeout=60.0, check=check); db["config"]["transcript_canal"] = int(trans.content)
        save(); await ctx.send("✅ Configurado!")
    except: await ctx.send("❌ Erro")

@bot.event
async def on_ready():
    verificar_anuncios.start()
    print(f'✅ V96 ONLINE')

bot.run(os.getenv("TOKEN"))
