import discord,os,json,datetime
from discord.ext import commands,tasks
from flask import Flask
from threading import Thread
app=Flask('')
@app.route('/')
def h():return"V97"
Thread(target=lambda:app.run(host='0.0.0.0',port=8080)).start()
intents=discord.Intents.all();intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

try:db=json.load(open('db.json'))
except:db={"an":[]}
def sv():json.dump(db,open('db.json','w'))
B="https://cdn.discordapp.com/attachments/1527669780364918925/1549093554960474243/file_0005a0820e8df98c1974ab6ecc.png"

@tasks.loop(minutes=1)
async def va():
 a=datetime.datetime.now().strftime("%H:%M")
 for x in db["an"][:]:
  if x["h"]==a:
   c=bot.get_channel(x["c"])
   if c:await c.send("@everyone",embed=discord.Embed(title="📢 ANÚNCIO PARADOXO RP",description=x["m"],color=0xFF0000).set_image(url=B))
   db["an"].remove(x);sv()

@bot.command()
async def anuncio(ctx):await ctx.send("✅ V97 ANUNCIO FUNCIONOU")

@bot.command()
async def anuncios(ctx):await ctx.send("✅ V97 ANUNCIOS FUNCIONOU")

@bot.command()
async def ticket(ctx):await ctx.send(embed=discord.Embed(title="🎫 PARADOXO RP",color=0xFF0000).set_image(url=B))

@bot.command()
async def whitelist(ctx):await ctx.send(embed=discord.Embed(title="📝 WHITELIST PARADOXO RP",color=0xFF0000).set_image(url=B))

@bot.event
async def on_ready():va.start();print("✅ V97 ONLINE - PARADOXO RP")

bot.run(os.getenv("TOKEN"))
