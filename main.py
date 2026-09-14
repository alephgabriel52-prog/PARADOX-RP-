import discord,os,json,datetime,asyncio
from discord.ext import commands,tasks
from flask import Flask
from threading import Thread

print("INICIANDO V124...")
app=Flask('')
@app.route('/')
def h():return"V124 NOSSO RP"
Thread(target=lambda:app.run(host='0.0.0.0',port=8080)).start()

intents=discord.Intents.all()
intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

BANNER="https://cdn.discordapp.com/attachments/1527669780364918925/1549093554960474243/file_0005a0820e8df98c1974ab6ecc.png"
DONO=1438010935783460954

# ====== ATENÇÃO: TROCA ESSES 3 IDS ======
CANAL_WL_ID = 1527669780364918925 # ID do CANAL #whitelist
CARGO_STAFF_ID = 0 # ID DO CARGO STAFF - TROCA!
CAT_TICKET_ID = 1526291631467397400 # ID da CATEGORIA - NÃO DO CANAL!
# =====================================

try:db=json.load(open('db.json'))
except:db={"cfg":{"tc":CAT_TICKET_ID,"sc":CARGO_STAFF_ID,"wc":CANAL_WL_ID,"tr":DONO,"banner":BANNER,"prefix":"!"},"an":[],"raid":{"on":False,"lim":5},"wl":{},"warns":{},"cmds":{},"tickets":{},"awaiting":{}}
def sv():
 with open('db.json','w') as f:json.dump(db,f)

def is_staff():
 async def p(ctx):return ctx.author.guild_permissions.administrator or ctx.author.id==DONO or str(ctx.author.id)==str(db["cfg"]["sc"])
 return commands.check(p)

PERGUNTAS=["1. Qual seu nome completo e idade?","2. Você tem microfone? Sabe usar?","3. Já jogou RP antes? Qual cidade?","4. Qual seu nível de interpretação RP de 0 a 10?","5. O que é RDM?","6. O que é VDM?","7. O que é Meta Gaming?","8. O que é Power Gaming?","9. O que é Fail RP?","10. Por que quer entrar no Nosso RP?","11. Você leu todas as regras? Concorda com elas?","12. Qual seu horário disponível para jogar?","13. Tem experiência com profissões? Qual?","14. O que você faria se visse alguém quebrando regra?","15. Deixe um recado final para a STAFF"]

async def criar_ticket(guild,user):
 uid=str(user.id)
 if uid in db["wl"] and db["wl"][uid]["status"]=="aprovado":return None,"Você já foi aprovado na whitelist!"
 if uid in db["tickets"]:return None,"Você já possui um ticket aberto!"
 cat=bot.get_channel(db["cfg"]["tc"])
 if not cat:return None,f"❌ Categoria de tickets não encontrada!\nID: {db['cfg']['tc']}\nVá em!botconfig e configure a CATEGORIA certo."
 try:
  overwrites={guild.default_role:discord.PermissionOverwrite(view_channel=False),user:discord.PermissionOverwrite(view_channel=True,send_messages=True),guild.get_role(db["cfg"]["sc"]):discord.PermissionOverwrite(view_channel=True,send_messages=True)}
  ch=await guild.create_text_channel(f"wl-{user.name}",category=cat,overwrites=overwrites)
 except Exception as e:
  return None,f"❌ Erro ao criar canal: {e}"
 db["tickets"][uid]=ch.id;db["tickets"][f"step_{uid}"]=0;db["tickets"][f"res_{uid}"]={};sv()
 embed=discord.Embed(title="📝 WHITELIST NOSSO RP",description=f"Olá {user.mention}!\n\nBem-vindo ao processo de Whitelist do **NOSSO RP**!\nResponda 15 perguntas.",color=0xFF0000)
 embed.set_image(url=db["cfg"]["banner"])
 await ch.send(embed=embed)
 await ch.send(PERGUNTAS[0],view=StaffTicket(uid,ch.id))
 return ch,None

