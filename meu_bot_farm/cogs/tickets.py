import os
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
import traceback

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

            embed = discord.Embed(
                title="📦 ENTREGA DE FARM — ACEITA",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            for k, v in self.dados.items():
                embed.add_field(name=k, value=v, inline=False)

            msg = await canal.send(embed=embed)
            await asyncio.sleep(24*3600)
            await msg.delete()
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

            embed = discord.Embed(
                title="❌ ENTREGA DE FARM — RECUSADA",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            for k, v in self.dados.items():
                embed.add_field(name=k, value=v, inline=False)

            msg = await canal.send(embed=embed)
            await asyncio.sleep(10*3600)
            await msg.delete()
            await interaction.channel.delete()
        except Exception:
            traceback.print_exc()

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
            msg = await interaction.response.send_message("✅ Entrega enviada para análise.", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
        except Exception:
            traceback.print_exc()

# =========================
# PAINEL DE MEMBROS
# =========================
class PainelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.cargo = None

    @discord.ui.select(
        placeholder="Selecione seu cargo",
        options=[
            discord.SelectOption(label="✈️ Aviãozinho", value="aviãozinho"),
            discord.SelectOption(label="👤 Membro", value="membro"),
            discord.SelectOption(label="📣 Recrutador", value="recrutador"),
            discord.SelectOption(label="🛡️ Gerente", value="gerente"),
        ]
    )
    async def selecionar(self, interaction: discord.Interaction, select):
        self.cargo = select.values[0]
        msg = await interaction.response.send_message(f"✅ Cargo selecionado: **{self.cargo}**", ephemeral=True)
        await asyncio.sleep(5)
        await msg.delete()

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        if not self.cargo:
            return await interaction.response.send_message("❌ Selecione um cargo primeiro.", ephemeral=True)
        await interaction.response.send_modal(EntregaModal(self.bot, self.cargo))
        self.cargo = None

# =========================
# PAINEL STAFF
# =========================
class PainelStaffView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Ver ADV", style=discord.ButtonStyle.blurple)
    async def ver_adv(self, interaction: discord.Interaction, _):
        await interaction.response.send_message("📋 Lista de ADV (implementação necessária)", ephemeral=True)

    @discord.ui.button(label="Aplicar ADV", style=discord.ButtonStyle.red)
    async def aplicar_adv(self, interaction: discord.Interaction, _):
        await interaction.response.send_message("Modal de aplicar ADV (implementação necessária)", ephemeral=True)

    @discord.ui.button(label="Remover ADV", style=discord.ButtonStyle.grey)
    async def remover_adv(self, interaction: discord.Interaction, _):
        await interaction.response.send_message("Modal de remover ADV (implementação necessária)", ephemeral=True)

    @discord.ui.button(label="Visualizar Entregas", style=discord.ButtonStyle.green)
    async def visualizar_entregas(self, interaction: discord.Interaction, _):
        await interaction.response.send_message("📦 Visualizar entregas (implementação necessária)", ephemeral=True)

# =========================
# COG PRINCIPAL
# =========================
class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot = bot
        self.adv_aplicados = {}  # Armazena ADV aplicados
        self.loop_adv.start()  # inicia loop semanal

    # -------------------------
    # Painel Farm (prefixo)
    # -------------------------
    @commands.command(name="painelfarm")
    async def painel_farm_cmd(self, ctx):
        embed = discord.Embed(
            title="📦 PAINEL DE FARM",
            description="Selecione seu cargo e registre a entrega.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=PainelView(self.bot))

    # -------------------------
    # Painel Staff (prefixo)
    # -------------------------
    @commands.command(name="painelstaff")
    async def painel_staff_cmd(self, ctx):
        embed = discord.Embed(
            title="📋 PAINEL STAFF",
            description="Use os botões abaixo para gerenciar farm e ADV",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=PainelStaffView(self.bot))

    # -------------------------
    # Config Ticket Farm (slash)
    # -------------------------
    @app_commands.command(name="configticketfarm", description="Configuração completa do Ticket Farm")
    @app_commands.describe(
        meta_aviao="Meta de Aviãozinho",
        meta_membro="Meta de Membro",
        meta_recrutador="Meta de Recrutador",
        meta_gerente="Meta de Gerente",
        categoria_analise="Categoria de análise",
        canal_aceitos="Canal de aceitos",
        canal_recusados="Canal de recusados",
        canal_adv="Canal de ADV"
    )
    async def config_ticket_farm(
        self,
        interaction: discord.Interaction,
        meta_aviao: int,
        meta_membro: int,
        meta_recrutador: int,
        meta_gerente: int,
        categoria_analise: discord.TextChannel,
        canal_aceitos: discord.TextChannel,
        canal_recusados: discord.TextChannel,
        canal_adv: discord.TextChannel
    ):
        config = garantir_config()
        config["metas"]["aviãozinho"] = meta_aviao
        config["metas"]["membro"] = meta_membro
        config["metas"]["recrutador"] = meta_recrutador
        config["metas"]["gerente"] = meta_gerente
        config["categoria_analise"] = categoria_analise.id
        config["canal_aceitos"] = canal_aceitos.id
        config["canal_recusados"] = canal_recusados.id
        config["canal_logs_adv"] = canal_adv.id
        salvar_config(config)
        await interaction.response.send_message("✅ Configuração de Ticket Farm salva com sucesso!", ephemeral=True)

    # -------------------------
    # LOOP AUTOMÁTICO DE ADV SEMANAL
    # -------------------------
    @tasks.loop(hours=24)
    async def loop_adv(self):
        now = datetime.utcnow()
        if now.weekday() == 0:  # Segunda-feira
            self.adv_aplicados.clear()  # reset lista ADV semanal

# =========================
# SETUP
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()
    print("Tickets cog carregado e comandos globais sincronizados!")