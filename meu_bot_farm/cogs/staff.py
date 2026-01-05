import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands
from discord import app_commands
import json
import os

ADVS = "meu_bot_farm/data/advs.json"

# ================== JSON ==================
def load(path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ================== COG ==================
class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- VER ADV ----------
    @app_commands.command(
        name="veradv",
        description="Ver advertências de um membro"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def veradv(
        self,
        interaction: discord.Interaction,
        membro: discord.Member
    ):
        advs = load(ADVS)
        await interaction.response.send_message(
            f"⚠️ {membro.mention} possui **{advs.get(str(membro.id), 0)} ADV(s)**",
            ephemeral=True
        )

    # ---------- ADICIONAR ADV ----------
    @app_commands.command(
        name="addadv",
        description="Aplicar advertência manual"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def addadv(
        self,
        interaction: discord.Interaction,
        membro: discord.Member
    ):
        advs = load(ADVS)
        advs[str(membro.id)] = advs.get(str(membro.id), 0) + 1
        save(ADVS, advs)

        await interaction.response.send_message(
            f"⚠️ ADV aplicado em {membro.mention}",
            ephemeral=True
        )

    # ---------- REMOVER ADV ----------
    @app_commands.command(
        name="removeadv",
        description="Remover advertência manual"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def removeadv(
        self,
        interaction: discord.Interaction,
        membro: discord.Member
    ):
        advs = load(ADVS)
        advs[str(membro.id)] = max(0, advs.get(str(membro.id), 0) - 1)
        save(ADVS, advs)

        await interaction.response.send_message(
            f"✅ ADV removido de {membro.mention}",
            ephemeral=True
        )

    # ---------- ERRO DE PERMISSÃO ----------
    @veradv.error
    @addadv.error
    @removeadv.error
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error
    ):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Você não tem permissão para usar este comando.",
                ephemeral=True
            )

# ================== SETUP ==================
async def setup(bot):
    await bot.add_cog(Staff(bot))