import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Modal, TextInput
import os, json, asyncio, io
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online V82"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

ARQUIVO = 'botdata.json'
try: db = json.load(open(ARQUIVO,'r',encoding='utf-8'))
except: db = {"config":{}, "tickets":{}, "whitelist":{}, "warns":{}}
def save(): json.dump(db, open(ARQUIVO,'w',encoding='utf-8'), ensure_ascii=False, indent=4)

OWNER_ID = 1438010935783460954
GUILD_ID = 1526291625763143770

BANNER_SUPORTE = "https://cdn.discordapp.com/attachments/1481856611587723295/1549067503588606033/file_00000136881f58a07836a66e4246c.png?ex=6aa95909&is=6aa80789&hm=bdc18d543ecb36c4417854a67c81826d27438297b74e41549a177b1843797a43"
BANNER_BOT = "https://cdn.discordapp.com/attachments/1481856611587723295/1549067503890866176/IMG_20260914_111956.jpg?ex=6aa95909&is=6aa80789&hm=e56e7317913f32b44715d63482cabc005132d429ed7e0eb7a61f7ab3c2e56181"

# ============ TICKET ============
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Suporte", emoji="💬"), discord.SelectOption(label="Parceria", emoji="🤝"),
            discord.SelectOption(label="Denúncia", emoji="🚨"), discord.SelectOption(label="Pagamento", emoji="💰"),
            discord.SelectOption(label="Seja Staff", emoji="📞"), discord.SelectOption(label="Assumir Facção", emoji="🚩"),
            discord.SelectOption(label="Assumir Polícia", emoji="🚓"), discord.SelectOption(label="Outros", emoji="❓")
        ]
        super().__init__(placeholder="Selecione o motivo do seu ticket", min_values=1, max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction): await interaction.response.send_modal(TicketMotivo(self.values[0]))

class TicketPainel(View):
    def __init__(self): super().__init__(timeout=None); self.add_item(TicketSelect())

class TicketAcoes(View):
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

class FecharMotivo(Modal, title="Fechar Ticket"):
    motivo = TextInput(label="Motivo", style=discord.TextStyle.paragraph)
    def __init__(self, user_id, cid, tipo): super().__init__(); self.user_id=user_id; self.cid=cid; self.tipo=tipo
    async def on_submit(self, i):
        user = await bot.fetch_user(self.user_id); await user.send(f"🔒 Fechado. Motivo: {self.motivo.value}")
        msgs = [f"[{m.created_at.strftime('%d/%m %H:%M')}] {m.author.name}: {m.content}" async for m in i.channel.history(limit=500)]
        file = discord.File(io.BytesIO("\n".join(reversed(msgs)).encode()), filename=f"ticket-{self.cid}.txt")
        if db["config"].get("transcript_canal"): await bot.get_channel(db["config"]["transcript_canal"]).send(f"📁 Repositório - {self.tipo}", file=file)
        await i.response.send_message("Fechando..."); await asyncio.sleep(3); await i.channel.delete()

class TicketMotivo(Modal):
    def __init__(self, tipo): super().__init__(title=f"Ticket: {tipo}"); self.tipo=tipo
    motivo = TextInput(label="Descreva", style=discord.TextStyle.paragraph)
    async def on_submit(self, i):
        if not db["config"].get("ticket_categoria"): return await i.response.send_message("❌ Configure /config primeiro", ephemeral=True)
        cat = bot.get_channel(db["config"]["ticket_categoria"])
        canal = await i.guild.create_text_channel(f"ticket-{self.tipo}-{i.user.name}", category=cat)
        await canal.set_permissions(i.guild.default_role, read_messages=False)
        await canal.set_permissions(i.user, read_messages=True, send_messages=True)
        db["tickets"][str(canal.id)] = {"user": i.user.id, "staff": None, "tipo": self.tipo}; save()
        await canal.send(f"{i.user.mention}\n**Tipo:** {self.tipo}\n**Motivo:** {self.motivo.value}", view=TicketAcoes(i.user.id, self.tipo))
        await i.response.send_message(f"✅ Ticket: {canal.mention}", ephemeral=True)

