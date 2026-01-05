import discord
from discord.ext import commands
import json
import os
from datetime import datetime

CONFIG = "meu_bot_farm/data/config_farm.json"

def load_config():
    if not os.path.exists(CONFIG):
        return None
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

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
        config = load_config()

        qtd = self.dados["quantidade"]
        meta = self.dados["meta"]
        faltam = meta - qtd

        if faltam <= 0:
            status_meta = "✅ Meta concluída"
        else:
            status_meta = f"⏳ Faltam {faltam} para a meta"

        embed = discord.Embed(
            title="📦 ENTREGA DE FARM – KORTE",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )

        embed.add_field(name="🧍 Quem entregou", value=self.dados["quem"], inline=False)
        embed.add_field(name="📦 Quantidade", value=str(qtd), inline=False)
        embed.add_field(name="📍 Entregou para", value=self.dados["para"], inline=False)
        embed.add_field(name="📅 Data", value=self.dados["data"], inline=False)
        embed.add_field(name="📊 Status da Meta", value=status_meta, inline=False)

        canal_aceitos = self.bot.get_channel(config["canal_aceitos"])
        await canal_aceitos.send(embed=embed)

        await interaction.channel.delete()

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, _):
        config = load_config()

        embed = discord.Embed(
            title="❌ ENTREGA RECUSADA",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )

        embed.add_field(name="🧍 Quem entregou", value=self.dados["quem"], inline=False)
        embed.add_field(name="📦 Quantidade", value=str(self.dados["quantidade"]), inline=False)
        embed.add_field(name="📍 Entregou para", value=self.dados["para"], inline=False)
        embed.add_field(name="📅 Data", value=self.dados["data"], inline=False)
        embed.add_field(name="📊 Status", value="❌ Entrega recusada", inline=False)

        canal_recusados = self.bot.get_channel(config["canal_recusados"])
        await canal_recusados.send(embed=embed)

        await interaction.channel.delete()

# =========================
# MODAL DE ENTREGA
# =========================
class EntregaModal(discord.ui.Modal, title="📦 Entrega de Farm"):
    quantidade = discord.ui.TextInput(label="Quantidade entregue", required=True)
    entregue_para = discord.ui.TextInput(label="Entregue para quem?", required=True)

    def __init__(self, bot, cargo):
        super().__init__()
        self.bot = bot
        self.cargo = cargo

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()

        quantidade = int(self.quantidade.value)
        meta = config["metas_por_cargo"][self.cargo]

        dados = {
            "quem": interaction.user.mention,
            "quantidade": quantidade,
            "meta": meta,
            "para": self.entregue_para.value,
            "data": datetime.now().strftime("%d/%m/%Y")
        }

        categoria = self.bot.get_channel(config["categoria_analise"])
        canal = await categoria.create_text_channel(
            name=f"📦-entrega-{interaction.user.name}"
        )

        embed = discord.Embed(
            title="📦 NOVA ENTREGA DE FARM – ANÁLISE",
            color=discord.Color.orange()
        )

        embed.add_field(name="🧍 Quem entregou", value=dados["quem"], inline=False)
        embed.add_field(name="🎖 Cargo", value=self.cargo, inline=False)
        embed.add_field(name="📦 Quantidade entregue", value=str(quantidade), inline=False)
        embed.add_field(name="🎯 Meta do cargo", value=str(meta), inline=False)
        embed.add_field(name="📍 Entregou para", value=dados["para"], inline=False)
        embed.add_field(name="📅 Data", value=dados["data"], inline=False)
        embed.add_field(name="🔎 Status", value="⏳ Aguardando decisão da staff", inline=False)

        await canal.send(embed=embed, view=AnaliseView(self.bot, dados))

        await interaction.response.send_message(
            "✅ Sua entrega foi enviada para análise.",
            ephemeral=True
        )

# =========================
# VIEW DO PAINEL
# =========================
class PainelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
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
            EntregaModal(self.bot, self.cargo_selecionado)
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