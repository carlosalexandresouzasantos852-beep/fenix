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

# =========================
# MODAL DE ENTREGA
# =========================
class EntregaModal(discord.ui.Modal, title="📦 Entrega de Farm"):
    quantidade = discord.ui.TextInput(
        label="Quantidade entregue",
        placeholder="Ex: 150",
        required=True
    )
    entregue_para = discord.ui.TextInput(
        label="Entregue para quem?",
        placeholder="Nome ou ID",
        required=True
    )

    def __init__(self, cargo):
        super().__init__()
        self.cargo = cargo

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ Entrega registrada!\n\n"
            f"**Cargo:** {self.cargo}\n"
            f"**Quantidade:** {self.quantidade}\n"
            f"**Para:** {self.entregue_para}",
            ephemeral=True
        )

# =========================
# VIEW DO PAINEL
# =========================
class PainelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cargo_selecionado = None

    @discord.ui.select(
        placeholder="Selecione seu cargo",
        options=[
            discord.SelectOption(label="✈️ Aviãozinho", value="Aviãozinho"),
            discord.SelectOption(label="👤 Membro", value="Membro"),
            discord.SelectOption(label="📣 Recrutador", value="Recrutador"),
            discord.SelectOption(label="🛡️ Gerente", value="Gerente"),
        ]
    )
    async def selecionar_cargo(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.cargo_selecionado = select.values[0]
        await interaction.response.send_message(
            f"✅ Cargo selecionado: **{self.cargo_selecionado}**",
            ephemeral=True
        )

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        if not self.cargo_selecionado:
            await interaction.response.send_message(
                "❌ Selecione seu cargo antes de entregar o farm.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            EntregaModal(self.cargo_selecionado)
        )

# =========================
# COG
# =========================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painelfarm")
    @commands.has_permissions(manage_guild=True)
    async def painel_farm(self, ctx):
        config = load_config()
        if not config:
            await ctx.send("❌ O painel ainda não foi configurado com /configticketfarm.")
            return

        embed = discord.Embed(
            title="📦 PAINEL DE FARM — KORTE",
            description="Selecione seu cargo e registre sua entrega.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)

        await ctx.send(embed=embed, view=PainelView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))