import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Modal, TextInput
import os, json, asyncio, io
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online V87"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
intents.message_content = True
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
        super().__init__(placeholder="🎫 Selecione o motivo do seu ticket", min_values=1, max_values=1, options=options)
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
    motivo = TextInput(label="Motivo")
    def __init__(self, user_id, cid, tipo): super().__init__(); self.user_id=user_id; self.cid=cid; self.tipo=tipo
    async def on_submit(self, i):
        user = await bot.fetch_user(self.user_id); await user.send(f"🔒 Fechado. Motivo: {self.motivo.value}")
        msgs = [f"[{m.created_at.strftime('%d/%m %H:%M')}] {m.author.name}: {m.content}" async for m in i.channel.history(limit=500)]
        file = discord.File(io.BytesIO("\n".join(reversed(msgs)).encode()), filename=f"ticket-{self.cid}.txt")
        if db["config"].get("transcript_canal"): await bot.get_channel(db["config"]["transcript_canal"]).send(f"📁 Repositório", file=file)
        await i.response.send_message("Fechando..."); await asyncio.sleep(3); await i.channel.delete()

class TicketMotivo(Modal):
    def __init__(self, tipo): super().__init__(title=f"Ticket: {tipo}"); self.tipo=tipo
    motivo = TextInput(label="Descreva", style=discord.TextStyle.paragraph)
    async def on_submit(self, i):
        if not db["config"].get("ticket_categoria"): return await i.response.send_message("❌ Configure com!botconfig", ephemeral=True)
        cat = bot.get_channel(db["config"]["ticket_categoria"])
        canal = await i.guild.create_text_channel(f"ticket-{self.tipo}-{i.user.name}", category=cat)
        await canal.set_permissions(i.guild.default_role, read_messages=False)
        await canal.set_permissions(i.user, read_messages=True, send_messages=True)
        db["tickets"][str(canal.id)] = {"user": i.user.id, "staff": None, "tipo": self.tipo}; save()
        await canal.send(f"{i.user.mention}\n**Tipo:** {self.tipo}\n**Motivo:** {self.motivo.value}", view=TicketAcoes(i.user.id, self.tipo))
        await i.response.send_message(f"✅ Ticket: {canal.mention}", ephemeral=True)

# ============ WHITELIST ============
class WhitelistPainel(View):
    @discord.ui.button(label="📝 Fazer Whitelist", style=discord.ButtonStyle.success)
    async def fazer(self, i, b): await i.response.send_modal(WhitelistEtapa1())
class WhitelistEtapa1(Modal, title="Whitelist 1/4"):
    r1=TextInput(label="1. O que é RDM?"); r2=TextInput(label="2. O que é VDM?"); r3=TextInput(label="3. Meta Gaming?"); r4=TextInput(label="4. Power Gaming?"); r5=TextInput(label="5. Combat Log?")
    async def on_submit(self, i): db["whitelist"][str(i.user.id)]={"e1":[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]}; save(); await i.response.send_modal(WhitelistEtapa2(i.user.id))
