import discord,os,json,datetime,asyncio
from discord.ext import commands,tasks
from flask import Flask
from threading import Thread

print("INICIANDO V108...")
app=Flask('')
@app.route('/')
def h():return"V108 PARADOXO RP"
Thread(target=lambda:app.run(host='0.0.0.0',port=8080)).start()

intents=discord.Intents.all()
intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

BANNER="https://cdn.discordapp.com/attachments/1527669780364918925/1549093554960474243/file_0005a0820e8df98c1974ab6ecc.png"
DONO=1438010935783460954

try:db=json.load(open('db.json'))
except:db={"cfg":{"tc":0,"sc":0,"wc":0,"tr":DONO,"banner":BANNER,"prefix":"!"},"an":[],"raid":{"on":False,"lim":5},"wl":{},"warns":{},"cmds":{}}
def sv():
 with open('db.json','w') as f:json.dump(db,f)

def is_staff():
 async def p(ctx):return ctx.author.guild_permissions.administrator or ctx.author.id==DONO or str(ctx.author.id)==db["cfg"]["sc"]
 return commands.check(p)

class ConfigPanel(discord.ui.View):
 def __init__(self):super().__init__(timeout=300)
 @discord.ui.select(placeholder="⚙️ SELECIONE O QUE QUER CONFIGURAR",options=[
  discord.SelectOption(label="Canal de Whitelist",emoji="📝",value="wc"),
  discord.SelectOption(label="Cargo da Staff",emoji="👮",value="sc"),
  discord.SelectOption(label="Anti-Raid ON/OFF",emoji="🚨",value="raid"),
  discord.SelectOption(label="Limite Anti-Raid",emoji="🔢",value="lim"),
  discord.SelectOption(label="Trocar Banner",emoji="🖼️",value="banner"),
  discord.SelectOption(label="Prefixo do Bot",emoji="#️⃣",value="prefix"),
  discord.SelectOption(label="Criar Comando Custom",emoji="➕",value="addcmd"),
  discord.SelectOption(label="Deletar Comando",emoji="➖",value="delcmd"),
  discord.SelectOption(label="Listar Comandos",emoji="📋",value="listcmd"),
 ],custom_id="config_select")
 async def select(self,interaction:discord.Interaction,select:discord.ui.Select):
  if interaction.user.id!=DONO and str(interaction.user.id)!=db["cfg"]["sc"]:return await interaction.response.send_message("❌ Sem permissão",ephemeral=True)
  op=select.values[0]
  if op=="wc":await interaction.response.send_message("📝 Manda o ID do canal de whitelist",ephemeral=True)
  elif op=="sc":await interaction.response.send_message("👮 Manda o ID do cargo de staff",ephemeral=True)
  elif op=="raid":db["raid"]["on"]=not db["raid"]["on"];sv();await interaction.response.send_message(f"🚨 Anti-Raid: {'ON' if db['raid']['on'] else 'OFF'}",ephemeral=True)
  elif op=="lim":await interaction.response.send_message("🔢 Manda o novo limite. Ex: 3",ephemeral=True)
  elif op=="banner":await interaction.response.send_message("🖼️ Manda o LINK da nova banner",ephemeral=True)
  elif op=="prefix":await interaction.response.send_message("#️⃣ Manda o novo prefixo. Ex:.",ephemeral=True)
  elif op=="addcmd":await interaction.response.send_message("➕ Manda: `nome | resposta`\nEx: `regras | Leia #regras`",ephemeral=True)
  elif op=="delcmd":await interaction.response.send_message("➖ Manda o nome do comando pra deletar",ephemeral=True)
  elif op=="listcmd":lista=", ".join(db['cmds'].keys()) if db['cmds'] else "Nenhum";await interaction.response.send_message(f"📋 Comandos: {lista}",ephemeral=True)

@bot.event
async def on_message(message):
 if message.author.bot:return
 if message.content.startswith(db["cfg"]["prefix"]):
  cmd=message.content[len(db["cfg"]["prefix"]):].split()[0]
  if cmd in db["cmds"]:
   await message.channel.send(db["cmds"][cmd])
 await bot.process_commands(message)

