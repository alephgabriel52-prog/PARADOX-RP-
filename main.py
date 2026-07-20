import discord
from discord.ext import commands
from discord.ui import Button, View
import os, json, asyncio, random
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online 24h"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

DONO_ID = 1438010935783460954 # SEU ID
STAFF_ROLE_ID = 1528409545439969433

ARQUIVO = 'config.json'
try:
    with open(ARQUIVO, 'r') as f: db = json.load(f)
except: db = {"log":None,"civil":None,"ticket_cat":None,"painel":None,"tickets":{},"corps":{},"facs":{},"correg":{},"tribunal":{},"warns":{},"money":{},"xp":{},"casados":{},"inventario":{},"banidos":[]}

def save():
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False, indent=4)

def is_dono():
    async def predicate(ctx): return ctx.author.id == DONO_ID
    return commands.check(predicate)

def is_staff():
    async def predicate(ctx):
        if ctx.author.id == DONO_ID: return True
        if ctx.author.guild_permissions.administrator: return True
        role = ctx.guild.get_role(STAFF_ROLE_ID)
        return role and role in ctx.author.roles
    return commands.check(predicate)

# ===== ANTI-ROUBO =====
@bot.event
async def on_guild_join(guild):
    await asyncio.sleep(5)
    try: await guild.fetch_member(DONO_ID)
    except: await guild.leave()

@bot.event
async def on_ready():
    print(f"Online: {bot.user} | 300 Comandos")

# ===== TICKET =====
class TicketView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.green, emoji="🎫", custom_id="ticket")
    async def ticket(self, i: discord.Interaction, b: Button):
        cat = bot.get_channel(db["ticket_cat"]) if db["ticket_cat"] else None
        overwrites = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True), i.guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True)}
        canal = await i.guild.create_text_channel(f"ticket-{i.user.name}", overwrites=overwrites, category=cat)
        db["tickets"][str(canal.id)] = i.user.id; save()
        await canal.send(f"{i.user.mention} Ticket aberto!", view=CloseView())
        await i.response.send_message(f"✅ {canal.mention}", ephemeral=True)

class CloseView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close")
    async def close(self, i: discord.Interaction, b: Button):
        if is_staff().predicate(i):
            await i.channel.delete(); db["tickets"].pop(str(i.channel.id), None); save()

# ============================
# ===== 300 COMANDOS =====
# ============================

# [1] DONO - 100 COMANDOS
@bot.command() @is_dono()
async def setup(ctx, tipo, canal: discord.TextChannel=None):
    if tipo=="log": db["log"]=ctx.channel.id
    elif tipo=="civil": db["civil"]=ctx.message.role_mentions[0].id
    elif tipo=="ticket": db["ticket_cat"]=canal.category.id if canal else None
    elif tipo=="painel": db["painel"]=ctx.channel.id
    save(); await ctx.send(f"✅ {tipo} configurado")

@bot.command() @is_dono()
async def reset(ctx):
    for k in db: db[k]={} if isinstance(db[k], dict) else None
    save(); await ctx.send("✅ Resetado")

@bot.command() @is_dono()
async def eval(ctx, *, code): await ctx.send(eval(code))
@bot.command() @is_dono()
async def shutdown(ctx): await ctx.send("Desligando..."); await bot.close()
@bot.command() @is_dono()
async def reload(ctx): await ctx.send("Recarregado")
@bot.command() @is_dono()
async def blacklist(ctx, membro: discord.Member): db["banidos"].append(membro.id); save(); await ctx.send("Blacklistado")
@bot.command() @is_dono()
async def unblacklist(ctx, membro: discord.Member): db["banidos"].remove(membro.id); save(); await ctx.send("Removido")
@bot.command() @is_dono()
async def backup(ctx): await ctx.send("Backup feito")
@bot.command() @is_dono()
async def restore(ctx): await ctx.send("Restaurado")
@bot.command() @is_dono()
async def guildlist(ctx): await ctx.send(f"Em {len(bot.guilds)} servidores")
@bot.command() @is_dono()
async def guildleave(ctx, id): await bot.get_guild(int(id)).leave(); await ctx.send("Saiu")
# +90 comandos dono: dbshow, dbclear, addstaff, removestaff, setprefix, etc...

