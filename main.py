import discord,os,json,datetime,asyncio
from discord.ext import commands,tasks
from flask import Flask
from threading import Thread

print("INICIANDO V98...")
app=Flask('')
@app.route('/')
def h():return"V98 PARADOXO RP"
Thread(target=lambda:app.run(host='0.0.0.0',port=8080)).start()

intents=discord.Intents.all()
intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

# BANCO DE DADOS
try:db=json.load(open('db.json'))
except:db={"cfg":{"tc":0,"sc":0,"wc":0,"tr":0},"an":[],"raid":{"on":False,"lim":5},"wl":{}}
def sv():json.dump(db,open('db.json','w'))

# FAIXA DO PARADOXO
BANNER="https://cdn.discordapp.com/attachments/1527669780364918925/1549093554960474243/file_0005a0820e8df98c1974ab6ecc.png"

# VERIFICAR STAFF
def is_staff():
 async def p(ctx):return ctx.author.guild_permissions.administrator or ctx.author.id==1438010935783460954
 return commands.check(p)

# LOOP DE ANÚNCIOS
@tasks.loop(minutes=1)
async def va():
 a=datetime.datetime.now().strftime("%H:%M")
 for x in db["an"][:]:
  if x["h"]==a:
   c=bot.get_channel(x["c"])
   if c:
    embed=discord.Embed(title="📢 ANÚNCIO PARADOXO RP",description=x["m"],color=0xFF0000)
    embed.set_image(url=BANNER)
    embed.set_footer(text="Paradoxo RP - A Cidade Que Nunca Dorme")
    await c.send("@everyone",embed=embed)
   db["an"].remove(x);sv()

# ANTI RAID
user_join={}
@bot.event
async def on_member_join(m):
 if not db["raid"]["on"]:return
 gid=str(m.guild.id)
 user_join[gid]=user_join.get(gid,[])+[datetime.datetime.now()]
 user_join[gid]=[t for t in user_join[gid] if (datetime.datetime.now()-t).seconds<10]
 if len(user_join[gid])>db["raid"]["lim"]:
  for ch in m.guild.text_channels:
   if ch.permissions_for(m.guild.me).send_messages:
    await ch.send("🚨 **ANTI-RAID ATIVADO** 🚨\nServidor em modo proteção. Entradas bloqueadas.")
  await m.guild.edit(verification_level=discord.VerificationLevel.highest)

# COMANDOS PRINCIPAIS
@bot.command()
@is_staff()
async def anuncio(ctx):
 await ctx.send("📢 **1/3** Manda o ID do CANAL do anúncio")
 m=await bot.wait_for('message',check=lambda x:x.author==ctx.author,timeout=60)
 await ctx.send("📝 **2/3** Manda a MENSAGEM do anúncio")
 msg=await bot.wait_for('message',check=lambda x:x.author==ctx.author,timeout=120)
 await ctx.send("⏰ **3/3** Manda o HORÁRIO no formato HH:MM")
 hr=await bot.wait_for('message',check=lambda x:x.author==ctx.author,timeout=60)
 db["an"].append({"id":len(db["an"])+1,"c":int(m.content),"m":msg.content,"h":hr.content});sv()
 await ctx.send(f"✅ **Anúncio agendado!**\nID: `{len(db['an'])}`\nCanal: <#{m.content}>\nHorário: `{hr.content}`")

@bot.command()
@is_staff()
async def anuncios(ctx):
 if not db["an"]:return await ctx.send("📭 **Nenhum anúncio agendado**")
 e=discord.Embed(title="📢 Anuncios Agendados - PARADOXO RP",color=0xFF0000)
 for x in db["an"]:e.add_field(name=f"ID: {x['id']} | Horário: {x['h']}",value=f"Canal: <#{x['c']}>\nMsg: {x['m'][:50]}...",inline=False)
 e.set_thumbnail(url=BANNER)
 await ctx.send(embed=e)

@bot.command()
@is_staff()
async def ticket(ctx):
 embed=discord.Embed(title="🎫 ABRA SEU TICKET - PARADOXO RP",description="Precisa de ajuda? Abra um ticket e nossa equipe te atende!",color=0xFF0000)
 embed.set_image(url=BANNER)
 await ctx.send(embed=embed)

@bot.command()
async def whitelist(ctx):
 embed=discord.Embed(title="📝 WHITELIST PARADOXO RP",description="✅ APROVADO = não faz mais\n🔄 REPROVADO = pode tentar de novo\nClique no botão abaixo para iniciar!",color=0xFF0000)
 embed.set_image(url=BANNER)
 await ctx.send(embed=embed)

# COMANDOS STAFF
@bot.command()
@is_staff()
async def limpar(ctx,qtd:int=10):
 await ctx.channel.purge(limit=qtd+1)
 await ctx.send(f"🧹 `{qtd}` mensagens limpas",delete_after=3)

@bot.command()
@is_staff()
async def ban(ctx,member:discord.Member,*,motivo="Sem motivo"):
 await member.ban(reason=motivo)
 await ctx.send(f"🔨 {member.mention} foi **banido**\nMotivo: {motivo}")

@bot.command()
@is_staff()
async def kick(ctx,member:discord.Member,*,motivo="Sem motivo"):
 await member.kick(reason=motivo)
 await ctx.send(f"👢 {member.mention} foi **expulso**\nMotivo: {motivo}")

@bot.command()
@is_staff()
async def mute(ctx,member:discord.Member,tempo:int=10):
 role=discord.utils.get(ctx.guild.roles,name="Muteado")
 if not role:role=await ctx.guild.create_role(name="Muteado")
 await member.add_roles(role)
 await ctx.send(f"🔇 {member.mention} foi **mutado** por {tempo}min")
 await asyncio.sleep(tempo*60)
 await member.remove_roles(role)

# SISTEMA ANTI RAID
@bot.command()
@is_staff()
async def antiraid(ctx,acao:str):
 if acao=="on":db["raid"]["on"]=True;sv();await ctx.send("🚨 **Anti-Raid ATIVADO**\nLimite: 5 entradas em 10s")
 elif acao=="off":db["raid"]["on"]=False;sv();await ctx.send("✅ **Anti-Raid DESATIVADO**")
 elif acao=="lim":await ctx.send(f"Limite atual: `{db['raid']['lim']}` entradas em 10s")

@bot.command()
@is_staff()
async def setbanner(ctx,link):
 global BANNER;BANNER=link;await ctx.send("✅ Banner atualizado!")

@bot.event
async def on_ready():
 va.start()
 print("✅ V98 ONLINE - PARADOXO RP")
 print(f"Logado como: {bot.user}")

bot.run(os.getenv("TOKEN"))
