import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands
from discord import app_commands

class Cargos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="subir",
        description="Sobe automaticamente de Aviãozinho para Membro"
    )
    async def subir(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        antigo = discord.utils.get(guild.roles, name="Aviãozinho")
        novo = discord.utils.get(guild.roles, name="Membro")

        if not antigo or not novo:
            await interaction.response.send_message(
                "❌ Cargos não encontrados.",
                ephemeral=True
            )
            return

        if antigo not in member.roles:
            await interaction.response.send_message(
                "❌ Você não possui o cargo necessário.",
                ephemeral=True
            )
            return

        await member.remove_roles(antigo)
        await member.add_roles(novo)

        await interaction.response.send_message(
            "✅ Cargo atualizado automaticamente!",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Cargos(bot))