import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands
from web import keep_alive

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

COGS = [
    "meu_bot_farm.cogs.config_farm",  # slash
    "meu_bot_farm.cogs.staff",        # slash
    "meu_bot_farm.cogs.tickets",      # prefixo (painel)
    "meu_bot_farm.cogs.cargos",
    "meu_bot_farm.cogs.farm"
]

@bot.event
async def setup_hook():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog carregado: {cog}")
        except Exception as e:
            print(f"❌ Erro ao carregar {cog}: {e}")

    # 🔥 ISSO GARANTE QUE OS SLASH VOLTEM
    synced = await bot.tree.sync()
    print(f"🔁 {len(synced)} slash commands sincronizados")

@bot.event
async def on_ready():
    print(f"🤖 Bot online como {bot.user} ({bot.user.id})")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))