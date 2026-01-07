import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands

# ================== INTENTS ==================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# ================== BOT ==================
class MeuBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        # 🔹 LISTA DE COGS (TODOS!)
        cogs = [
            "meu_bot_farm.cogs.tickets",
            "meu_bot_farm.cogs.config_farm",
            "meu_bot_farm.cogs.metas",
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Cog carregado: {cog}")
            except Exception as e:
                print(f"❌ Erro ao carregar {cog}: {e}")

        # 🔹 SINCRONIZA SLASH COMMANDS (GLOBAL)
        synced = await self.tree.sync()
        print(f"🚀 Slash commands sincronizados: {len(synced)}")

# ================== START ==================
bot = MeuBot()

@bot.event
async def on_ready():
    print(f"🔥 Bot online como {bot.user}")

TOKEN = os.getenv("TOKEN")
print("TOKEN carregado?", bool(TOKEN))

if not TOKEN:
    raise RuntimeError("❌ TOKEN não encontrado nas variáveis de ambiente")

bot.run(TOKEN)