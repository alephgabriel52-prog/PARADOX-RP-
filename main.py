import discord,os
bot=commands.Bot("!")
@bot.event
async def on_ready():print("RESET FORCADO")
bot.run(os.getenv("TOKEN"))
