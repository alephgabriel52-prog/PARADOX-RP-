import discord,os,json,datetime,asyncio
from discord.ext import commands,tasks
from flask import Flask
from threading import Thread

print("INICIANDO V116...")
app=Flask('')
@app.route('/')
def h():return"V116 NOSSO RP"
Thread(target=lambda:app.run(host='0.0.0.0',port=8080)).start()

intents=discord.Intents.all()
intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

BANNER="https://cdn.discordapp.com/attachments/1527669780364918925/1549093554960474243/file_0005a0820e8df98c1974ab6ecc.png"
DONO=1438010935783460954

try:db=json.load(open('db.json'))
except:db={"cfg":{"tc":0,"sc":0,"wc":0,"tr":DONO,"banner":BANNER,"prefix":"!"},"an":[],"raid":{"on":False,"lim":5},"wl":{},"warns":{},"cmds":{},"tickets":{}}
def sv():
 with open('db.json','w') as f:json.dump(db,f)

def is_staff():
 async def p(ctx):return ctx.author.guild_permissions.administrator or ctx.author.id==DONO or str(ctx.author.id)==db["cfg"]["sc"]
 return commands.check(p)

PERGUNTAS=[
 "1. Qual seu nome completo e idade?","2. Você tem microfone? Sabe usar?","3. Já jogou RP antes? Qual cidade?",
 "4. Qual seu nível de interpretação RP de 0 a 10?","5. O que é RDM?","6. O que é VDM?","7. O que é Meta Gaming?",
 "8. O que é Power Gaming?","9. O que é Fail RP?","10. Por que quer entrar no Nosso RP?",
 "11. Você leu todas as regras? Concorda com elas?","12. Qual seu horário disponível para jogar?",
 "13. Tem experiência com profissões? Qual?","14. O que você faria se visse alguém quebrando regra?",
 "15. Deixe um recado final para a STAFF"
]

