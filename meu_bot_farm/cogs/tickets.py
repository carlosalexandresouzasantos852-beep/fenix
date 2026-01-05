import discord
import asyncio
import json
import os
from datetime import datetime
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, Modal, TextInput

# ================== CONFIG ==================
MAX_ADV = 5
PASTA = "meu_bot_farm/data"
os.makedirs(PASTA, exist_ok=True)

ENTREGAS_FILE = f"{PASTA}/entregas.json"
ADV_FILE = f"{PASTA}/advs.json"
CONFIG_FILE = f"{PASTA}/config_farm.json"

GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

# ================== JSON ==================
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ================== VIEW DE ANÁLISE ==================
class AnaliseView(View):
    def __init__(self, user, qtd, meta, canais):
        super().__init__(timeout=None)
        self.user = user
        self.qtd = qtd
        self.meta = meta
        self.canais = canais

    @discord.ui.button(label="✅ ACEITAR", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, _):
        entregas = load_json(ENTREGAS_FILE, {})
        advs = load_json(ADV_FILE, {})

        total = entregas.get(str(self.user.id), 0) + self.qtd
        entregas[str(self.user.id)] = total

        embed = interaction.message.embeds[0]
        embed.set_field_at(
            4,
            name="📊 Status da Meta",
            value="✅ Meta concluída" if total >= self.meta else f"🕒 Faltam {self.meta - total}",
            inline=False
        )

        canal = interaction.guild.get_channel(self.canais["aceitos"])
        if canal:
            await canal.send(embed=embed)

        save_json(ENTREGAS_FILE, entregas)
        save_json(ADV_FILE, advs)

        await interaction.message.delete()
        await interaction.response.send_message("Entrega aceita.", ephemeral=True)

    @discord.ui.button(label="❌ RECUSAR", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, _):
        embed = interaction.message.embeds[0]
        embed.set_field_at(4, name="📊 Status da Meta", value="❌ Entrega recusada", inline=False)

        canal = interaction.guild.get_channel(self.canais["recusados"])
        if canal:
            await canal.send(embed=embed)

        await interaction.message.delete()
        await interaction.response.send_message("Entrega recusada.", ephemeral=True)

# ================== MODAL ==================
class EntregaModal(Modal):
    def __init__(self, meta, canais):
        super().__init__(title="Entrega de Farm – KORTE")
        self.meta = meta
        self.canais = canais

        self.qtd = TextInput(label="Quantidade entregue", required=True)
        self.para = TextInput(label="Entregou para quem?", required=True)
        self.data = TextInput(label="Data (DD/MM)", required=True)

        self.add_item(self.qtd)
        self.add_item(self.para)
        self.add_item(self.data)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            qtd = int(self.qtd.value)
        except:
            return await interaction.followup.send("Quantidade inválida.", ephemeral=True)

        status = "✅ Meta concluída" if qtd >= self.meta else f"🕒 Faltam {self.meta - qtd}"

        embed = discord.Embed(
            title="📦 ENTREGA DE FARM – KORTE",
            color=discord.Color.orange()
        )
        embed.add_field(name="👤 Quem entregou", value=interaction.user.mention, inline=False)
        embed.add_field(name="📦 Quantidade", value=str(qtd), inline=False)
        embed.add_field(name="📍 Entregou para", value=self.para.value, inline=False)
        embed.add_field(name="📅 Data", value=self.data.value, inline=False)
        embed.add_field(name="📊 Status da Meta", value=status, inline=False)

        canal = interaction.guild.get_channel(self.canais["analise"])
        if canal:
            await canal.send(
                embed=embed,
                view=AnaliseView(interaction.user, qtd, self.meta, self.canais)
            )

        await interaction.followup.send("Entrega enviada para análise.", ephemeral=True)

# ================== PAINEL ==================
class PainelView(View):
    def __init__(self, meta, canais):
        super().__init__(timeout=None)
        self.meta = meta
        self.canais = canais

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(
            EntregaModal(self.meta, self.canais)
        )

# ================== COG ==================
class KorteFarm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticketfarm", description="Abrir painel de entrega de farm")
    async def ticketfarm(self, interaction: discord.Interaction):
        config = load_json(CONFIG_FILE, {})

        if not config:
            return await interaction.response.send_message(
                "❌ Sistema não configurado. Use `/configticketfarm`.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📦 ENTREGA DE FARM – KORTE",
            description="Clique no botão abaixo para entregar seu farming.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)

        canais = {
            "analise": config["categoria_analise"],
            "aceitos": config["canal_aceitos"],
            "recusados": config["canal_recusados"],
            "adv": config["canal_adv"]
        }

        await interaction.response.send_message(
            embed=embed,
            view=PainelView(config["metas"]["Membro"], canais)
        )

# ================== SETUP ==================
async def setup(bot):
    await bot.add_cog(KorteFarm(bot))