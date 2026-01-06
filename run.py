import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🔥 Bot online: {bot.user}")
    await bot.load_extension("meu_bot_farm.cogs.tickets")

TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)