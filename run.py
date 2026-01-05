import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands
from web import keep_alive

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "meu_bot_farm.cogs.farm",
    "meu_bot_farm.cogs.tickets",
    "meu_bot_farm.cogs.metas",
    "meu_bot_farm.cogs.staff",
    "meu_bot_farm.cogs.cargos",
]

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"[OK] Cog carregado: {cog}")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar {cog}: {e}")

@bot.event
async def setup_hook():
    await load_cogs()

@bot.event
async def on_ready():
    print(f"🔥 Bot ONLINE como {bot.user}")

keep_alive()  # mantém a porta aberta no Render
bot.run(os.getenv("DISCORD_TOKEN"))