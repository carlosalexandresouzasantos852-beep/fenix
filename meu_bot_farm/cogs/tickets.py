import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import asyncio
import traceback

CONFIG = "meu_bot_farm/data/config_farm.json"

GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"


# =========================
# CONFIG
# =========================
def load_config():
    if not os.path.exists(CONFIG):
        return None
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# VIEW DE ANÁLISE
# =========================
class AnaliseView(discord.ui.View):
    def __init__(self, bot, dados):
        super().__init__(timeout=None)
        self.bot = bot
        self.dados = dados

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, _):
        try:
            config = load_config()
            canal = self.bot.get_channel(config["canal_aceitos"])

            embed = discord.Embed(
                title="📦 ENTREGA DE FARM — ACEITA",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )

            for k, v in self.dados.items():
                embed.add_field(name=k, value=v, inline=False)

            msg = await canal.send(embed=embed)

            # apaga após 24h
            await asyncio.sleep(86400)
            await msg.delete()

            await interaction.channel.delete()

        except Exception:
            traceback.print_exc()
            await interaction.response.send_message("❌ Erro ao aceitar.", ephemeral=True)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, _):
        try:
            config = load_config()
            canal = self.bot.get_channel(config["canal_recusados"])

            embed = discord.Embed(
                title="❌ ENTREGA DE FARM — RECUSADA",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )

            for k, v in self.dados.items():
                embed.add_field(name=k, value=v, inline=False)

            msg = await canal.send(embed=embed)

            # apaga após 10h
            await asyncio.sleep(36000)
            await msg.delete()

            await interaction.channel.delete()

        except Exception:
            traceback.print_exc()
            await interaction.response.send_message("❌ Erro ao recusar.", ephemeral=True)


# =========================
# MODAL
# =========================
class EntregaModal(discord.ui.Modal, title="📦 Entrega de Farm"):
    quantidade = discord.ui.TextInput(label="Quantidade entregue", required=True)
    entregue_para = discord.ui.TextInput(label="Entregou para quem?", required=True)

    def __init__(self, bot, cargo):
        super().__init__()
        self.bot = bot
        self.cargo = cargo

    async def on_submit(self, interaction: discord.Interaction):
        try:
            config = load_config()
            categoria = self.bot.get_channel(config["categoria_analise"])

            dados = {
                "🧍 Quem entregou": interaction.user.mention,
                "🎖 Cargo": self.cargo,
                "📦 Quantidade": self.quantidade.value,
                "📍 Entregou para": self.entregue_para.value,
                "📅 Data": datetime.now().strftime("%d/%m/%Y")
            }

            canal = await categoria.create_text_channel(
                name=f"entrega-{interaction.user.name}"
            )

            embed = discord.Embed(
                title="📦 NOVA ENTREGA — ANÁLISE",
                color=discord.Color.orange()
            )

            for k, v in dados.items():
                embed.add_field(name=k, value=v, inline=False)

            await canal.send(embed=embed, view=AnaliseView(self.bot, dados))
            await interaction.response.send_message("✅ Enviado para análise.", ephemeral=True)

        except Exception:
            traceback.print_exc()
            await interaction.response.send_message("❌ Erro ao enviar.", ephemeral=True)


# =========================
# PAINEL
# =========================
class PainelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.cargo = None

    @discord.ui.select(
        placeholder="Selecione seu cargo",
        options=[
            discord.SelectOption(label="✈️ Aviãozinho", value="Aviãozinho"),
            discord.SelectOption(label="👤 Membro", value="Membro"),
            discord.SelectOption(label="📣 Recrutador", value="Recrutador"),
            discord.SelectOption(label="🛡️ Gerente", value="Gerente"),
        ]
    )
    async def selecionar(self, interaction: discord.Interaction, select):
        self.cargo = select.values[0]
        await interaction.response.send_message(
            f"✅ Cargo selecionado: **{self.cargo}**",
            ephemeral=True
        )

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        if not self.cargo:
            return await interaction.response.send_message(
                "❌ Selecione um cargo primeiro.",
                ephemeral=True
            )
        await interaction.response.send_modal(EntregaModal(self.bot, self.cargo))


# =========================
# COG
# =========================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painelfarm")
    @commands.has_permissions(manage_guild=True)
    async def painel_farm(self, ctx):
        embed = discord.Embed(
            title="📦 PAINEL DE FARM — KORTE",
            description="Selecione seu cargo e registre sua entrega.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)

        await ctx.send(embed=embed, view=PainelView(self.bot))
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Tickets(bot))