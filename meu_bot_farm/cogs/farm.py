import discord
from discord.ext import commands
from discord import app_commands

class Farm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================== PING ==================
    @app_commands.command(
        name="ping",
        description="Testar se o bot está online"
    )
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🏓 Pong funcionando",
            ephemeral=True
        )

    # ================== META ==================
    @app_commands.command(
        name="meta",
        description="Definir meta de farm"
    )
    async def meta(
        self,
        interaction: discord.Interaction,
        quantidade: int
    ):
        await interaction.response.send_message(
            f"🎯 Meta definida: **{quantidade}**",
            ephemeral=True
        )

    # ================== ENTREGA ==================
    @app_commands.command(
        name="entrega",
        description="Registrar entrega de farm"
    )
    async def entrega(
        self,
        interaction: discord.Interaction,
        quantidade: int
    ):
        await interaction.response.send_message(
            f"📦 Entrega registrada: **{quantidade}**",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Farm(bot))