# ============ WHITELIST 4 ETAPAS ============
class WhitelistPainel(View):
    @discord.ui.button(label="📝 Fazer Whitelist", style=discord.ButtonStyle.success)
    async def fazer(self, i, b): await i.response.send_modal(WhitelistEtapa1())
class WhitelistEtapa1(Modal, title="Whitelist 1/4"):
    r1=TextInput(label="1. O que é RDM?"); r2=TextInput(label="2. O que é VDM?"); r3=TextInput(label="3. Meta Gaming?"); r4=TextInput(label="4. Power Gaming?"); r5=TextInput(label="5. Combat Log?")
    async def on_submit(self, i): db["whitelist"][str(i.user.id)]={"e1":[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]}; save(); await i.response.send_modal(WhitelistEtapa2(i.user.id))
class WhitelistEtapa2(Modal):
    def __init__(self, uid): super().__init__(title="Whitelist 2/4"); self.uid=uid
    r1=TextInput(label="6. Sequestro?"); r2=TextInput(label="7. Atirar de carro?"); r3=TextInput(label="8. Fear RP?"); r4=TextInput(label="9. Assalto?"); r5=TextInput(label="10. Favorecimento?")
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e2"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa3(self.uid))
class WhitelistEtapa3(Modal):
    def __init__(self, uid): super().__init__(title="Whitelist 3/4"); self.uid=uid
    r1=TextInput(label="11. Roubar polícia?"); r2=TextInput(label="12. Anti RP?"); r3=TextInput(label="13. Idade facção?"); r4=TextInput(label="14. Tomar DM?"); r5=TextInput(label="15. Gatilho?")
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e3"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa4(self.uid))
class WhitelistEtapa4(Modal):
    def __init__(self, uid): super().__init__(title="Whitelist 4/4"); self.uid=uid
    r1=TextInput(label="16. Info Discord?"); r2=TextInput(label="17. Coerência?"); r3=TextInput(label="18. Abordagem?"); r4=TextInput(label="19. Por que entrar? 10 linhas"); r5=TextInput(label="20. RP completo")
    async def on_submit(self, i):
        db["whitelist"][str(self.uid)]["e4"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save()
        if db["config"].get("whitelist_canal"): await bot.get_channel(db["config"]["whitelist_canal"]).send(f"📝 Nova Whitelist: {i.user.mention}")
        await i.response.send_message("✅ Enviada pra STAFF!", ephemeral=True)

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
        await i.response.send_message("✅ Configurado com sucesso!", ephemeral=True)

def is_owner():
    async def predicate(i: discord.Interaction):
        if i.user.id == OWNER_ID: return True
        await i.response.send_message("❌ Só o dono do bot", ephemeral=True)
        return False
    return app_commands.check(predicate)

def is_staff():
    async def predicate(i: discord.Interaction):
        if any(r.id == db["config"].get("staff_cargo") for r in i.user.roles) or i.user.id == OWNER_ID:
            return True
        await i.response.send_message("❌ Você não tem permissão!", ephemeral=True)
        return False
    return app_commands.check(predicate)

# ============ COMANDOS ============
@bot.tree.command(name="ticket", description="Abre o painel de ticket", guild=discord.Object(id=GUILD_ID))
async def ticket(i: discord.Interaction):
    embed = discord.Embed(title="🎫 CENTRAL DE ATENDIMENTO", description="Selecione abaixo o motivo do seu atendimento", color=0xFF0000)
    embed.set_image(url=BANNER_SUPORTE)
    embed.set_footer(text=bot.user.name, icon_url=BANNER_BOT)
    await i.channel.send(embed=embed, view=TicketPainel())
    await i.response.send_message("✅ Painel enviado", ephemeral=True)

@bot.tree.command(name="whitelist", description="Abre o painel de whitelist", guild=discord.Object(id=GUILD_ID))
async def whitelist(i: discord.Interaction):
    embed = discord.Embed(title="📝 WHITELIST", description="Clique no botão abaixo para iniciar", color=0x57F287)
    embed.set_image(url=BANNER_BOT)
    await i.channel.send(embed=embed, view=WhitelistPainel())
    await i.response.send_message("✅ Painel enviado", ephemeral=True)

@bot.tree.command(name="config", description="Configure um ticket", guild=discord.Object(id=GUILD_ID))
@is_owner()
async def config(i: discord.Interaction):
    await i.response.send_modal(ConfigModal())

@bot.tree.command(name="config_painel", description="Configure um painel ticket", guild=discord.Object(id=GUILD_ID))
@is_owner()
async def config_painel(i: discord.Interaction):
    await i.response.send_message("Use `/ticket` para enviar o painel de ticket e `/whitelist` para enviar o painel de whitelist", ephemeral=True)

@bot.tree.command(name="botconfig", description="[Gerencie seu bot]", guild=discord.Object(id=GUILD_ID))
@is_owner()
async def botconfig(i: discord.Interaction):
    embed = discord.Embed(title="⚙️ PAINEL DO BOT", color=0x5865F2)
    embed.add_field(name="Ticket Categoria", value=f"<#{db['config'].get('ticket_categoria', 'Não definido')}>", inline=False)
    embed.add_field(name="Cargo Staff", value=f"<@&{db['config'].get('staff_cargo', 'Não definido')}>", inline=False)
    embed.add_field(name="Canal Whitelist", value=f"<#{db['config'].get('whitelist_canal', 'Não definido')}>", inline=False)
    embed.add_field(name="Anti-Raid", value="ON" if db["config"].get("antiraid") else "OFF", inline=False)
    await i.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="warn", guild=discord.Object(id=GUILD_ID))
