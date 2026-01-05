import discord
from discord.ext import commands
import os
from web import keep_alive

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_cogs():
    for cog in ["meu_bot_farm.cogs.farm"]:
        try:
            await bot.load_extension(cog)
            print(f"[INFO] Cog carregado: {cog}")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar {cog}: {e}")

@bot.event
async def on_ready():
    print(f"[INFO] Bot ON como {bot.user} (ID: {bot.user.id})")

@bot.event
async def setup_hook():
    await load_cogs()

keep_alive()  # 🔥 mantém porta aberta
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)