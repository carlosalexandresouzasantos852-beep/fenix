import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
import asyncio
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands
import json, os

CONFIG_PATH = "meu_bot_farm/data/config_farm.json"

# ================= UTIL =================
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    os.makedirs("meu_bot_farm/data", exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ================= MODAL =================
class EnvioFarmModal(Modal):
    def __init__(self, bot, cargo_nome, painel_view):
        super().__init__(title="📦 Envio de Farm-KORTE")
        self.bot = bot
        self.cargo_nome = cargo_nome
        self.painel_view = painel_view

        self.quantidade = TextInput(
            label="Quantidade entregue",
            placeholder="Ex: 1500",
            required=True
        )
        self.para_quem = TextInput(
            label="Para quem você entregou?",
            placeholder="Nome ou ID",
            required=True
        )

        self.add_item(self.quantidade)
        self.add_item(self.para_quem)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        metas = config.get("metas", {})

        quantidade = int(self.quantidade.value)
        meta = metas[self.cargo_nome]

        if quantidade >= meta:
            status = "✅ Meta concluída"
            if quantidade > meta:
                status += f" (+{quantidade - meta})"
        else:
            status = f"❌ Faltam {meta - quantidade}"

        categoria = interaction.guild.get_channel(config["categoria_analise"])

        canal = await interaction.guild.create_text_channel(
            name=f"farm-{interaction.user.name}",
            category=categoria
        )

        embed = discord.Embed(
            title="📦 Ticket de Farm-KORTE",
            color=0xf1c40f
        )
        embed.add_field(name="👤 Nome", value=interaction.user.mention, inline=False)
        embed.add_field(name="🎖️ Cargo", value=self.cargo_nome, inline=True)
        embed.add_field(name="📦 Quantidade", value=str(quantidade), inline=True)
        embed.add_field(name="🎯 Meta", value=str(meta), inline=True)
        embed.add_field(name="📊 Status", value=status, inline=False)
        embed.add_field(name="📍 Quem Recebeu", value=self.para_quem.value, inline=False)

        await canal.send(
            embed=embed,
            view=AnaliseView(self.bot, embed)
        )

        # Volta o painel para selecionar cargo
        self.painel_view.reset_select()

        await interaction.response.send_message(
            "📨 Seu ticket foi enviado para análise da **staff-KORTE**.",
            ephemeral=True,
            delete_after=3
        )

# ================= VIEW ANALISE =================
class AnaliseView(View):
    def __init__(self, bot, embed):
        super().__init__(timeout=None)
        self.bot = bot
        self.embed = embed
        self.finalizado = False

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.green, custom_id="btn_aceitar")
    async def aceitar(self, interaction: discord.Interaction, button: Button):
        if self.finalizado:
            return
        self.finalizado = True

        config = load_config()
        canal_aceitos = interaction.guild.get_channel(config["canal_aceitos"])

        await canal_aceitos.send(embed=self.embed)
        await interaction.channel.delete()
        await interaction.response.send_message("Ticket aceito!", ephemeral=True)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.red, custom_id="btn_recusar")
    async def recusar(self, interaction: discord.Interaction, button: Button):
        if self.finalizado:
            return
        self.finalizado = True

        config = load_config()
        canal_recusados = interaction.guild.get_channel(config["canal_recusados"])

        await canal_recusados.send(embed=self.embed)
        await interaction.channel.delete()
        await interaction.response.send_message("Ticket recusado!", ephemeral=True)

# ================= SELECT =================
class CargoSelect(Select):
    def __init__(self, bot):
        config = load_config()
        metas = config.get("metas", {})

        options = [discord.SelectOption(label=cargo) for cargo in metas.keys()]
        super().__init__(
            placeholder="Selecione seu cargo",
            options=options,
            custom_id="select_cargo"
        )
        self.bot = bot
        self.valor_selecionado = None

    async def callback(self, interaction: discord.Interaction):
        self.valor_selecionado = self.values[0]
        await interaction.response.send_message(
            f"✅ Cargo **{self.valor_selecionado}** selecionado. Clique em **Iniciar Farm** para enviar.",
            ephemeral=True,
            delete_after=3
        )

# ================= BOTÃO INICIAR FARM =================
class IniciarFarmButton(Button):
    def __init__(self, bot, select_cargo):
        super().__init__(label="Iniciar Farm-KORTE", style=discord.ButtonStyle.blurple, custom_id="btn_iniciar_farm")
        self.bot = bot
        self.select_cargo = select_cargo

    async def callback(self, interaction: discord.Interaction):
        if not self.select_cargo.valor_selecionado:
            await interaction.response.send_message(
                "❌ Selecione um cargo antes de iniciar a farm.",  
                ephemeral=True,
                delete_after=3
            )
            return
        await interaction.response.send_modal(EnvioFarmModal(self.bot, self.select_cargo.valor_selecionado, self.view))

# ================= PAINEL =================
class PainelFarmView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.select_cargo = CargoSelect(bot)
        self.add_item(self.select_cargo)
        self.add_item(IniciarFarmButton(bot, self.select_cargo))

    def reset_select(self):
        # Remove e recria o select para resetar visualmente
        self.remove_item(self.select_cargo)
        self.select_cargo = CargoSelect(self.bot)
        self.add_item(self.select_cargo)

# ================= COG TICKETS =================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(PainelFarmView(bot))

    @commands.command(name="painelfarm")
    async def painel(self, ctx):
        embed = discord.Embed(
            title="📦 Painel Entrega de Farm-KORTE",
            description="Selecione seu cargo e envie sua meta de farm.",
            color=0x2ecc71
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"
        )
        embed.set_footer(text="Sistema de Farm • Automático")

        await ctx.send(embed=embed, view=PainelFarmView(self.bot))

# ================= GERENCIADOR DE CARGOS =================
class CargoManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addcargo", description="Adicionar cargo e meta")
    @app_commands.checks.has_permissions(administrator=True)
    async def addcargo(self, interaction: discord.Interaction, nome: str, meta: int):
        config = load_config()
        metas = config.get("metas", {})

        if nome in metas:
            await interaction.response.send_message("❌ Cargo já existe.", ephemeral=True)
            return

        metas[nome] = meta
        config["metas"] = metas
        save_config(config)

        await interaction.response.send_message(
            f"✅ Cargo **{nome}** adicionado com meta **{meta}**.", ephemeral=True
        )

    @app_commands.command(name="removecargo", description="Remover cargo")
    @app_commands.checks.has_permissions(administrator=True)
    async def removecargo(self, interaction: discord.Interaction, nome: str):
        config = load_config()
        metas = config.get("metas", {})

        if nome not in metas:
            await interaction.response.send_message("❌ Cargo não existe.", ephemeral=True)
            return

        del metas[nome]
        config["metas"] = metas
        save_config(config)

        await interaction.response.send_message(
            f"🗑️ Cargo **{nome}** removido.", ephemeral=True
        )

# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
    await bot.add_cog(CargoManager(bot))