@is_staff()
async def warn(i: discord.Interaction, membro: discord.Member, motivo: str):
    uid = str(membro.id)
    if uid not in db["warns"]: db["warns"][uid] = []
    db["warns"][uid].append({"motivo": motivo, "staff": i.user.name})
    save()
    await i.response.send_message(f"⚠️ {membro.mention} recebeu warn. Motivo: {motivo}")

@bot.tree.command(name="clear", guild=discord.Object(id=GUILD_ID))
@is_staff()
async def clear(i: discord.Interaction, quantidade: int):
    await i.channel.purge(limit=quantidade)
    await i.response.send_message(f"✅ {quantidade} mensagens apagadas", ephemeral=True)

@bot.tree.command(name="kick", guild=discord.Object(id=GUILD_ID))
@is_staff()
async def kick(i: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    await membro.kick(reason=motivo)
    await i.response.send_message(f"👢 {membro.mention} foi expulso")

@bot.tree.command(name="ban", guild=discord.Object(id=GUILD_ID))
@is_staff()
async def ban(i: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    await membro.ban(reason=motivo)
    await i.response.send_message(f"🔨 {membro.mention} foi banido")

@bot.tree.command(name="logs", guild=discord.Object(id=GUILD_ID))
@is_owner()
async def logs(i: discord.Interaction):
    cat1 = await i.guild.create_category("📁 LOGS RP")
    cat2 = await i.guild.create_category("📁 LOGS SERVIDOR")
    ch1 = await i.guild.create_text_channel("📜・rp", category=cat1)
    ch2 = await i.guild.create_text_channel("🛡️・servidor", category=cat2)
    db["config"]["logs_rp"]=ch1.id; db["config"]["logs_servidor"]=ch2.id; save()
    await i.response.send_message(f"✅ Logs criadas: {ch1.mention} e {ch2.mention}", ephemeral=True)

@bot.tree.command(name="antiraid", guild=discord.Object(id=GUILD_ID))
@is_owner()
async def antiraid(i: discord.Interaction, ativo: bool):
    db["config"]["antiraid"]=ativo; save()
    await i.response.send_message(f"✅ Anti-Raid: {'ON' if ativo else 'OFF'}", ephemeral=True)

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    bot.tree.clear_commands(guild=guild)
    await bot.tree.sync(guild=guild)
    print(f'✅ V82 ONLINE - ID: {GUILD_ID} - /config /config_painel /botconfig ADICIONADOS')

bot.run(os.getenv("TOKEN"))