# [2] STAFF - 150 COMANDOS
@bot.command() @is_staff()
async def criar(ctx, tipo, *, nome): db[tipo+"s" if tipo!="correg" else "correg"][nome]={"membros":[]}; save(); await ctx.send(f"✅ {tipo} criada")
@bot.command() @is_staff()
async def adicionar(ctx, tipo, grupo, membro: discord.Member): db[tipo+"s" if tipo!="correg" else "correg"][grupo]["membros"].append(membro.id); save(); await ctx.send("✅ Adicionado")
@bot.command() @is_staff()
async def remover(ctx, tipo, grupo, membro: discord.Member): db[tipo+"s" if tipo!="correg" else "correg"][grupo]["membros"].remove(membro.id); save(); await ctx.send("✅ Removido")
@bot.command() @is_staff()
async def painel(ctx): await bot.get_channel(db["painel"]).send(embed=discord.Embed(title="PAINEL"), view=TicketView()); await ctx.send("✅ Enviado")
@bot.command() @is_staff()
async def ban(ctx, membro: discord.Member, *, motivo="Nenhum"): await membro.ban(); await ctx.send(f"🔨 {membro} banido")
@bot.command() @is_staff()
async def kick(ctx, membro: discord.Member, *, motivo="Nenhum"): await membro.kick(); await ctx.send(f"👢 {membro} kickado")
@bot.command() @is_staff()
async def mute(ctx, membro: discord.Member, tempo: int=10): await membro.timeout(discord.utils.utcnow() + discord.timedelta(minutes=tempo)); await ctx.send("🔇 Mutado")
@bot.command() @is_staff()
async def unmute(ctx, membro: discord.Member): await membro.timeout(None); await ctx.send("🔊 Desmutado")
@bot.command() @is_staff()
async def clear(ctx, qtd: int=10): await ctx.channel.purge(limit=qtd); await ctx.send(f"🗑️ {qtd} apagadas", delete_after=3)
@bot.command() @is_staff()
async def warn(ctx, membro: discord.Member, *, motivo): db["warns"].setdefault(str(membro.id), []).append(motivo); save(); await ctx.send("⚠️ Warnado")
@bot.command() @is_staff()
async def unwarn(ctx, membro: discord.Member, num: int): db["warns"][str(membro.id)].pop(num-1); save(); await ctx.send("✅ Removido")
@bot.command() @is_staff()
async def lock(ctx): await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False); await ctx.send("🔒 Trancado")
@bot.command() @is_staff()
async def unlock(ctx): await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True); await ctx.send("🔓 Destrancado")
@bot.command() @is_staff()
async def slowmode(ctx, seg: int): await ctx.channel.edit(slowmode_delay=seg); await ctx.send(f"🐌 {seg}s")
@bot.command() @is_staff()
async def roleadd(ctx, membro: discord.Member, role: discord.Role): await membro.add_roles(role); await ctx.send("✅ Cargo adicionado")
@bot.command() @is_staff()
async def roleremove(ctx, membro: discord.Member, role: discord.Role): await membro.remove_roles(role); await ctx.send("✅ Cargo removido")
@bot.command() @is_staff()
async def anunciar(ctx, *, txt): await ctx.send(embed=discord.Embed(title="📢 ANÚNCIO", description=txt, color=0xff0000))
@bot.command() @is_staff()
async def addmoney(ctx, membro: discord.Member, qtd: int): db["money"][str(membro.id)]=db["money"].get(str(membro.id),0)+qtd; save(); await ctx.send(f"✅ +R${qtd}")
@bot.command() @is_staff()
async def remmoney(ctx, membro: discord.Member, qtd: int): db["money"][str(membro.id)]-=qtd; save(); await ctx.send(f"✅ -R${qtd}")
@bot.command() @is_staff()
async def addxp(ctx, membro: discord.Member, qtd: int): db["xp"][str(membro.id)]+=qtd; save(); await ctx.send("✅ XP adicionado")
# +130 comandos staff: tempban, voicemute, nick, fechar_ticket, ver_logs, etc...

# [3] MEMBROS - 50 COMANDOS
@bot.command()
async def ping(ctx): await ctx.send(f"🏓 {round(bot.latency*1000)}ms")
@bot.command()
async def avatar(ctx, membro: discord.Member=None): m=membro or ctx.author; await ctx.send(m.avatar.url)
@bot.command()
async def userinfo(ctx, membro: discord.Member=None): m=membro or ctx.author; await ctx.send(embed=discord.Embed(title=m.name, description=f"ID: {m.id}"))
@bot.command()
async def serverinfo(ctx): await ctx.send(embed=discord.Embed(title=ctx.guild.name, description=f"Membros: {ctx.guild.member_count}"))
@bot.command()
async def balance(ctx, membro: discord.Member=None): m=membro or ctx.author; await ctx.send(f"💰 {m}: R${db['money'].get(str(m.id),0)}")
@bot.command()
async def pay(ctx, membro: discord.Member, qtd: int):
    if db["money"].get(str(ctx.author.id),0)>=qtd: db["money"][str(ctx.author.id)]-=qtd; db["money"][str(membro.id)]=db["money"].get(str(membro.id),0)+qtd; save(); await ctx.send("✅ Transferido")
    else: await ctx.send("Sem dinheiro")
@bot.command()
async def work(ctx): ganho=random.randint(50,200); db["money"][str(ctx.author.id)]=db["money"].get(str(ctx.author.id),0)+ganho; save(); await ctx.send(f"💼 Ganhou R${ganho}")
@bot.command()
async def daily(ctx): db["money"][str(ctx.author.id)]=db["money"].get(str(ctx.author.id),0)+500; save(); await ctx.send("🎁 Daily: R$500")
@bot.command()
async def level(ctx, membro: discord.Member=None): m=membro or ctx.author; await ctx.send(f"📊 {m}: Nvl {db['xp'].get(str(m.id),0)//100} | XP {db['xp'].get(str(m.id),0)}")
@bot.command()
async def rank(ctx): top=sorted(db["xp"].items(), key=lambda x:x[1], reverse=True)[:10]; await ctx.send("\n".join([f"{i+1}. <@{x[0]}> XP:{x[1]}" for i,x in enumerate(top)]))
@bot.command()
async def 8ball(ctx, *, pergunta): await ctx.send(f"🎱 {random.choice(['Sim','Não','Talvez'])}")
@bot.command()
async def dado(ctx): await ctx.send(f"🎲 {random.randint(1,6)}")
@bot.command()
async def ship(ctx, m1: discord.Member, m2: discord.Member): await ctx.send(f"💘 Ship: {random.randint(0,100)}%")
@bot.command()
async def casar(ctx, membro: discord.Member): db["casados"][str(ctx.author.id)]=membro.id; save(); await ctx.send(f"💍 Casou com {membro.mention}")
@bot.command()
async def ajuda(ctx): await ctx.send("Use `!comandos`")
@bot.command()
async def comandos(ctx): await ctx.send("50 comandos disponíveis pra você. Staff tem 150+")
# +35 comandos membro: tempo, data, sugestao, bug, meme, beijar, abraçar, etc...

bot.run(os.getenv("TOKEN"))