class ConfigPanel(discord.ui.View):
 def __init__(self):super().__init__(timeout=None)
 @discord.ui.select(placeholder="⚙️ SELECIONE O QUE QUER CONFIGURAR",custom_id="config_select_v124",options=[discord.SelectOption(label="Canal de Whitelist",emoji="📝",value="wc"),discord.SelectOption(label="Cargo da Staff",emoji="👮",value="sc"),discord.SelectOption(label="Categoria de Tickets",emoji="📂",value="tc"),discord.SelectOption(label="Anti-Raid ON/OFF",emoji="🚨",value="raid"),discord.SelectOption(label="Limite Anti-Raid",emoji="🔢",value="lim"),discord.SelectOption(label="Trocar Banner",emoji="🖼️",value="banner"),discord.SelectOption(label="Prefixo do Bot",emoji="#️⃣",value="prefix"),discord.SelectOption(label="Criar Comando Custom",emoji="➕",value="addcmd"),discord.SelectOption(label="Deletar Comando",emoji="➖",value="delcmd"),discord.SelectOption(label="Listar Comandos",emoji="📋",value="listcmd"),])
 async def select(self,i,s):
  if i.user.id!=DONO and str(i.user.id)!=str(db["cfg"]["sc"]):return await i.response.send_message("❌ Sem permissão",ephemeral=True)
  op=s.values[0];uid=str(i.user.id);db["awaiting"][uid]=op;sv()
  msgs={"wc":"📝 Manda o ID do canal de whitelist","sc":"👮 Manda o ID do cargo de staff","tc":"📂 Manda o ID da CATEGORIA","lim":"🔢 Manda o novo limite","banner":"🖼️ Manda o link da banner","prefix":"#️⃣ Manda o novo prefixo","addcmd":"➕ Use: nome | resposta","delcmd":"➖ Manda o nome do comando","listcmd":f"📋 {', '.join(db['cmds'].keys()) if db['cmds'] else 'Nenhum'}"}
  if op=="raid":db["raid"]["on"]=not db["raid"]["on"];db["awaiting"].pop(uid,None);sv();await i.response.send_message(f"🚨 Anti-Raid: {'ON' if db['raid']['on'] else 'OFF'}",ephemeral=True)
  else:await i.response.send_message(msgs[op],ephemeral=True)

class StaffTicket(discord.ui.View):
 def __init__(self,uid,cid):super().__init__(timeout=None);self.uid=uid;self.cid=cid
 async def apagar(self,i):
  await i.response.send_message("🔒 Fechando ticket em 3s...",ephemeral=True);await asyncio.sleep(3)
  ch=bot.get_channel(self.cid)
  if ch:await ch.delete()
  for k in [self.uid,f"step_{self.uid}",f"res_{self.uid}"]:db["tickets"].pop(k,None);sv()
 @discord.ui.button(label="ACEITAR",style=discord.ButtonStyle.green,emoji="✅",custom_id="accept_ticket_v124")
 async def accept(self,i,b):
  if not (i.user.guild_permissions.administrator or i.user.id==DONO or str(i.user.id)==str(db["cfg"]["sc"])):return await i.response.send_message("❌ Só STAFF",ephemeral=True)
  db["wl"][self.uid]["status"]="aprovado";sv();await (await bot.fetch_user(int(self.uid))).send("✅ **APROVADO** no Nosso RP!");e=discord.Embed(title="✅ APROVADO",description=f"Aprovado por: {i.user.mention}",color=0x00FF00);await i.response.send_message(embed=e);await self.apagar(i)
 @discord.ui.button(label="RECUSAR",style=discord.ButtonStyle.red,emoji="❌",custom_id="deny_ticket_v124")
 async def deny(self,i,b):
  if not (i.user.guild_permissions.administrator or i.user.id==DONO or str(i.user.id)==str(db["cfg"]["sc"])):return await i.response.send_message("❌ Só STAFF",ephemeral=True)
  db["wl"][self.uid]["status"]="reprovado";sv();await (await bot.fetch_user(int(self.uid))).send("❌ **REPROVADO** no Nosso RP!");e=discord.Embed(title="❌ REPROVADO",description=f"Reprovado por: {i.user.mention}",color=0xFF0000);await i.response.send_message(embed=e);await self.apagar(i)
 @discord.ui.button(label="FECHAR",style=discord.ButtonStyle.gray,emoji="🔒",custom_id="close_ticket_v124")
 async def close(self,i,b):
  if not (i.user.guild_permissions.administrator or i.user.id==DONO or str(i.user.id)==str(db["cfg"]["sc"])):return await i.response.send_message("❌ Só STAFF",ephemeral=True)
  e=discord.Embed(title="🔒 TICKET FECHADO",description=f"Fechado por: {i.user.mention}",color=0x808080);await i.response.send_message(embed=e);await self.apagar(i)

