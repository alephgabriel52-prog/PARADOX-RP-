import discord,os,json,datetime,asyncio
from discord.ext import commands,tasks
from flask import Flask
from threading import Thread

print("INICIANDO V102...")
app=Flask('')
@app.route('/')
def h():return"V102 PARADOXO RP"
Thread(target=lambda:app.run(host='0.0.0.0',port=8080)).start()

intents=discord.Intents.all()
intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

try:db=json.load(open('db.json'))
except:db={"cfg":{"tc":0,"sc":0,"wc":0,"tr":0},"an":[],"raid":{"on":False,"lim":5},"wl":{},"warns":{}}
def sv():json.dump(db,open('db.json','w'))

BANNER="https://cdn.discordapp.com/attachments/1527669780364918925/1549093554960474243/file_0005a0820e8df98c1974ab6ecc.png"

def is_staff():
 async def p(ctx):return ctx.author.guild_permissions.administrator or ctx.author.id==1438010935783460954
 return commands.check(p)

@tasks.loop(minutes=1)
async def va():
 a=datetime.datetime.now().strftime("%H:%M")
 for x in db["an"][:]:
  if x["h"]==a:
   c=bot.get_channel(x["c"])
   if c:await c.send("@everyone",embed=discord.Embed(title="📢 ANÚNCIO PARADOXO RP",description=x["m"],color=0xFF0000).set_image(url=BANNER))
   db["an"].remove(x);sv()

# WHITELIST SEM BOTÃO - 100% FUNCIONAL
@bot.command()
async def whitelist(ctx):
 embed=discord.Embed(title="📝 WHITELIST PARADOXO RP",description="✅ APROVADO = não faz mais\n🔄 REPROVADO = pode tentar de novo\n\n**Para começar digite:** `!fazerwl`\nEu vou te chamar no PV com as perguntas",color=0xFF0000).set_image(url=BANNER)
 await ctx.send(embed=embed)

@bot.command()
async def fazerwl(ctx):
 uid=str(ctx.author.id)
 if uid in db["wl"] and db["wl"][uid]["status"]=="aprovado":
  return await ctx.send("❌ Você já foi **APROVADO**")
 try:
  await ctx.author.send("**WHITELIST PARADOXO RP**\n1. Qual seu nome e idade?")
  r1=await bot.wait_for('message',check=lambda m:m.author==ctx.author and isinstance(m.channel,discord.DMChannel),timeout=300)
  await ctx.author.send("2. Já jogou RP antes? Qual cidade?")
  r2=await bot.wait_for('message',check=lambda m:m.author==ctx.author and isinstance(m.channel,discord.DMChannel),timeout=300)
  await ctx.author.send("3. Por que quer entrar no Paradoxo RP?")
  r3=await bot.wait_for('message',check=lambda m:m.author==ctx.author and isinstance(m.channel,discord.DMChannel),timeout=300)
  
  db["wl"][uid]={"r1":r1.content,"r2":r2.content,"r3":r3.content,"status":"pendente"};sv()
  ch=bot.get_channel(db["cfg"]["wc"])
  if ch:
   e=discord.Embed(title=f"📝 NOVA WHITELIST - {ctx.author.name}",color=0xFF0000)
   e.add_field(name="1. Nome/Idade",value=r1.content,inline=False)
   e.add_field(name="2. Exp RP",value=r2.content,inline=False)
   e.add_field(name="3. Motivo",value=r3.content,inline=False)
   e.set_footer(text=f"ID: {uid}")
   await ch.send(f"<@&{db['cfg']['sc']}>",embed=e)
  await ctx.author.send("✅ Enviado! Aguarde a STAFF analisar.")
 except:await ctx.author.send("❌ Tempo esgotou. Use!fazerwl de novo")

@bot.command()
@is_staff()
async def aprovar(ctx,member:discord.Member):
 db["wl"][str(member.id)]["status"]="aprovado";sv()
 await member.send("✅ **APROVADO** na whitelist do Paradoxo RP!")
 await ctx.send(f"✅ {member.mention} **APROVADO**")

@bot.command()
@is_staff()
async def reprovar(ctx,member:discord.Member,*,motivo="Sem motivo"):
 db["wl"][str(member.id)]["status"]="reprovado";sv()
 await member.send(f"❌ **REPROVADO**\nMotivo: {motivo}\nPode tentar novamente!")
 await ctx.send(f"❌ {member.mention} **REPROVADO**")

@bot.command()
@is_staff()
async def setwlchannel(ctx,ch:discord.TextChannel):
 db["cfg"]["wc"]=ch.id;sv();await ctx.send(f"✅ Canal de whitelist: {ch.mention}")

@bot.command()
@is_staff()
async def setstaffcargo(ctx,role:discord.Role):
 db["cfg"]["sc"]=role.id;sv();await ctx.send(f"✅ Cargo STAFF: {role.name}")

@bot.event
async def on_ready():
 va.start()
 print("✅ V102 ONLINE - PARADOXO RP")

bot.run(os.getenv("TOKEN"))
