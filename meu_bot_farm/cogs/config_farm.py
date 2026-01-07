import discord
from discord.ext import commands
from discord import app_commands

from meu_bot_farm.utils.config_manager import get_config, set_config


class ConfigFarm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setcanal_adv", description="Define o canal de advertências")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_canal_adv(self, interaction: discord.Interaction, canal: discord.TextChannel):
        set_config(interaction.guild.id, "canal_adv", canal.id)
        await interaction.response.send_message(
            f"✅ Canal de advertências definido para {canal.mention}",
            ephemeral=True
        )

    @app_commands.command(name="ver_config", description="Mostra a configuração atual do servidor")
    async def ver_config(self, interaction: discord.Interaction):
        cfg = get_config(interaction.guild.id)

        embed = discord.Embed(
            title="⚙️ Configuração do Servidor",
            color=discord.Color.blue()
        )

        for k, v in cfg.items():
            embed.add_field(name=k, value=str(v), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ConfigFarm(bot))