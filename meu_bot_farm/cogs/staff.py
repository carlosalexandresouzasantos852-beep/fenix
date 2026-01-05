import discord
from discord.ext import commands
from discord import app_commands
import json
import os

ADVS = "meu_bot_farm/data/advs.json"


# ================== JSON ==================

def load_advs():
    if not os.path.exists(ADVS):
        os.makedirs("meu_bot_farm/data", exist_ok=True)
        with open(ADVS, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(ADVS, "r", encoding="utf-8") as f:
        return json.load(f)


def save_advs(data):
    with open(ADVS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ================== MODAIS ==================

class AddAdvModal(discord.ui.Modal, title="➕ Aplicar ADV"):
    membro = discord.ui.TextInput(label="ID do membro", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        advs = load_advs()
        uid = self.membro.value

        advs[uid] = advs.get(uid, 0) + 1
        save_advs(advs)

        await interaction.response.send_message(
            f"✅ ADV aplicado.\n📛 Total atual: **{advs[uid]}**",
            ephemeral=True
        )


class RemoveAdvModal(discord.ui.Modal, title="➖ Remover ADV"):
    membro = discord.ui.TextInput(label="ID do membro", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        advs = load_advs()
        uid = self.membro.value

        advs[uid] = max(0, advs.get(uid, 0) - 1)
        save_advs(advs)

        await interaction.response.send_message(
            f"🔁 ADV removido.\n📛 Total atual: **{advs[uid]}**",
            ephemeral=True
        )


class VerAdvModal(discord.ui.Modal, title="👀 Ver ADV"):
    membro = discord.ui.TextInput(label="ID do membro", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        advs = load_advs()
        total = advs.get(self.membro.value, 0)

        await interaction.response.send_message(
            f"⚠️ Total de ADV: **{total}**",
            ephemeral=True
        )


# ================== VIEW ==================

class PainelStaffView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="➕ ADD ADV", style=discord.ButtonStyle.danger)
    async def add_adv(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(AddAdvModal())

    @discord.ui.button(label="➖ REMOVER ADV", style=discord.ButtonStyle.secondary)
    async def remove_adv(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(RemoveAdvModal())

    @discord.ui.button(label="👀 VER ADV", style=discord.ButtonStyle.primary)
    async def ver_adv(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(VerAdvModal())


# ================== COG STAFF ==================

class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- SLASH COMMANDS ----------

    @app_commands.command(name="veradv", description="Ver ADV de um membro")
    async def veradv(self, interaction: discord.Interaction, membro: discord.Member):
        advs = load_advs()
        await interaction.response.send_message(
            f"⚠️ {membro.mention} possui **{advs.get(str(membro.id), 0)} ADV**",
            ephemeral=True
        )

    @app_commands.command(name="addadv", description="Aplicar ADV manual")
    async def addadv(self, interaction: discord.Interaction, membro: discord.Member):
        advs = load_advs()
        advs[str(membro.id)] = advs.get(str(membro.id), 0) + 1
        save_advs(advs)

        await interaction.response.send_message(
            "✅ ADV aplicado com sucesso.",
            ephemeral=True
        )

    @app_commands.command(name="removeadv", description="Remover ADV manual")
    async def removeadv(self, interaction: discord.Interaction, membro: discord.Member):
        advs = load_advs()
        advs[str(membro.id)] = max(0, advs.get(str(membro.id), 0) - 1)
        save_advs(advs)

        await interaction.response.send_message(
            "🔁 ADV removido com sucesso.",
            ephemeral=True
        )

    # ---------- PAINEL PREFIXO ----------

    @commands.command(name="painelstaff")
    @commands.has_permissions(manage_guild=True)
    async def painel_staff(self, ctx):
        embed = discord.Embed(
            title="🛡 PAINEL STAFF — FARM & ADV",
            description="Gerencie advertências usando os botões abaixo.",
            color=discord.Color.red()
        )

        await ctx.send(embed=embed, view=PainelStaffView())
        await ctx.message.delete()


# ================== SETUP ==================

async def setup(bot):
    await bot.add_cog(Staff(bot))