import discord,os,json,datetime,asyncio
from discord.ext import commands,tasks
from flask import Flask
from threading import Thread

print("INICIANDO V97...")
app=Flask('')
@app.route('/')
def h():return"V97 PARADOXO RP"
Thread(target=lambda:app.run(host='0.0.0.0',port=8080)).start()

intents=discord.Intents.all()
intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

# BANCO DE DADOS
try:db=json.load(open('db.json'))
except:db={"cfg":{"tc":0,"sc":0,"wc":0,"tr":0},"an":[]}
def sv():json.dump(db,open('db.json','w'))

# FAIXA DO PARADOXO
BANNER="https://cdn.discordapp.com/attachments/1527669780364918925/1549093554960474243/file_0005a0820e8df98c1974ab6ecc.png"

# VERIFICAR ADMIN
def is_admin():
 async def p(ctx):return ctx.author.guild_permissions.administrator or ctx.author.id==1438010935783460954
 return commands.check(p)

# LOOP DE ANÚNCIOS AUTOMÁTICO
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

@va.before_loop
async def b():await bot.wait_until_ready()

# COMANDOS
@bot.command()
@is_admin()
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
@is_admin()
async def anuncios(ctx):
 if not db["an"]:return await ctx.send("📭 **Nenhum anúncio agendado**")
 e=discord.Embed(title="📢 Anuncios Agendados - PARADOXO RP",color=0xFF0000)
 for x in db["an"]:e.add_field(name=f"ID: {x['id']} | Horário: {x['h']}",value=f"Canal: <#{x['c']}>\nMsg: {x['m'][:50]}...",inline=False)
 e.set_thumbnail(url=BANNER)
 await ctx.send(embed=e)

@bot.command()
@is_admin()
async def ticket(ctx):
 embed=discord.Embed(title="🎫 ABRA SEU TICKET - PARADOXO RP",description="Precisa de ajuda? Abra um ticket e nossa equipe te atende!",color=0xFF0000)
 embed.set_image(url=BANNER)
 await ctx.send(embed=embed)

@bot.command()
@is_admin()
async def whitelist(ctx):
 embed=discord.Embed(title="📝 WHITELIST PARADOXO RP",description="Quer entrar na cidade? Preencha a whitelist!",color=0xFF0000)
 embed.set_image(url=BANNER)
 await ctx.send(embed=embed)

@bot.event
async def on_ready():
 va.start()
 print("✅ V97 ONLINE - PARADOXO RP")
 print(f"Logado como: {bot.user}")

bot.run(os.getenv("TOKEN"))
