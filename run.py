import discord
from discord.ext import commands
import os
import asyncio
import traceback
from web import keep_alive

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# Keep alive HTTP
# =====================
keep_alive()

# =====================
# Ready
# =====================
@bot.event
async def on_ready():
    print(f"🔥 Bot online: {bot.user}")
    try:
        await bot.load_extension("meu_bot_farm.cogs.tickets")
        print("✅ tickets.py carregado")
    except Exception as e:
        print("❌ Erro ao carregar tickets.py")
        traceback.print_exc()

# =====================
# Captura QUALQUER erro global
# =====================
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Erro global no evento {event}")
    traceback.print_exc()

# =====================
# Run seguro
# =====================
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN não definido no Render")

while True:
    try:
        bot.run(TOKEN)
    except Exception:
        print("⚠️ Bot caiu — reiniciando em 5s")
        traceback.print_exc()
        asyncio.sleep(5)