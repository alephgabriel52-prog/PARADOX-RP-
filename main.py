import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Modal, TextInput, Button
import os, json, asyncio, io
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online V86"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
intents.message_content = True # ESSENCIAL PRO! FUNCIONAR
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
            discord.SelectOption(label="Suporte", emoji="💬", description="Dúvidas e ajuda"),
            discord.SelectOption(label="Parceria", emoji="🤝", description="Parcerias"),
            discord.SelectOption(label="Denúncia", emoji="🚨", description="Denunciar player"),
            discord.SelectOption(label="Pagamento", emoji="💰", description="Problemas com compra"),
            discord.SelectOption(label="Seja Staff", emoji="📞", description="Quero ser staff"),
            discord.SelectOption(label="Assumir Facção", emoji="🚩", description="Liderar facção"),
            discord.SelectOption(label="Assumir Polícia", emoji="🚓", description="Entrar na PM"),
            discord.SelectOption(label="Outros", emoji="❓", description="Outros assuntos")
        ]
        super().__init__(placeholder="🎫 Selecione o motivo do seu ticket", min_values=1, max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction): await interaction.response.send_modal(TicketMotivo(self.values[0]))

class TicketPainel(View):
    def __init__(self): super().__init__(timeout=None); self.add_item(TicketSelect())

class TicketAcoes(View):
    def __init__(self, user_id, tipo): super().__init__(timeout=None); self.user_id = user_id; self.tipo = tipo
    @discord.ui.button(label="✅ Assumir", style=discord.ButtonStyle.green, emoji="✅")
    async def assumir(self, i, b):
        if not any(r.id == db["config"].get("staff_cargo") for r in i.user.roles): return await i.response.send_message("❌ Só STAFF", ephemeral=True)
        db["tickets"][str(i.channel.id)]["staff"] = i.user.id; save()
        await i.channel.set_permissions(i.guild.default_role, send_messages=False, view_channel=True)
        await i.channel.set_permissions(i.user, send_messages=True, view_channel=True)
        await i.channel.set_permissions(await bot.fetch_user(self.user_id), send_messages=True, view_channel=True)
        await i.response.send_message(f"✅ Ticket assumido por {i.user.mention}")
    @discord.ui.button(label="🔒 Fechar", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, i, b): await i.response.send_modal(FecharMotivo(self.user_id, i.channel.id, self.tipo))

class FecharMotivo(Modal, title="Fechar Ticket"):
    motivo = TextInput(label="Motivo do fechamento", style=discord.TextStyle.paragraph)
    def __init__(self, user_id, cid, tipo): super().__init__(); self.user_id=user_id; self.cid=cid; self.tipo=tipo
    async def on_submit(self, i):
        user = await bot.fetch_user(self.user_id); await user.send(f"🔒 Seu ticket de {self.tipo} foi fechado.\nMotivo: {self.motivo.value}")
        msgs = [f"[{m.created_at.strftime('%d/%m %H:%M')}] {m.author.name}: {m.content}" async for m in i.channel.history(limit=500)]
        file = discord.File(io.BytesIO("\n".join(reversed(msgs)).encode()), filename=f"ticket-{self.cid}.txt")
        if db["config"].get("transcript_canal"): await bot.get_channel(db["config"]["transcript_canal"]).send(f"📁 Repositório - {self.tipo} - {user.name}", file=file)
        await i.response.send_message("Fechando em 3s..."); await asyncio.sleep(3); await i.channel.delete()

class TicketMotivo(Modal):
    def __init__(self, tipo): super().__init__(title=f"Ticket: {tipo}"); self.tipo=tipo
    motivo = TextInput(label="Descreva seu problema", style=discord.TextStyle.paragraph, max_length=1000)
    async def on_submit(self, i):
        if not db["config"].get("ticket_categoria"): return await i.response.send_message("❌ Configure a categoria com `!botconfig` primeiro", ephemeral=True)
        cat = bot.get_channel(db["config"]["ticket_categoria"])
        canal = await i.guild.create_text_channel(f"ticket-{self.tipo}-{i.user.name}", category=cat)
        await canal.set_permissions(i.guild.default_role, read_messages=False)
        await canal.set_permissions(i.user, read_messages=True, send_messages=True)
        db["tickets"][str(canal.id)] = {"user": i.user.id, "staff": None, "tipo": self.tipo}; save()
        await canal.send(f"{i.user.mention}\n**Tipo:** {self.tipo}\n**Motivo:** {self.motivo.value}", view=TicketAcoes(i.user.id, self.tipo))
        await i.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

