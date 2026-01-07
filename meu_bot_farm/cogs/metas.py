import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands
import json

CONFIG = "meu_bot_farm/data/config_farm.json"


# ================== JSON ==================
def load(path, default):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ================== COG ==================
class Metas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cargo_do_usuario(self, member: discord.Member) -> str | None:
        cargos = [r.name.lower() for r in member.roles]

        if "aviãozinho" in cargos:
            return "aviãozinho"
        if "membro" in cargos:
            return "membro"
        if "recrutador" in cargos:
            return "recrutador"
        if "gerente" in cargos:
            return "gerente"

        return None

    def meta_por_usuario(self, member: discord.Member) -> int | None:
        config = load(CONFIG, {})
        metas = config.get("metas", {})

        cargo = self.cargo_do_usuario(member)
        if not cargo:
            return None

        return metas.get(cargo)


# ================== SETUP ==================
async def setup(bot):
    await bot.add_cog(Metas(bot))