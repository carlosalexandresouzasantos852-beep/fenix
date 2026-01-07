import discord
from discord.ext import commands
import json
import os

CONFIG = "meu_bot_farm/data/config_farm.json"
ENTREGAS = "meu_bot_farm/data/entregas.json"


# ================= JSON =================
def load(path, default):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


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

    def __init__(self, cargo: str):
        super().__init__()
        self.cargo = cargo.lower()  # 🔥 normalizado

    async def on_submit(self, interaction: discord.Interaction):
        config = load(CONFIG, {})
        entregas = load(ENTREGAS, {})

        metas = config.get("metas", {})
        meta = metas.get(self.cargo)

        if meta is None:
            await interaction.response.send_message(
                "❌ A meta para esse cargo **não foi configurada**.",
                ephemeral=True
            )
            return

        uid = str(interaction.user.id)
        entregas.setdefault(uid, 0)
        entregas[uid] += int(self.quantidade.value)

        save(ENTREGAS, entregas)

        await interaction.response.send_message(
            f"✅ **Entrega registrada com sucesso!**\n\n"
            f"👤 Cargo: **{self.cargo.capitalize()}**\n"
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
            discord.SelectOption(label="Aviãozinho", value="aviãozinho"),
            discord.SelectOption(label="Membro", value="membro"),
            discord.SelectOption(label="Recrutador", value="recrutador"),
            discord.SelectOption(label="Gerente", value="gerente"),
        ]
    )
    async def selecionar_cargo(self, interaction: discord.Interaction, select):
        self.cargo = select.values[0]  # já vem lowercase
        await interaction.response.send_message(
            f"✅ Cargo selecionado: **{self.cargo.capitalize()}**",
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

    @commands.command(name="painelfarm")
    async def painel_farm(self, ctx):
        await ctx.send(
            "📦 **Painel de Entrega de Farm**",
            view=PainelEntregaView()
        )


async def setup(bot):
    await bot.add_cog(Farm(bot))