# ============ WHITELIST 4 ETAPAS ============
class WhitelistPainel(View):
    @discord.ui.button(label="📝 Fazer Whitelist", style=discord.ButtonStyle.success, emoji="📝")
    async def fazer(self, i, b): await i.response.send_modal(WhitelistEtapa1())
class WhitelistEtapa1(Modal, title="Whitelist 1/4 - Regras Básicas"):
    r1=TextInput(label="1. O que é RDM?"); r2=TextInput(label="2. O que é VDM?"); r3=TextInput(label="3. Meta Gaming?"); r4=TextInput(label="4. Power Gaming?"); r5=TextInput(label="5. Combat Log?")
    async def on_submit(self, i): db["whitelist"][str(i.user.id)]={"e1":[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]}; save(); await i.response.send_modal(WhitelistEtapa2(i.user.id))
class WhitelistEtapa2(Modal, title="Whitelist 2/4 - RP"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=TextInput(label="6. Sequestro?"); r2=TextInput(label="7. Atirar de carro?"); r3=TextInput(label="8. Fear RP?"); r4=TextInput(label="9. Assalto?"); r5=TextInput(label="10. Favorecimento?")
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e2"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa3(self.uid))
class WhitelistEtapa3(Modal, title="Whitelist 3/4 - Facção"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=TextInput(label="11. Roubar polícia?"); r2=TextInput(label="12. Anti RP?"); r3=TextInput(label="13. Idade mínima facção?"); r4=TextInput(label="14. Tomar DM?"); r5=TextInput(label="15. Gatilho?")
    async def on_submit(self, i): db["whitelist"][str(self.uid)]["e3"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save(); await i.response.send_modal(WhitelistEtapa4(self.uid))
class WhitelistEtapa4(Modal, title="Whitelist 4/4 - Final"):
    def __init__(self, uid): super().__init__(); self.uid=uid
    r1=TextInput(label="16. Info Discord?"); r2=TextInput(label="17. Coerência?"); r3=TextInput(label="18. Abordagem policial?"); r4=TextInput(label="19. Por que entrar? Mín 10 linhas", style=discord.TextStyle.paragraph); r5=TextInput(label="20. RP completo", style=discord.TextStyle.paragraph)
    async def on_submit(self, i):
        db["whitelist"][str(self.uid)]["e4"]=[self.r1.value,self.r2.value,self.r3.value,self.r4.value,self.r5.value]; save()
        if db["config"].get("whitelist_canal"): await bot.get_channel(db["config"]["whitelist_canal"]).send(f"📝 Nova Whitelist de {i.user.mention}")
        await i.response.send_message("✅ Whitelist enviada para análise da STAFF!", ephemeral=True)

# ============ PAINEL DE CONFIG ============
class BotConfigView(View):
    def __init__(self): super().__init__(timeout=180)
    @discord.ui.button(label="📂 Categoria Ticket", style=discord.ButtonStyle.primary)
    async def btn_categoria(self, i, b): await i.response.send_modal(SetCategoriaModal())
    @discord.ui.button(label="👮 Cargo Staff", style=discord.ButtonStyle.primary)
    async def btn_staff(self, i, b): await i.response.send_modal(SetStaffModal())
    @discord.ui.button(label="📝 Canal Whitelist", style=discord.ButtonStyle.primary)
    async def btn_whitelist(self, i, b): await i.response.send_modal(SetWhitelistModal())
    @discord.ui.button(label="📁 Canal Repositório", style=discord.ButtonStyle.primary)
    async def btn_repo(self, i, b): await i.response.send_modal(SetRepoModal())

class SetCategoriaModal(Modal, title="Categoria de Ticket"):
    id_input = TextInput(label="Cole o ID da Categoria")
    async def on_submit(self, i): db["config"]["ticket_categoria"] = int(self.id_input.value); save(); await i.response.send_message(f"✅ Categoria: <#{self.id_input.value}>", ephemeral=True)
class SetStaffModal(Modal, title="Cargo da Staff"):
    id_input = TextInput(label="Cole o ID do Cargo")
    async def on_submit(self, i): db["config"]["staff_cargo"] = int(self.id_input.value); save(); await i.response.send_message(f"✅ Cargo: <@&{self.id_input.value}>", ephemeral=True)
class SetWhitelistModal(Modal, title="Canal de Whitelist"):
    id_input = TextInput(label="Cole o ID do Canal")
    async def on_submit(self, i): db["config"]["whitelist_canal"] = int(self.id_input.value); save(); await i.response.send_message(f"✅ Canal: <#{self.id_input.value}>", ephemeral=True)
class SetRepoModal(Modal, title="Canal de Repositório"):
    id_input = TextInput(label="Cole o ID do Canal")
    async def on_submit(self, i): db["config"]["transcript_canal"] = int(self.id_input.value); save(); await i.response.send_message(f"✅ Canal: <#{self.id_input.value}>", ephemeral=True)

def is_owner_check():
    async def predicate(i: discord.Interaction):
        if i.user.id == OWNER_ID: return True
        await i.response.send_message("❌ Só o dono", ephemeral=True); return False
    return app_commands.check(predicate)
def is_owner(ctx): return ctx.author.id == OWNER_ID
def is_staff(ctx): return any(r.id == db["config"].get("staff_cargo") for r in ctx.author.roles) or ctx.author.id == OWNER_ID

# ============ COMANDOS ============
@bot.command(name="ticket")
async def ticket_prefix(ctx):
    embed = discord.Embed(title="🎫 CENTRAL DE ATENDIMENTO", description="Escolha uma das opções abaixo:", color=0xFF0000)
    embed.set_image(url=BANNER_SUPORTE)
    embed.set_footer(text=bot.user.name, icon_url=BANNER_BOT)
    await ctx.send(embed=embed, view=TicketPainel())

@bot.command(name="whitelist")
async def whitelist_prefix(ctx):
    embed = discord.Embed(title="📝 WHITELIST PARADOXO RP", description="Clique no botão abaixo para iniciar", color=0x57F287)
    embed.set_image(url=BANNER_BOT)
    await ctx.send(embed=embed, view=WhitelistPainel())

@bot.command(name="botconfig")
@commands.check(is_owner)
async def botconfig_prefix(ctx):
    embed = discord.Embed(title="⚙️ PAINEL DE CONFIGURAÇÃO", color=0x5865F2)
    embed.add_field(name="Categoria Ticket", value=f"<#{db['config'].get('ticket_categoria', 'Não definido')}>", inline=True)
    embed.add_field(name="Cargo Staff", value=f"<@&{db['config'].get('staff_cargo', 'Não definido')}>", inline=True)
    embed.add_field(name="Canal Whitelist", value=f"<#{db['config'].get('whitelist_canal', 'Não definido')}>", inline=True)
    await ctx.send(embed=embed, view=BotConfigView())

@bot.command(name="clear")
@commands.check(is_staff)
async def clear(ctx, q: int): await ctx.channel.purge(limit=q); await ctx.send(f"✅ {q} apagadas", delete_after=3)
@bot.command(name="kick")
@commands.check(is_staff)
async def kick(ctx, m: discord.Member, *, motivo="Sem motivo"): await m.kick(reason=motivo); await ctx.send(f"👢 {m.mention} expulso")
@bot.command(name="ban")
@commands.check(is_staff)
async def ban(ctx, m: discord.Member, *, motivo="Sem motivo"): await m.ban(reason=motivo); await ctx.send(f"🔨 {m.mention} banido")

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f'✅ V86 ONLINE -!ticket!whitelist!botconfig')

bot.run(os.getenv("TOKEN"))
