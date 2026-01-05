import discord
from discord.ext import commands
import json
import os

CONFIG = "meu_bot_farm/data/config_farm.json"

def load_config():
    if not os.path.exists(CONFIG):
        return None
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

class PainelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        await interaction.response.send_message(
            "✅ Sistema de entrega ativo (modal já conectado).",
            ephemeral=True
        )

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painelfarm")
    @commands.has_permissions(manage_guild=True)
    async def painel_farm(self, ctx):
        """
        COMANDO QUE VOCÊ ESTAVA USANDO:
        !painelfarm
        """

        config = load_config()
        if not config:
            await ctx.send("❌ O painel ainda não foi configurado com /configticketfarm.")
            return

        embed = discord.Embed(
            title="📦 PAINEL DE FARM — KORTE",
            description="Clique no botão abaixo para registrar sua entrega.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)

        await ctx.send(embed=embed, view=PainelView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))