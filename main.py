import discord,os,json,datetime,asyncio
from discord.ext import commands,tasks
from flask import Flask
from threading import Thread

print("INICIANDO V100...")
app=Flask('')
@app.route('/')
def h():return"V100 PARADOXO RP"
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

# BOTÃO DA WHITELIST
class WLButton(discord.ui.View):
 def __init__(self):super().__init__(timeout=None)
 @discord.ui.button(label="INICIAR WHITELIST",style=discord.ButtonStyle.green,emoji="📝")
 async def btn(self,interaction:discord.Interaction,button:discord.ui.Button):
  uid=str(interaction.user.id)
  if uid in db["wl"] and db["wl"][uid]["status"]=="aprovado":
   return await interaction.response.send_message("❌ Você já foi **APROVADO** e não precisa fazer mais",ephemeral=True)
  await interaction.response.send_message("📩 Te mandei as perguntas no PV!",ephemeral=True)
  try:
   await interaction.user.send("**WHITELIST PARADOXO RP**\nResponda as perguntas:\n\n1. Qual seu nome e idade?")
   r1=await bot.wait_for('message',check=lambda m:m.author==interaction.user and isinstance(m.channel,discord.DMChannel),timeout=300)
   await interaction.user.send("2. Já jogou RP antes? Qual cidade?")
   r2=await bot.wait_for('message',check=lambda m:m.author==interaction.user and isinstance(m.channel,discord.DMChannel),timeout=300)
   await interaction.user.send("3. Por que quer entrar no Paradoxo RP?")
   r3=await bot.wait_for('message',check=lambda m:m.author==interaction.user and isinstance(m.channel,discord.DMChannel),timeout=300)
   
   db["wl"][uid]={"r1":r1.content,"r2":r2.content,"r3":r3.content,"status":"pendente"};sv()
   ch=bot.get_channel(db["cfg"]["wc"])
   if ch:
    e=discord.Embed(title=f"📝 NOVA WHITELIST - {interaction.user.name}",color=0xFF0000)
    e.add_field(name="1. Nome/Idade",value=r1.content,inline=False)
    e.add_field(name="2. Exp RP",value=r2.content,inline=False)
    e.add_field(name="3. Motivo",value=r3.content,inline=False)
    e.set_footer(text=f"ID: {uid}")
    await ch.send(f"<@&{db['cfg']['sc']}>",embed=e)
   await interaction.user.send("✅ Enviado! Aguarde a STAFF analisar.")
  except:await interaction.user.send("❌ Tempo esgotou. Use!whitelist de novo")

@tasks.loop(minutes=1)
async def va():
 a=datetime.datetime.now().strftime("%H:%M")
 for x in db["an"][:]:
  if x["h"]==a:
   c=bot.get_channel(x["c"])
   if c:await c.send("@everyone",embed=discord.Embed(title="📢 ANÚNCIO PARADOXO RP",description=x["m"],color=0xFF0000).set_image(url=BANNER))
   db["an"].remove(x);sv()

# COMANDOS
@bot.command()
@is_staff()
async def anuncio(ctx): #... mesmo do anterior
 await ctx.send("📢 **1/3** Manda o ID do CANAL")
 m=await bot.wait_for('message',check=lambda x:x.author==ctx.author,timeout=60)
 await ctx.send("📝 **2/3** Manda a MENSAGEM")
 msg=await bot.wait_for('message',check=lambda x:x.author==ctx.author,timeout=120)
 await ctx.send("⏰ **3/3** Manda o HORÁRIO HH:MM")
 hr=await bot.wait_for('message',check=lambda x:x.author==ctx.author,timeout=60)
 db["an"].append({"id":len(db["an"])+1,"c":int(m.content),"m":msg.content,"h":hr.content});sv()
 await ctx.send(f"✅ **Agendado!** ID: `{len(db['an'])}`")

@bot.command()
@is_staff()
async def setwlchannel(ctx,ch:discord.TextChannel):
 db["cfg"]["wc"]=ch.id;sv();await ctx.send(f"✅ Canal de whitelist definido: {ch.mention}")

@bot.command()
@is_staff()
async def setstaffcargo(ctx,role:discord.Role):
 db["cfg"]["sc"]=role.id;sv();await ctx.send(f"✅ Cargo da STAFF definido: {role.name}")

@bot.command()
async def whitelist(ctx):
 embed=discord.Embed(title="📝 WHITELIST PARADOXO RP",description="✅ APROVADO = não faz mais\n🔄 REPROVADO = pode tentar de novo\nClique no botão abaixo para iniciar!",color=0xFF0000).set_image(url=BANNER)
 await ctx.send(embed=embed,view=WLButton())

@bot.command()
@is_staff()
async def aprovar(ctx,member:discord.Member):
 db["wl"][str(member.id)]["status"]="aprovado";sv()
 await member.send("✅ **PARABÉNS!** Você foi APROVADO na whitelist do Paradoxo RP!")
 await ctx.send(f"✅ {member.mention} **APROVADO**")

@bot.command()
@is_staff()
async def reprovar(ctx,member:discord.Member,*,motivo="Sem motivo"):
 db["wl"][str(member.id)]["status"]="reprovado";sv()
 await member.send(f"❌ Você foi REPROVADO na whitelist.\nMotivo: {motivo}\nPode tentar novamente!")
 await ctx.send(f"❌ {member.mention} **REPROVADO**")

#... todos os outros comandos: limpar, ban, kick, mute, warn, antiraid

@bot.event
async def on_ready():
 va.start()
 bot.add_view(WLButton())
 print("✅ V100 ONLINE - PARADOXO RP")

bot.run(os.getenv("TOKEN"))
