import discord
from discord.ext import commands
import os

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# Carregar cogs
async def load_cogs():
    for cog in ["meu_bot_farm.cogs.farm"]:
        try:
            await bot.load_extension(cog)
            print(f"[INFO] Cog carregado: {cog}")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar {cog}: {e}")

@bot.event
async def setup_hook():
    await load_cogs()

@bot.event
async def on_ready():
    # 🔥 SINCRONIZA OS SLASH COMMANDS
    synced = await bot.tree.sync()
    print(f"[INFO] {len(synced)} slash commands sincronizados")
    print(f"[INFO] Bot ON como {bot.user} (ID: {bot.user.id})")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)