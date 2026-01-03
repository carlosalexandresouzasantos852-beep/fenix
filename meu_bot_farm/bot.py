import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
import asyncio
from discord.ext import commands
from meu_bot_farm.config import BOT_PREFIX, TOKEN  # ✅ CORRETO

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=BOT_PREFIX,
    intents=intents
)

EXTENSIONS = [
    "meu_bot_farm.cogs.tickets",
    "meu_bot_farm.cogs.farm",
    "meu_bot_farm.cogs.staff",
    "meu_bot_farm.cogs.cargos",
    "meu_bot_farm.cogs.metas",
    "meu_bot_farm.cogs.config_farm",
]

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Slash sincronizados: {len(synced)}")
    except Exception as e:
        print(f"❌ Erro ao sincronizar slash: {e}")

    print(f"🔥 Bot online como {bot.user} (ID: {bot.user.id})")

async def main():
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"[COG] Carregado: {ext}")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar {ext}: {e}")

    await bot.start(TOKEN)

asyncio.run(main())