class WLStartButton(discord.ui.View):
 def __init__(self):super().__init__(timeout=None)
 @discord.ui.button(label="INICIAR WHITELIST",style=discord.ButtonStyle.green,emoji="📝",custom_id="wl_ticket_v124")
 async def start(self,i,b):
  ch,erro=await criar_ticket(i.guild,i.user)
  if erro:return await i.response.send_message(erro,ephemeral=True)
  await i.response.send_message(f"✅ Ticket criado: {ch.mention}",ephemeral=True)

@bot.event
async def on_message(m):
 if m.author.bot:return
 uid=str(m.author.id)
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
   await m.reply(f"✅ {tipo.upper()} configurado!")
   return
  except:await m.reply("❌ Valor inválido.")
 if uid in db["tickets"] and m.channel.id==db["tickets"][uid]:
  s=db["tickets"][f"step_{uid}"];db["tickets"][f"res_{uid}"][f"p{s+1}"]=m.content;s+=1;db["tickets"][f"step_{uid}"]=s
  if s<len(PERGUNTAS):await m.channel.send(PERGUNTAS[s])
  else:
   db["wl"][uid]=db["tickets"][f"res_{uid}"];db["wl"][uid]["status"]="pendente";sv()
   ch=bot.get_channel(db["cfg"]["wc"])
   if ch:
    e=discord.Embed(title=f"📝 WHITELIST - {m.author.name}",color=0xFF0000)
    for i,p in enumerate(PERGUNTAS):e.add_field(name=p[:50],value=db["tickets"][f"res_{uid}"][f"p{i+1}"][:100],inline=False)
    await ch.send(f"<@&{db['cfg']['sc']}> Nova whitelist!",embed=e)
   await m.channel.send("✅ Enviado! Aguarde a STAFF.")
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
 e=discord.Embed(title="📝 WHITELIST NOSSO RP",description="Clique no botão abaixo para iniciar sua whitelist.\n\n15 perguntas sobre RP.",color=0xFF0000).set_image(url=db["cfg"]["banner"])
 await ctx.send(embed=e,view=WLStartButton())

@bot.command()
async def ticket(ctx):
 ch,erro=await criar_ticket(ctx.guild,ctx.author)
 if erro:return await ctx.send(erro)
 await ctx.send(f"✅ Ticket criado: {ch.mention}")

@bot.command()
async def botconfig(ctx):
 if ctx.author.id!=DONO and str(ctx.author.id)!=str(db["cfg"]["sc"]):return await ctx.send("❌ Só DONO/STAFF")
 e=discord.Embed(title="⚙️ CENTRAL NOSSO RP",color=0xFF0000)
 e.add_field(name="📝 Canal WL",value=f"<#{db['cfg']['wc']}>" if db['cfg']['wc'] else "Não setado")
 e.add_field(name="👮 Cargo STAFF",value=f"<@&{db['cfg']['sc']}>" if db['cfg']['sc'] else "Não setado")
 e.add_field(name="📂 Categoria",value=f"<#{db['cfg']['tc']}>" if db['cfg']['tc'] else "Não setado")
 e.add_field(name="🚨 Anti-Raid",value="ON" if db['raid']['on'] else "OFF")
 await ctx.send(embed=e,view=ConfigPanel())

