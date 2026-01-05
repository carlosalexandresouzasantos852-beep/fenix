import discord
from discord.ext import commands
import json
import os

CONFIG = "meu_bot_farm/data/config_farm.json"
ENTREGAS = "meu_bot_farm/data/entregas.json"


def load(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ================= MODAL =================
class EntregaModal(discord.ui.Modal, title="📦 Entrega de Farm"):
    quantidade = discord.ui.TextInput(
        label="Quantidade entregue",
        placeholder="Ex: 150",
        required=True
    )

    entregue_para = discord.ui.TextInput(
        label="Entregou para quem?",
        placeholder="Nome ou ID",
        required=True
    )

    def __init__(self, cargo):
        super().__init__()
        self.cargo = cargo

    async def on_submit(self, interaction: discord.Interaction):
        config = load(CONFIG, {})
        entregas = load(ENTREGAS, {})

        metas = config.get("metas", {})
        meta = metas.get(self.cargo)

        if not meta:
            await interaction.response.send_message(
                "❌ Não existe meta configurada para esse cargo.",
                ephemeral=True
            )
            return

        uid = str(interaction.user.id)
        entregas.setdefault(uid, 0)
        entregas[uid] += int(self.quantidade.value)

        save(ENTREGAS, entregas)

        await interaction.response.send_message(
            f"✅ **Entrega registrada**\n"
            f"👤 Cargo: **{self.cargo}**\n"
            f"📦 Quantidade: **{self.quantidade.value}**\n"
            f"🎯 Meta: **{meta}**",
            ephemeral=True
        )


# ================= VIEW =================
class PainelEntregaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cargo = None

    @discord.ui.select(
        placeholder="Selecione seu cargo",
        options=[
            discord.SelectOption(label="Aviãozinho"),
            discord.SelectOption(label="Membro"),
            discord.SelectOption(label="Recrutador"),
            discord.SelectOption(label="Gerente"),
        ]
    )
    async def selecionar_cargo(self, interaction: discord.Interaction, select):
        self.cargo = select.values[0]
        await interaction.response.send_message(
            f"✅ Cargo selecionado: **{self.cargo}**",
            ephemeral=True
        )

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        if not self.cargo:
            await interaction.response.send_message(
                "❌ Selecione seu cargo antes de entregar.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(EntregaModal(self.cargo))


# ================= COG =================
class Farm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send("🏓 Pong funcionando")

async def setup(bot):
    await bot.add_cog(Farm(bot))