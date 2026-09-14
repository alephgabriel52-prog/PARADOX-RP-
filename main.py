import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Modal, TextInput, Button
import os, json, asyncio, io
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online V85"
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

# ... COLA TODO O CODIGO DO TICKET E WHITELIST DO V84 AQUI ...

# ============ PAINEL DE CONFIG ============
class BotConfigView(View):
    def __init__(self): super().__init__(timeout=180)
    
    @discord.ui.button(label="📂 Categoria Ticket", style=discord.ButtonStyle.primary, row=0)
    async def btn_categoria(self, i, b):
        await i.response.send_modal(SetCategoriaModal())
    
    @discord.ui.button(label="👮 Cargo Staff", style=discord.ButtonStyle.primary, row=0)
    async def btn_staff(self, i, b):
        await i.response.send_modal(SetStaffModal())
    
    @discord.ui.button(label="📝 Canal Whitelist", style=discord.ButtonStyle.primary, row=1)
    async def btn_whitelist(self, i, b):
        await i.response.send_modal(SetWhitelistModal())
    
    @discord.ui.button(label="📁 Canal Repositório", style=discord.ButtonStyle.primary, row=1)
    async def btn_repo(self, i, b):
        await i.response.send_modal(SetRepoModal())
    
    @discord.ui.button(label="🔒 Anti-Raid ON/OFF", style=discord.ButtonStyle.danger, row=2)
    async def btn_antiraid(self, i, b):
        db["config"]["antiraid"] = not db["config"].get("antiraid", False)
        save()
        await i.response.send_message(f"✅ Anti-Raid: {'ON' if db['config']['antiraid'] else 'OFF'}", ephemeral=True)

class SetCategoriaModal(Modal, title="Configurar Categoria de Ticket"):
    id_input = TextInput(label="Cole o ID da Categoria")
    async def on_submit(self, i):
        db["config"]["ticket_categoria"] = int(self.id_input.value); save()
        await i.response.send_message(f"✅ Categoria configurada: <#{self.id_input.value}>", ephemeral=True)

class SetStaffModal(Modal, title="Configurar Cargo da Staff"):
    id_input = TextInput(label="Cole o ID do Cargo")
    async def on_submit(self, i):
        db["config"]["staff_cargo"] = int(self.id_input.value); save()
        await i.response.send_message(f"✅ Cargo Staff configurado: <@&{self.id_input.value}>", ephemeral=True)

class SetWhitelistModal(Modal, title="Configurar Canal de Whitelist"):
    id_input = TextInput(label="Cole o ID do Canal")
    async def on_submit(self, i):
        db["config"]["whitelist_canal"] = int(self.id_input.value); save()
        await i.response.send_message(f"✅ Canal Whitelist: <#{self.id_input.value}>", ephemeral=True)

class SetRepoModal(Modal, title="Configurar Canal de Repositório"):
    id_input = TextInput(label="Cole o ID do Canal")
    async def on_submit(self, i):
        db["config"]["transcript_canal"] = int(self.id_input.value); save()
        await i.response.send_message(f"✅ Canal Repositório: <#{self.id_input.value}>", ephemeral=True)

def is_owner_check():
    async def predicate(i: discord.Interaction):
        if i.user.id == OWNER_ID: return True
        await i.response.send_message("❌ Só o dono do bot", ephemeral=True)
        return False
    return app_commands.check(predicate)

def is_owner(ctx): return ctx.author.id == OWNER_ID

# ============ COMANDOS ============
@bot.tree.command(name="botconfig", description="Painel para configurar o bot", guild=discord.Object(id=GUILD_ID))
@is_owner_check()
async def botconfig_slash(i: discord.Interaction):
    embed = discord.Embed(title="⚙️ PAINEL DE CONFIGURAÇÃO", description="Clique nos botões abaixo para configurar", color=0x5865F2)
    embed.add_field(name="Categoria Ticket", value=f"<#{db['config'].get('ticket_categoria', 'Não definido')}>", inline=True)
    embed.add_field(name="Cargo Staff", value=f"<@&{db['config'].get('staff_cargo', 'Não definido')}>", inline=True)
    embed.add_field(name="Canal Whitelist", value=f"<#{db['config'].get('whitelist_canal', 'Não definido')}>", inline=True)
    embed.add_field(name="Anti-Raid", value="ON" if db["config"].get("antiraid") else "OFF", inline=True)
    await i.response.send_message(embed=embed, view=BotConfigView(), ephemeral=True)

@bot.command(name="botconfig")
@commands.check(is_owner)
async def botconfig_prefix(ctx):
    embed = discord.Embed(title="⚙️ PAINEL DE CONFIGURAÇÃO", description="Clique nos botões abaixo para configurar", color=0x5865F2)
    embed.add_field(name="Categoria Ticket", value=f"<#{db['config'].get('ticket_categoria', 'Não definido')}>", inline=True)
    embed.add_field(name="Cargo Staff", value=f"<@&{db['config'].get('staff_cargo', 'Não definido')}>", inline=True)
    embed.add_field(name="Canal Whitelist", value=f"<#{db['config'].get('whitelist_canal', 'Não definido')}>", inline=True)
    embed.add_field(name="Anti-Raid", value="ON" if db["config"].get("antiraid") else "OFF", inline=True)
    await ctx.send(embed=embed, view=BotConfigView())

# ... COLA O RESTO DOS COMANDOS !ticket !whitelist !clear !kick !ban AQUI IGUAL V84 ...

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    bot.tree.clear_commands(guild=guild)
    await bot.tree.sync(guild=guild)
    print(f'✅ V85 ONLINE - /botconfig COM PAINEL')

bot.run(os.getenv("TOKEN"))