class StaffPanel(discord.ui.View):
 def __init__(self,uid):super().__init__(timeout=None);self.uid=uid
 @discord.ui.button(label="APROVAR",style=discord.ButtonStyle.green,emoji="✅",custom_id="wl_aprovar")
 async def aprovar(self,interaction:discord.Interaction,button:discord.ui.Button):
  if not (interaction.user.guild_permissions.administrator or interaction.user.id==DONO or str(interaction.user.id)==db["cfg"]["sc"]):
   return await interaction.response.send_message("❌ Sem permissão",ephemeral=True)
  db["wl"][self.uid]["status"]="aprovado";sv()
  user=await bot.fetch_user(int(self.uid))
  await user.send("✅ **APROVADO** na whitelist do Paradoxo RP!")
  await interaction.response.edit_message(content="✅ **APROVADO PELA STAFF**",embed=None,view=None)
 @discord.ui.button(label="REPROVAR",style=discord.ButtonStyle.red,emoji="❌",custom_id="wl_reprovar")
 async def reprovar(self,interaction:discord.Interaction,button:discord.ui.Button):
  if not (interaction.user.guild_permissions.administrator or interaction.user.id==DONO or str(interaction.user.id)==db["cfg"]["sc"]):
   return await interaction.response.send_message("❌ Sem permissão",ephemeral=True)
  db["wl"][self.uid]["status"]="reprovado";sv()
  user=await bot.fetch_user(int(self.uid))
  await user.send("❌ **REPROVADO** na whitelist. Pode tentar novamente!")
  await interaction.response.edit_message(content="❌ **REPROVADO PELA STAFF**",embed=None,view=None)

class WLButton(discord.ui.View):
 def __init__(self):super().__init__(timeout=None)
 @discord.ui.button(label="INICIAR WHITELIST",style=discord.ButtonStyle.green,emoji="📝",custom_id="wl_start_btn")
 async def btn(self,interaction:discord.Interaction,button:discord.ui.Button):
  uid=str(interaction.user.id)
  if uid in db["wl"] and db["wl"][uid]["status"]=="aprovado":
   return await interaction.response.send_message("❌ Você já foi **APROVADO**",ephemeral=True)
  await interaction.response.send_message("📩 Te mandei as perguntas no PV!",ephemeral=True)
  try:
   await interaction.user.send("**WHITELIST PARADOXO RP**\n1. Qual seu nome e idade?")
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
    await ch.send(f"<@&{db['cfg']['sc']}>",embed=e,view=StaffPanel(uid))
   await interaction.user.send("✅ Enviado! Aguarde a STAFF analisar.")
  except:await interaction.user.send("❌ Tempo esgotou. Use!whitelist de novo")

@tasks.loop(minutes=1)
async def va():
 a=datetime.datetime.now().strftime("%H:%M")
 for x in db["an"][:]:
  if x["h"]==a:
   c=bot.get_channel(x["c"])
   if c:await c.send("@everyone",embed=discord.Embed(title="📢 ANÚNCIO PARADOXO RP",description=x["m"],color=0xFF0000).set_image(url=db["cfg"]["banner"]))
   db["an"].remove(x);sv()

@bot.command()
async def whitelist(ctx):
 embed=discord.Embed(title="📝 WHITELIST PARADOXO RP",description="✅ APROVADO = não faz mais\n🔄 REPROVADO = pode tentar de novo\nClique no botão abaixo para iniciar!",color=0xFF0000).set_image(url=db["cfg"]["banner"])
 await ctx.send(embed=embed,view=WLButton())

@bot.command()
async def botconfig(ctx):
 if ctx.author.id!=DONO and str(ctx.author.id)!=db["cfg"]["sc"]:return await ctx.send("❌ Só DONO/STAFF")
 e=discord.Embed(title="⚙️ CENTRAL DE CONTROLE PARADOXO",color=0xFF0000)
 e.add_field(name="📝 Canal WL",value=f"<#{db['cfg']['wc']}>" if db['cfg']['wc'] else "Não setado",inline=True)
 e.add_field(name="👮 Cargo STAFF",value=f"<@&{db['cfg']['sc']}>" if db['cfg']['sc'] else "Não setado",inline=True)
 e.add_field(name="🚨 Anti-Raid",value="ON" if db['raid']['on'] else "OFF",inline=True)
 e.add_field(name="#️⃣ Prefixo",value=f"`{db['cfg']['prefix']}`",inline=True)
 e.add_field(name="📋 Comandos Custom",value=f"{len(db['cmds'])} criados",inline=True)
 await ctx.send(embed=e,view=ConfigPanel())

@bot.command()
@is_staff()
async def addcmd(ctx,*,args):
 try:
  nome,resposta=args.split("|",1)
  db["cmds"][nome.strip()]=resposta.strip();sv()
  await ctx.send(f"✅ Comando `!{nome.strip()}` criado!")
 except:await ctx.send("❌ Use: `!addcmd nome | resposta`")

@bot.command()
@is_staff()
async def delcmd(ctx,nome):
 if nome in db["cmds"]:del db["cmds"][nome];sv();await ctx.send(f"✅ Comando `!{nome}` deletado")
 else:await ctx.send("❌ Comando não existe")

@bot.event
async def setup_hook():
 bot.add_view(WLButton())
 bot.add_view(StaffPanel("0"))

@bot.event
async def on_ready():
 va.start()
 print("✅ V108 ONLINE - PARADOXO RP")

bot.run(os.getenv("TOKEN"))
