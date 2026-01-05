import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CONFIG = "meu_bot_farm/data/config_farm.json"
ENTREGAS = "meu_bot_farm/data/entregas.json"
ADVS = "meu_bot_farm/data/advs.json"

# ================== JSON ==================
def load(path, default):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ================== COG ==================
class Metas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def meta_por_cargo(self, member: discord.Member, config: dict):
        cargos = [r.name.lower() for r in member.roles]
        metas = config.get("metas", {})

        if "aviãozinho" in cargos:
            return metas.get("Aviãozinho")
        if "membro" in cargos:
            return metas.get("Membro")
        if "recrutador" in cargos:
            return metas.get("Recrutador")
        if "gerente" in cargos:
            return metas.get("Gerente")
        return None

    @app_commands.command(
        name="entregar",
        description="Registrar entrega de farm"
    )
    async def entregar(
        self,
        interaction: discord.Interaction,
        quantidade: int
    ):
        config = load(CONFIG, {})
        entregas = load(ENTREGAS, {})
        advs = load(ADVS, {})

        meta = self.meta_por_cargo(interaction.user, config)
        if not meta:
            return await interaction.response.send_message(
                "❌ Seu cargo não possui meta configurada.",
                ephemeral=True
            )

        uid = str(interaction.user.id)
        entregas[uid] = entregas.get(uid, 0) + quantidade

        texto = (
            f"📦 **Entrega registrada**: {quantidade}\n"
            f"🎯 **Meta do seu cargo**: {meta}\n"
            f"📊 **Total entregue**: {entregas[uid]}"
        )

        if entregas[uid] >= meta:
            texto += "\n✅ **Meta cumprida!**"

            if entregas[uid] >= meta * 2 and advs.get(uid, 0) > 0:
                advs[uid] -= 1
                texto += "\n🔁 **1 ADV removido por compensação**"

        save(ENTREGAS, entregas)
        save(ADVS, advs)

        await interaction.response.send_message(texto, ephemeral=True)

# ================== SETUP ==================
async def setup(bot):
    await bot.add_cog(Metas(bot))