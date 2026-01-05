import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands
from meu_bot_farm.utils.logger import setup_logger

logger = setup_logger("BOT")

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

async def load_cogs():
    cogs = [
        "meu_bot_farm.cogs.farm",
        "meu_bot_farm.cogs.config_farm",
        "meu_bot_farm.cogs.cargos",
        "meu_bot_farm.cogs.staff"
        "meu_bot_farm.cogs.adv_automatico"
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Cog carregado: {cog}")
        except Exception as e:
            logger.error(f"Erro ao carregar {cog}: {e}")

@bot.event
async def setup_hook():
    await load_cogs()
    synced = await bot.tree.sync()
    logger.info(f"{len(synced)} slash commands sincronizados")

@bot.event
async def on_ready():
    logger.info(f"Bot ONLINE como {bot.user} | ID: {bot.user.id}")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)