class WhitelistEtapa2(Modal, title="Whitelist 2/4"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=TextInput(label="6. Sequestro?"); r2=TextInput(label="7. Atirar de carro?"); r3=TextInput(label="8. Fear RP?"); r4=TextInput(label="9. Assalto?"); r5=TextInput(label="10. Favorecimento?")
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e2"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa3(self.uid))
class WhitelistEtapa3(Modal, title="Whitelist 3/4"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=TextInput(label="11. Roubar polícia?"); r2=TextInput(label="12. Anti RP?"); r3=TextInput(label="13. Idade facção?"); r4=TextInput(label="14. Tomar DM?"); r5=TextInput(label="15. Gatilho?")
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e3"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa4(self.uid))
class WhitelistEtapa4(Modal, title="Whitelist 4/4"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=TextInput(label="16. Info Discord?"); r2=TextInput(label="17. Coerência?"); r3=TextInput(label="18. Abordagem?"); r4=TextInput(label="19. Por que entrar? 10 linhas", style=discord.TextStyle.paragraph); r5=TextInput(label="20. RP completo", style=discord.TextStyle.paragraph)
    async def on_submit(self, i):
        db["whitelist"][str(self.uid)]["e4"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save()
        if db["config"].get("whitelist_canal"): await bot.get_channel(db["config"]["whitelist_canal"]).send(f"📝 Nova Whitelist: {i.user.mention}")
        await i.response.send_message("✅ Enviada pra STAFF!", ephemeral=True)

# ============ CONFIG COM TRATAMENTO DE ERRO ============
class BotConfigView(View):
    def __init__(self): super().__init__(timeout=180)
    @discord.ui.button(label="📂 Categoria Ticket", style=discord.ButtonStyle.primary)
    async def btn_categoria(self, i, b): await i.response.send_modal(SetCategoriaModal())
    @discord.ui.button(label="👮 Cargo Staff", style=discord.ButtonStyle.primary)
    async def btn_staff(self, i, b): await i.response.send_modal(SetStaffModal())
    @discord.ui.button(label="📝 Canal Whitelist", style=discord.ButtonStyle.primary)
    async def btn_whitelist(self, i, b): await i.response.send_modal(SetWhitelistModal())

class SetCategoriaModal(Modal, title="Categoria de Ticket"):
    id_input = TextInput(label="Cole o ID da Categoria")
    async def on_submit(self, i):
        try: db["config"]["ticket_categoria"] = int(self.id_input.value); save()
        except: return await i.response.send_message("❌ ID inválido! Só números", ephemeral=True)
        await i.response.send_message(f"✅ Categoria: <#{self.id_input.value}>", ephemeral=True)

class SetStaffModal(Modal, title="Cargo da Staff"):
    id_input = TextInput(label="Cole o ID do Cargo")
    async def on_submit(self, i):
        try: db["config"]["staff_cargo"] = int(self.id_input.value); save()
        except: return await i.response.send_message("❌ ID inválido! Só números", ephemeral=True)
        await i.response.send_message(f"✅ Cargo: <@&{self.id_input.value}>", ephemeral=True)

class SetWhitelistModal(Modal, title="Canal de Whitelist"):
    id_input = TextInput(label="Cole o ID do Canal")
    async def on_submit(self, i):
        try: db["config"]["whitelist_canal"] = int(self.id_input.value); save()
        except: return await i.response.send_message("❌ ID inválido! Só números", ephemeral=True)
        await i.response.send_message(f"✅ Canal: <#{self.id_input.value}>", ephemeral=True)

def is_owner(ctx): return ctx.author.id == OWNER_ID
def is_staff(ctx): return any(r.id == db["config"].get("staff_cargo") for r in ctx.author.roles) or ctx.author.id == OWNER_ID

# ============ COMANDOS ============
@bot.command(name="ticket")
async def ticket(ctx):
    embed = discord.Embed(title="🎫 CENTRAL DE ATENDIMENTO", color=0xFF0000)
    embed.set_image(url=BANNER_SUPORTE)
    embed.set_footer(text=bot.user.name, icon_url=BANNER_BOT)
    await ctx.send(embed=embed, view=TicketPainel())

@bot.command(name="whitelist")
async def whitelist(ctx):
    embed = discord.Embed(title="📝 WHITELIST PARADOXO RP", color=0x57F287)
    embed.set_image(url=BANNER_BOT)
    await ctx.send(embed=embed, view=WhitelistPainel())

@bot.command(name="botconfig")
@commands.check(is_owner)
async def botconfig(ctx):
    embed = discord.Embed(title="⚙️ PAINEL DE CONFIGURAÇÃO", color=0x5865F2)
    embed.add_field(name="Categoria Ticket", value=f"<#{db['config'].get('ticket_categoria', 'Não definido')}>", inline=False)
    embed.add_field(name="Cargo Staff", value=f"<@&{db['config'].get('staff_cargo', 'Não definido')}>", inline=False)
    embed.add_field(name="Canal Whitelist", value=f"<#{db['config'].get('whitelist_canal', 'Não definido')}>", inline=False)
    await ctx.send(embed=embed, view=BotConfigView())

@bot.command(name="clear")
@commands.check(is_staff)
async def clear(ctx, q: int): await ctx.channel.purge(limit=q); await ctx.send(f"✅ {q} apagadas", delete_after=3)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando não encontrado. Use: `!ticket` `!whitelist` `!botconfig`")

@bot.event
async def on_ready():
    await bot.add_cog(commands.Cog())
    print(f'✅ V87 ONLINE - COMANDOS! CARREGADOS')

bot.run(os.getenv("TOKEN"))
