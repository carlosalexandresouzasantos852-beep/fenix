# meu_bot_farm/cogs/tickets.py
import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import traceback
import asyncio

# =========================
# CONFIGURAÇÃO
# =========================
CONFIG_PATH = "meu_bot_farm/data/config_farm.json"

def garantir_config():
    default = {
        "canal_aceitos": 0,
        "canal_recusados": 0,
        "categoria_analise": 0,
        "canal_logs_adv": 0,
        "canal_logs_pd": 0,
        "metas": {
            "aviãozinho": 10,
            "membro": 20,
            "recrutador": 30,
            "gerente": 40
        }
    }
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)
        return default
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# =========================
# GIF PAINEL
# =========================
GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

# =========================
# FUNÇÕES DE META
# =========================
def cargo_do_usuario(member: discord.Member) -> str | None:
    cargos = [r.name.lower() for r in member.roles]
    for c in ["aviãozinho", "membro", "recrutador", "gerente"]:
        if c in cargos:
            return c
    return None

def meta_por_usuario(member: discord.Member) -> int | None:
    config = garantir_config()
    cargo = cargo_do_usuario(member)
    if not cargo:
        return None
    return config.get("metas", {}).get(cargo)

# =========================
# MODAL DE ENTREGA
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
            config = garantir_config()
            categoria = self.bot.get_channel(config["categoria_analise"])
            if not categoria:
                return await interaction.response.send_message("❌ Categoria de análise não configurada.", ephemeral=True)

            dados = {
                "🧍 Quem entregou": interaction.user.mention,
                "🎖 Cargo": self.cargo,
                "📦 Quantidade": self.quantidade.value,
                "📍 Entregou para": self.entregue_para.value,
                "📅 Data": datetime.now().strftime("%d/%m/%Y")
            }

            canal = await categoria.create_text_channel(name=f"📦-entrega-{interaction.user.name}")

            embed = discord.Embed(title="📦 NOVA ENTREGA — ANÁLISE", color=discord.Color.orange())
            for k, v in dados.items():
                embed.add_field(name=k, value=v, inline=False)

            await canal.send(embed=embed, view=AnaliseView(self.bot, dados))
            await interaction.response.send_message("✅ Entrega enviada para análise.", ephemeral=True)
        except Exception:
            traceback.print_exc()

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
            config = garantir_config()
            canal = self.bot.get_channel(config["canal_aceitos"])
            if not canal:
                return await interaction.response.send_message("❌ Canal de aceitos não configurado.", ephemeral=True)

            embed = discord.Embed(title="📦 ENTREGA DE FARM — ACEITA", color=discord.Color.green(), timestamp=datetime.now())
            for k, v in self.dados.items():
                embed.add_field(name=k, value=v, inline=False)

            await canal.send(embed=embed)
            await interaction.channel.delete()
        except Exception:
            traceback.print_exc()

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, _):
        try:
            config = garantir_config()
            canal = self.bot.get_channel(config["canal_recusados"])
            if not canal:
                return await interaction.response.send_message("❌ Canal de recusados não configurado.", ephemeral=True)

            embed = discord.Embed(title="❌ ENTREGA DE FARM — RECUSADA", color=discord.Color.red(), timestamp=datetime.now())
            for k, v in self.dados.items():
                embed.add_field(name=k, value=v, inline=False)

            await canal.send(embed=embed)
            await interaction.channel.delete()
        except Exception:
            traceback.print_exc()

# =========================
# VIEW DO PAINEL DE MEMBROS
# =========================
class PainelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.cargo = None

    @discord.ui.select(
        placeholder="Selecione seu cargo para iniciar seu farm",
        options=[
            discord.SelectOption(label="✈️ Aviãozinho"),
            discord.SelectOption(label="👤 Membro"),
            discord.SelectOption(label="📣 Recrutador"),
            discord.SelectOption(label="🛡️ Gerente"),
        ]
    )
    async def selecionar(self, interaction: discord.Interaction, select):
        self.cargo = select.values[0]
        await interaction.response.send_message(f"✅ Cargo selecionado: **{self.cargo}**", ephemeral=True)

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        if not self.cargo:
            return await interaction.response.send_message("❌ Selecione um cargo primeiro.", ephemeral=True)
        await interaction.response.send_modal(EntregaModal(self.bot, self.cargo))
        # Resetar seleção para próxima entrega
        self.cargo = None

# =========================
# COG PRINCIPAL
# =========================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # Painel de membros
    # -------------------------
    @commands.command(name="painelfarm")
    async def painelfarm(self, ctx: commands.Context):
        embed = discord.Embed(
            title="📦 PAINEL DE FARM",
            description="Selecione seu cargo e registre a entrega.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)
        view = PainelView(self.bot)
        await ctx.send(embed=embed, view=view)

    # -------------------------
    # Painel Staff
    # -------------------------
    @commands.command(name="painelstaff")
    async def painel_staff(self, ctx: commands.Context):
        embed = discord.Embed(
            title="📋 PAINEL STAFF",
            description="Use os botões abaixo para gerenciar farm e ADV",
            color=discord.Color.blue()
        )
        view = PainelStaffView(self.bot)
        await ctx.send(embed=embed, view=view)

    # -------------------------
    # Configuração do Ticket
    # -------------------------
    @app_commands.command(name="config-ticket-farm", description="Configurar ticket de farm")
    async def config_ticket_farm(self, interaction: discord.Interaction):
        config = garantir_config()

        class ConfigModal(discord.ui.Modal, title="Configuração Ticket Farm"):
            canal_aceitos = discord.ui.TextInput(label="ID do Canal de Aceitos", default=str(config.get("canal_aceitos", 0)))
            canal_recusados = discord.ui.TextInput(label="ID do Canal de Recusados", default=str(config.get("canal_recusados", 0)))
            categoria_analise = discord.ui.TextInput(label="ID da Categoria de Análise", default=str(config.get("categoria_analise", 0)))
            canal_logs_adv = discord.ui.TextInput(label="ID do Canal de Logs ADV", default=str(config.get("canal_logs_adv", 0)))
            canal_logs_pd = discord.ui.TextInput(label="ID do Canal de Logs PD", default=str(config.get("canal_logs_pd", 0)))

            async def on_submit(self_modal, interaction_modal: discord.Interaction):
                config["canal_aceitos"] = int(self_modal.canal_aceitos.value)
                config["canal_recusados"] = int(self_modal.canal_recusados.value)
                config["categoria_analise"] = int(self_modal.categoria_analise.value)
                config["canal_logs_adv"] = int(self_modal.canal_logs_adv.value)
                config["canal_logs_pd"] = int(self_modal.canal_logs_pd.value)
                salvar_config(config)
                await interaction_modal.response.send_message("✅ Configuração salva com sucesso!", ephemeral=True)

        await interaction.response.send_modal(ConfigModal())

# =========================
# SETUP
# =========================
async def setup(bot):
    await bot.add_cog(Tickets(bot))