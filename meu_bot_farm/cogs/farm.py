import discord
from discord.ext import commands
import json
import os
from datetime import datetime

CONFIG = "meu_bot_farm/data/config_farm.json"

# ================= JSON =================
def load_config():
    if not os.path.exists(CONFIG):
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump({"guilds": {}}, f, indent=4, ensure_ascii=False)

    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def garantir_guild(cfg, guild_id):
    gid = str(guild_id)
    cfg.setdefault("guilds", {})
    cfg["guilds"].setdefault(gid, {})
    g = cfg["guilds"][gid]

    g.setdefault("metas", {})
    g.setdefault("entregas_semana", {})

    return g


# ================= UTIL =================
def cargo_valido(member: discord.Member, metas: dict) -> str | None:
    for role in member.roles:
        if role.name.lower() in metas:
            return role.name.lower()
    return None


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

    async def on_submit(self, interaction: discord.Interaction):
        cfg = load_config()
        g = garantir_guild(cfg, interaction.guild.id)

        metas = g["metas"]
        cargo = cargo_valido(interaction.user, metas)

        if not cargo:
            await interaction.response.send_message(
                "❌ Você não possui **nenhum cargo válido** para entrega de farm.",
                ephemeral=True
            )
            return

        try:
            quantidade = int(self.quantidade.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ Quantidade inválida.",
                ephemeral=True
            )
            return

        uid = str(interaction.user.id)

        # 🔥 MARCA COMO ENTREGUE NA SEMANA
        g["entregas_semana"][uid] = {
            "cargo": cargo,
            "quantidade": quantidade,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        save_config(cfg)

        await interaction.response.send_message(
            f"✅ **Entrega registrada com sucesso!**\n\n"
            f"👤 Cargo: **{cargo.capitalize()}**\n"
            f"📦 Quantidade: **{quantidade}**\n"
            f"🎯 Meta: **{metas[cargo]}**",
            ephemeral=True
        )


# ================= VIEW =================
class PainelEntregaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(EntregaModal())


# ================= COG =================
class Farm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painelfarm")
    async def painel_farm(self, ctx):
        embed = discord.Embed(
            title="📦 PAINEL DE ENTREGA DE FARM",
            description="Clique no botão abaixo para registrar sua entrega.",
            color=discord.Color.green()
        )

        await ctx.send(embed=embed, view=PainelEntregaView())


# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Farm(bot))
    print("✅ Farm carregado — integrado ao ADV automático")