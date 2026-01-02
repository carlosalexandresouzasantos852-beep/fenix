import discord
import asyncio
from discord.ext import commands
from config import BOT_PREFIX, TOKEN

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=BOT_PREFIX,
    intents=intents
)

EXTENSIONS = [
    "cogs.tickets",
    "cogs.farm",
    "cogs.staff",
    "cogs.cargos",
    "cogs.metas",
    "cogs.config_farm",
]

@bot.event
async def on_ready():
    # 🔥 SINCRONIZA SLASH NO MOMENTO CERTO
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