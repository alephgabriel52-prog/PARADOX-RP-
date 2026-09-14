import discord,os,json,datetime,asyncio
from discord.ext import commands,tasks
from flask import Flask
from threading import Thread

print("INICIANDO V117...")
app=Flask('')
@app.route('/')
def h():return"V117 NOSSO RP"
Thread(target=lambda:app.run(host='0.0.0.0',port=8080)).start()

intents=discord.Intents.all()
intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

BANNER="https://cdn.discordapp.com/attachments/1527669780364918925/1549093554960474243/file_0005a0820e8df98c1974ab6ecc.png"
DONO=1438010935783460954

try:db=json.load(open('db.json'))
except:db={"cfg":{"tc":0,"sc":0,"wc":0,"tr":DONO,"banner":BANNER,"prefix":"!"},"an":[],"raid":{"on":False,"lim":5},"wl":{},"warns":{},"cmds":{},"tickets":{},"awaiting":{}}
def sv():
 with open('db.json','w') as f:json.dump(db,f)

def is_staff():
 async def p(ctx):return ctx.author.guild_permissions.administrator or ctx.author.id==DONO or str(ctx.author.id)==db["cfg"]["sc"]
 return commands.check(p)

PERGUNTAS=[...mesmas 15 perguntas...]

class ConfigPanel(discord.ui.View):
 def __init__(self):super().__init__(timeout=None)
 @discord.ui.select(placeholder="⚙️ SELECIONE O QUE QUER CONFIGURAR",custom_id="config_select_v117",options=[
  discord.SelectOption(label="Canal de Whitelist",emoji="📝",value="wc"),
  discord.SelectOption(label="Cargo da Staff",emoji="👮",value="sc"),
  discord.SelectOption(label="Categoria de Tickets",emoji="📂",value="tc"),
  discord.SelectOption(label="Anti-Raid ON/OFF",emoji="🚨",value="raid"),
  discord.SelectOption(label="Limite Anti-Raid",emoji="🔢",value="lim"),
  discord.SelectOption(label="Trocar Banner",emoji="🖼️",value="banner"),
  discord.SelectOption(label="Prefixo do Bot",emoji="#️⃣",value="prefix"),
  discord.SelectOption(label="Criar Comando Custom",emoji="➕",value="addcmd"),
  discord.SelectOption(label="Deletar Comando",emoji="➖",value="delcmd"),
  discord.SelectOption(label="Listar Comandos",emoji="📋",value="listcmd"),
 ])
 async def select(self,i,s):
  if i.user.id!=DONO and str(i.user.id)!=db["cfg"]["sc"]:return await i.response.send_message("❌ Sem permissão",ephemeral=True)
  op=s.values[0]
  uid=str(i.user.id)
  db["awaiting"][uid]=op;sv()

  msgs={"wc":"📝 Manda o ID do canal de whitelist AQUI NO CHAT","sc":"👮 Manda o ID do cargo de staff AQUI NO CHAT","tc":"📂 Manda o ID da CATEGORIA de tickets AQUI NO CHAT","lim":"🔢 Manda o novo limite. Ex: 3","banner":"🖼️ Manda o link da banner","prefix":"#️⃣ Manda o novo prefixo. Ex:.","addcmd":"➕ Use: nome | resposta","delcmd":"➖ Manda o nome do comando","listcmd":f"📋 {', '.join(db['cmds'].keys()) if db['cmds'] else 'Nenhum'}"}
  if op=="raid":db["raid"]["on"]=not db["raid"]["on"];db["awaiting"].pop(uid,None);sv();await i.response.send_message(f"🚨 Anti-Raid: {'ON' if db['raid']['on'] else 'OFF'}",ephemeral=True)
  else:await i.response.send_message(msgs[op],ephemeral=True)

... resto das classes StaffTicket e WLStartButton igual V116...

@bot.event
async def on_message(m):
 if m.author.bot:return
 uid=str(m.author.id)

 # SISTEMA DE CONFIG PELO CHAT
 if uid in db["awaiting"]:
  tipo=db["awaiting"][uid]
  try:
   if tipo in ["wc","sc","tc"]:db["cfg"][tipo]=int(m.content)
   elif tipo=="lim":db["cfg"]["lim"]=int(m.content)
   elif tipo=="banner":db["cfg"]["banner"]=m.content
   elif tipo=="prefix":db["cfg"]["prefix"]=m.content
   elif tipo=="addcmd":
    nome,resposta=m.content.split("|",1)
    db["cmds"][nome.strip()]=resposta.strip()
   elif tipo=="delcmd":db["cmds"].pop(m.content,None)
   sv();db["awaiting"].pop(uid,None)
   await m.reply(f"✅ {tipo.upper()} configurado com sucesso!")
   return
  except:await m.reply("❌ Valor inválido. Tenta de novo.")

 # Resto do sistema de WL igual V116
 if uid in db["tickets"] and m.channel.id==db["tickets"][uid]:
 ... código das 15 perguntas...

 if m.content.startswith(db["cfg"]["prefix"]):
  cmd=m.content[len(db["cfg"]["prefix"]):].split()[0]
  if cmd in db["cmds"]:await m.channel.send(db["cmds"][cmd])
 await bot.process_commands(m)

... todos os comandos iguais V116...

@bot.event
async def setup_hook():
 bot.add_view(WLStartButton())
 bot.add_view(StaffTicket("0",0))
 bot.add_view(ConfigPanel())

@bot.event
async def on_ready():
 va.start()
 print("✅ V117 ONLINE - CONFIG PELO CHAT ATIVO")

bot.run(os.getenv("TOKEN"))