class ConfigPanel(discord.ui.View):
 def __init__(self):super().__init__(timeout=None)
 @discord.ui.select(placeholder="⚙️ SELECIONE O QUE QUER CONFIGURAR",custom_id="config_select_v116",options=[
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
  msgs={"wc":"📝 Manda o ID do canal de whitelist","sc":"👮 Manda o ID do cargo de staff","tc":"📂 Manda o ID da CATEGORIA de tickets","lim":"🔢 Novo limite. Ex: 3","banner":"🖼️ Link da banner","prefix":"#️⃣ Novo prefixo. Ex:.","addcmd":"➕ nome | resposta","delcmd":"➖ nome","listcmd":f"📋 {', '.join(db['cmds'].keys()) if db['cmds'] else 'Nenhum'}"}
  if op=="raid":db["raid"]["on"]=not db["raid"]["on"];sv();await i.response.send_message(f"🚨 Anti-Raid: {'ON' if db['raid']['on'] else 'OFF'}",ephemeral=True)
  else:await i.response.send_message(msgs[op],ephemeral=True)

class StaffTicket(discord.ui.View):
 def __init__(self,uid,cid):super().__init__(timeout=None);self.uid=uid;self.cid=cid
 async def apagar(self,i):
  await i.response.send_message("🔒 Apagando em 3s...",ephemeral=True);await asyncio.sleep(3)
  ch=bot.get_channel(self.cid)
  if ch:await ch.delete()
  for k in [self.uid,f"step_{self.uid}",f"res_{self.uid}"]:db["tickets"].pop(k,None);sv()
 @discord.ui.button(label="ACEITAR",style=discord.ButtonStyle.green,emoji="✅",custom_id="accept_ticket_v116")
 async def accept(self,i,b):
  if not (i.user.guild_permissions.administrator or i.user.id==DONO or str(i.user.id)==db["cfg"]["sc"]):return await i.response.send_message("❌ Só STAFF",ephemeral=True)
  db["wl"][self.uid]["status"]="aprovado";sv();await (await bot.fetch_user(int(self.uid))).send("✅ **APROVADO** no Nosso RP!");await self.apagar(i)
 @discord.ui.button(label="RECUSAR",style=discord.ButtonStyle.red,emoji="❌",custom_id="deny_ticket_v116")
 async def deny(self,i,b):
  if not (i.user.guild_permissions.administrator or i.user.id==DONO or str(i.user.id)==db["cfg"]["sc"]):return await i.response.send_message("❌ Só STAFF",ephemeral=True)
  db["wl"][self.uid]["status"]="reprovado";sv();await (await bot.fetch_user(int(self.uid))).send("❌ **REPROVADO** no Nosso RP!");await self.apagar(i)
 @discord.ui.button(label="FECHAR",style=discord.ButtonStyle.gray,emoji="🔒",custom_id="close_ticket_v116")
 async def close(self,i,b):
  if not (i.user.guild_permissions.administrator or i.user.id==DONO or str(i.user.id)==db["cfg"]["sc"]):return await i.response.send_message("❌ Só STAFF",ephemeral=True)
  await self.apagar(i)

class WLStartButton(discord.ui.View):
 def __init__(self):super().__init__(timeout=None)
 @discord.ui.button(label="INICIAR WHITELIST",style=discord.ButtonStyle.green,emoji="📝",custom_id="wl_ticket_v116")
 async def start(self,i,b):
  uid=str(i.user.id)
  if uid in db["wl"] and db["wl"][uid]["status"]=="aprovado":return await i.response.send_message("❌ Já aprovado",ephemeral=True)
  if uid in db["tickets"]:return await i.response.send_message("❌ Ticket aberto",ephemeral=True)
  cat=bot.get_channel(db["cfg"]["tc"])
  if not cat:return await i.response.send_message("❌ Categoria não configurada no!botconfig",ephemeral=True)
  overwrites={i.guild.default_role:discord.PermissionOverwrite(view_channel=False),i.user:discord.PermissionOverwrite(view_channel=True,send_messages=True),i.guild.get_role(db["cfg"]["sc"]):discord.PermissionOverwrite(view_channel=True,send_messages=True)}
  ch=await i.guild.create_text_channel(f"wl-{i.user.name}",category=cat,overwrites=overwrites)
  db["tickets"][uid]=ch.id;db["tickets"][f"step_{uid}"]=0;db["tickets"][f"res_{uid}"]={};sv()
  await i.response.send_message(f"✅ Ticket: {ch.mention}",ephemeral=True)
  await ch.send(f"{i.user.mention} **WHITELIST NOSSO RP**\nResponda as 15 perguntas:");await ch.send(PERGUNTAS[0],view=StaffTicket(uid,ch.id))

@bot.event
async def on_message(m):
 if m.author.bot:return
 uid=str(m.author.id)
 if uid in db["tickets"] and m.channel.id==db["tickets"][uid]:
  s=db["tickets"][f"step_{uid}"];db["tickets"][f"res_{uid}"][f"p{s+1}"]=m.content;s+=1;db["tickets"][f"step_{uid}"]=s
  if s<len(PERGUNTAS):await m.channel.send(PERGUNTAS[s])
  else:
   db["wl"][uid]=db["tickets"][f"res_{uid}"];db["wl"][uid]["status"]="pendente";sv()
   ch=bot.get_channel(db["cfg"]["wc"]);e=discord.Embed(title=f"📝 WHITELIST - {m.author.name}",color=0xFF0000)
   for i,p in enumerate(PERGUNTAS):e.add_field(name=p[:50],value=db["tickets"][f"res_{uid}"][f"p{i+1}"][:100],inline=False)
   await ch.send(f"<@&{db['cfg']['sc']}>",embed=e);await m.channel.send("✅ Enviado! Aguarde a STAFF.")
 if m.content.startswith(db["cfg"]["prefix"]):
  cmd=m.content[len(db["cfg"]["prefix"]):].split()[0]
  if cmd in db["cmds"]:await m.channel.send(db["cmds"][cmd])
 await bot.process_commands(m)

@tasks.loop(minutes=1)
async def va():
 a=datetime.datetime.now().strftime("%H:%M")
 for x in db["an"][:]:
  if x["h"]==a:
   c=bot.get_channel(x["c"])
   if c:await c.send("@everyone",embed=discord.Embed(title="📢 ANÚNCIO NOSSO RP",description=x["m"],color=0xFF0000).set_image(url=db["cfg"]["banner"]))
   db["an"].remove(x);sv()

@bot.command()
async def whitelist(ctx):
 if ctx.channel.id!=db["cfg"]["wc"]:return await ctx.send(f"❌ Use <#{db['cfg']['wc']}>")
 await ctx.send(embed=discord.Embed(title="📝 WHITELIST NOSSO RP",description="15 perguntas. Clique!",color=0xFF0000).set_image(url=db["cfg"]["banner"]),view=WLStartButton())

@bot.command()
async def botconfig(ctx):
 if ctx.author.id!=DONO and str(ctx.author.id)!=db["cfg"]["sc"]:return await ctx.send("❌ Só DONO/STAFF")
 e=discord.Embed(title="⚙️ CENTRAL NOSSO RP",color=0xFF0000)
 e.add_field(name="📝 Canal WL",value=f"<#{db['cfg']['wc']}>" if db['cfg']['wc'] else "Não setado")
 e.add_field(name="👮 Cargo STAFF",value=f"<@&{db['cfg']['sc']}>" if db['cfg']['sc'] else "Não setado")
 e.add_field(name="📂 Categoria",value=f"<#{db['cfg']['tc']}>" if db['cfg']['tc'] else "Não setado")
 e.add_field(name="🚨 Anti-Raid",value="ON" if db['raid']['on'] else "OFF")
 e.add_field(name="#️⃣ Prefixo",value=f"`{db['cfg']['prefix']}`")
 await ctx.send(embed=e,view=ConfigPanel())

@bot.command()
@is_staff()
async def ban(ctx,member:discord.Member,*,motivo="Sem motivo"):await member.ban(reason=motivo);await ctx.send(f"🔨 {member.mention} BANIDO. Motivo: {motivo}")
@bot.command()
@is_staff()
async def kick(ctx,member:discord.Member,*,motivo="Sem motivo"):await member.kick(reason=motivo);await ctx.send(f"👢 {member.mention} EXPULSO. Motivo: {motivo}")
@bot.command()
@is_staff()
async def mute(ctx,member:discord.Member,tempo:int=10):
 role=discord.utils.get(ctx.guild.roles,name="Mutado")
 if not role:role=await ctx.guild.create_role(name="Mutado")
 for c in ctx.guild.channels:await c.set_permissions(role,send_messages=False)
 await member.add_roles(role);await ctx.send(f"🔇 {member.mention} mutado por {tempo}min")
 await asyncio.sleep(tempo*60);await member.remove_roles(role)
@bot.command()
@is_staff()
async def unmute(ctx,member:discord.Member):
 role=discord.utils.get(ctx.guild.roles,name="Mutado")
 if role:await member.remove_roles(role)
 await ctx.send(f"🔊 {member.mention} desmutado")
@bot.command()
@is_staff()
async def warn(ctx,member:discord.Member,*,motivo):
 uid=str(member.id);db["warns"].setdefault(uid,[]);db["warns"][uid].append(motivo);sv()
 await ctx.send(f"⚠️ {member.mention} WARN. Total: {len(db['warns'][uid])}")
@bot.command()
@is_staff()
async def warns(ctx,member:discord.Member):
 uid=str(member.id)
 if uid not in db["warns"] or not db["warns"][uid]:return await ctx.send("✅ Sem warns")
 txt="\n".join([f"{i+1}. {w}" for i,w in enumerate(db['warns'][uid])])
 await ctx.send(f"**WARNS DE {member.name}:**\n{txt}")
@bot.command()
@is_staff()
async def clear(ctx,amount:int=10):await ctx.channel.purge(limit=amount+1);await ctx.send(f"🧹 {amount} apagadas",delete_after=3)
@bot.command()
@is_staff()
async def anuncio(ctx,*,msg):
 for c in ctx.guild.text_channels:
  if c.name in ["anuncio","anuncios","avisos"]:
   await c.send("@everyone",embed=discord.Embed(title="📢 ANÚNCIO NOSSO RP",description=msg,color=0xFF0000).set_image(url=db["cfg"]["banner"]))
   return await ctx.send("✅ Enviado!")
 await ctx.send("❌ Crie #anuncios")
@bot.command()
@is_staff()
async def addcmd(ctx,*,args):
 try:nome,resposta=args.split("|",1);db["cmds"][nome.strip()]=resposta.strip();sv();await ctx.send(f"✅ `!{nome.strip()}` criado!")
 except:await ctx.send("❌ Use: `!addcmd nome | resposta`")
@bot.command()
@is_staff()
async def delcmd(ctx,nome):
 if nome in db["cmds"]:del db["cmds"][nome];sv();await ctx.send(f"✅ `!{nome}` deletado")
 else:await ctx.send("❌ Não existe")
@bot.command()
async def comandos(ctx):
 cmds="**COMANDOS:**\n`!whitelist` `!botconfig` `!comandos`\n`!ban` `!kick` `!mute` `!unmute` `!warn` `!warns` `!clear` `!anuncio` `!addcmd` `!delcmd`"
 if db["cmds"]:cmds+="\n\n**CUSTOM:** " + ", ".join([f"!{k}" for k in db["cmds"].keys()])
 await ctx.send(cmds)

@bot.event
async def setup_hook():
 bot.add_view(WLStartButton())
 bot.add_view(StaffTicket("0",0))
 bot.add_view(ConfigPanel())

@bot.event
async def on_ready():
 va.start()
 print("✅ V116 ONLINE - SEM ERRO")

bot.run(os.getenv("TOKEN"))
