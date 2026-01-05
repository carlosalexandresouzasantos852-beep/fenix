import discord
from discord.ext import commands
import os
import threading
import uvicorn
from web import app  # seu web.py

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# Função para rodar o servidor HTTP (mantém bot online no Render)
# =====================
def start_web():
    uvicorn.run(app, host="0.0.0.0", port=10000)

threading.Thread(target=start_web).start()  # roda em background

# =====================
# Carregar COGs
# =====================
async def load_cogs():
    await bot.load_extension("meu_bot_farm.cogs.tickets")

# =====================
# Evento ready
# =====================
@bot.event
async def on_ready():
    print(f"🔥 Bot online! Usuário: {bot.user}")
    await load_cogs()

# =====================
# Rodar o bot
# =====================
TOKEN = os.getenv("TOKEN")  # variável de ambiente no Render
bot.run(TOKEN)