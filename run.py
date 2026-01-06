import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🔥 Bot online como {bot.user}")
    await bot.load_extension("meu_bot_farm.cogs.tickets")

TOKEN = os.getenv("TOKEN")
print("TOKEN carregado?", bool(TOKEN))

if not TOKEN:
    raise RuntimeError("TOKEN não encontrado")

bot.run(TOKEN)