import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands
from discord import app_commands
import json

CONFIG_PATH = "meu_bot_farm/data/config_farm.json"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data):
    os.makedirs("meu_bot_farm/data", exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class ConfigFarm(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="configticketfarm",
        description="Configurar sistema de ticket/farm"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def config_ticket_farm(
        self,
        interaction: discord.Interaction,

        meta_aviao: int,
        meta_membro: int,
        meta_recrutador: int,
        meta_gerente: int,

        categoria_analise: discord.CategoryChannel,
        canal_aceitos: discord.TextChannel,
        canal_recusados: discord.TextChannel,
        canal_adv: discord.TextChannel
    ):
        config = {
            "metas": {
                "Aviãozinho": meta_aviao,
                "Membro": meta_membro,
                "Recrutador": meta_recrutador,
                "Gerente": meta_gerente
            },
            "categoria_analise": categoria_analise.id,
            "canal_aceitos": canal_aceitos.id,
            "canal_recusados": canal_recusados.id,
            "canal_adv": canal_adv.id
        }

        save_config(config)

        await interaction.response.send_message(
            "✅ **Configuração do Ticket Farm salva com sucesso!**",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigFarm(bot))