@bot.command()@is_staff()
async def ban(ctx,member:discord.Member,*,motivo="Sem motivo"):await member.ban(reason=motivo);await ctx.send(embed=discord.Embed(title="🔨 BANIDO",description=f"{member.mention} | Motivo: {motivo}",color=0xFF0000))
@bot.command()@is_staff()
async def kick(ctx,member:discord.Member,*,motivo="Sem motivo"):await member.kick(reason=motivo);await ctx.send(embed=discord.Embed(title="👢 EXPULSO",description=f"{member.mention} | Motivo: {motivo}",color=0xFFA500))
@bot.command()@is_staff()
async def mute(ctx,member:discord.Member,tempo:int=10):
 role=discord.utils.get(ctx.guild.roles,name="Mutado")
 if not role:role=await ctx.guild.create_role(name="Mutado")
 for c in ctx.guild.channels:await c.set_permissions(role,send_messages=False)
 await member.add_roles(role);await ctx.send(embed=discord.Embed(title="🔇 MUTADO",description=f"{member.mention} por {tempo}min",color=0x808080))
 await asyncio.sleep(tempo*60);await member.remove_roles(role)
@bot.command()@is_staff()
async def unmute(ctx,member:discord.Member):
 role=discord.utils.get(ctx.guild.roles,name="Mutado")
 if role:await member.remove_roles(role)
 await ctx.send(embed=discord.Embed(title="🔊 DESMUTADO",description=f"{member.mention}",color=0x00FF00))
@bot.command()@is_staff()
async def warn(ctx,member:discord.Member,*,motivo):
 uid=str(member.id);db["warns"].setdefault(uid,[]);db["warns"][uid].append(motivo);sv()
 await ctx.send(embed=discord.Embed(title="⚠️ WARN",description=f"{member.mention}\nMotivo: {motivo}\nTotal: {len(db['warns'][uid])}",color=0xFFFF00))
@bot.command()@is_staff()
async def warns(ctx,member:discord.Member):
 uid=str(member.id)
 if uid not in db["warns"] or not db["warns"][uid]:return await ctx.send("✅ Sem warns")
 txt="\n".join([f"{i+1}. {w}" for i,w in enumerate(db['warns'][uid])])
 await ctx.send(embed=discord.Embed(title=f"WARNS DE {member.name}",description=txt,color=0xFFFF00))
@bot.command()@is_staff()
async def clear(ctx,amount:int=10):await ctx.channel.purge(limit=amount+1);await ctx.send(embed=discord.Embed(title="🧹 LIMPO",description=f"{amount} mensagens apagadas",color=0x00FFFF),delete_after=5)
@bot.command()@is_staff()
async def anuncio(ctx,*,msg):
 for c in ctx.guild.text_channels:
  if c.name in ["anuncio","anuncios","avisos"]:
   await c.send("@everyone",embed=discord.Embed(title="📢 ANÚNCIO",description=msg,color=0xFF0000).set_image(url=db["cfg"]["banner"]))
   return await ctx.send("✅ Enviado!")
 await ctx.send("❌ Crie #anuncios")
@bot.command()@is_staff()
async def addcmd(ctx,*,args):
 try:nome,resposta=args.split("|",1);db["cmds"][nome.strip()]=resposta.strip();sv();await ctx.send(f"✅ `!{nome.strip()}` criado!")
 except:await ctx.send("❌ Use: `!addcmd nome | resposta`")
@bot.command()@is_staff()
async def delcmd(ctx,nome):
 if nome in db["cmds"]:del db["cmds"][nome];sv();await ctx.send(f"✅ `!{nome}` deletado")
 else:await ctx.send("❌ Não existe")
@bot.command()
async def comandos(ctx):
 e=discord.Embed(title="📋 COMANDOS NOSSO RP",color=0xFF0000)
 e.add_field(name="📝 WHITELIST",value="`!whitelist` `!ticket`",inline=False)
 e.add_field(name="👮 MODERAÇÃO",value="`!ban` `!kick` `!mute` `!unmute` `!warn` `!warns` `!clear`",inline=False)
 e.add_field(name="⚙️ ADMIN",value="`!botconfig` `!anuncio` `!addcmd` `!delcmd` `!comandos`",inline=False)
 if db["cmds"]:e.add_field(name="🔧 CUSTOM",value=", ".join([f"!{k}" for k in db["cmds"].keys()]),inline=False)
 await ctx.send(embed=e)

@bot.event
async def setup_hook():
 bot.add_view(WLStartButton())
 bot.add_view(StaffTicket("0",0))
 bot.add_view(ConfigPanel())

@bot.event
async def on_ready():
 va.start()
 print("✅ V124 ONLINE")

bot.run(os.getenv("TOKEN"))
