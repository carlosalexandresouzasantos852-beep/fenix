import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands
from web import keep_alive

# ================== INTENTS ==================
intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ================== COGS ==================
COGS = [
    "meu_bot_farm.cogs.farm",
    "meu_bot_farm.cogs.config_farm",
    "meu_bot_farm.cogs.staff",
    "meu_bot_farm.cogs.cargos",
]

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"[INFO] Cog carregado: {cog}")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar {cog}: {e}")

# ================== EVENTS ==================
@bot.event
async def setup_hook():
    await load_cogs()

    # 🔥 sincroniza slash commands
    synced = await bot.tree.sync()
    print(f"[INFO] {len(synced)} slash commands sincronizados")

@bot.event
async def on_ready():
    print(f"[INFO] Bot ON como {bot.user} (ID: {bot.user.id})")

# ================== START ==================
keep_alive()  # mantém a porta aberta no Render

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN não encontrado nas variáveis de ambiente")

bot.run(TOKEN)