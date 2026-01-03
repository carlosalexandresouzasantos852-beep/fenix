import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord, json, os
from discord.ext import commands
from discord import app_commands

ADVS = "meu_bot_farm/data/advs.json"

def load(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)
    with open(path) as f:
        return json.load(f)

def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="veradv", description="Ver ADV de um membro")
    async def veradv(self, interaction: discord.Interaction, membro: discord.Member):
        advs = load(ADVS)
        await interaction.response.send_message(
            f"⚠️ {membro.mention} possui {advs.get(str(membro.id), 0)} ADV",
            ephemeral=True
        )

    @app_commands.command(name="addadv", description="Aplicar ADV manual")
    async def addadv(self, interaction: discord.Interaction, membro: discord.Member):
        advs = load(ADVS)
        advs[str(membro.id)] = advs.get(str(membro.id), 0) + 1
        save(ADVS, advs)
        await interaction.response.send_message("ADV aplicado.", ephemeral=True)

    @app_commands.command(name="removeadv", description="Remover ADV manual")
    async def removeadv(self, interaction: discord.Interaction, membro: discord.Member):
        advs = load(ADVS)
        advs[str(membro.id)] = max(0, advs.get(str(membro.id), 0) - 1)
        save(ADVS, advs)
        await interaction.response.send_message("ADV removido.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Staff(bot))