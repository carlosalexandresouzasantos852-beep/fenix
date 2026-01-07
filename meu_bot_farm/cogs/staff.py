import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands
from discord import app_commands
import json
import os

ADVS = "meu_bot_farm/data/advs.json"


# ================== JSON ==================

def load_advs():
    if not os.path.exists(ADVS):
        os.makedirs(os.path.dirname(ADVS), exist_ok=True)
        with open(ADVS, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)

    with open(ADVS, "r", encoding="utf-8") as f:
        return json.load(f)


def save_advs(data: dict):
    with open(ADVS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ================== HELPERS ==================

def add_adv(user_id: int, qtd: int = 1):
    advs = load_advs()
    uid = str(user_id)
    advs[uid] = advs.get(uid, 0) + qtd
    save_advs(advs)


def remove_adv(user_id: int, qtd: int = 1):
    advs = load_advs()
    uid = str(user_id)
    advs[uid] = max(0, advs.get(uid, 0) - qtd)
    save_advs(advs)


def get_adv(user_id: int) -> int:
    advs = load_advs()
    return advs.get(str(user_id), 0)


# ================== MODAIS ==================

class AddAdvModal(discord.ui.Modal, title="➕ Aplicar ADV"):
    membro = discord.ui.TextInput(label="ID do membro", required=True)
    quantidade = discord.ui.TextInput(label="Quantidade", required=False, placeholder="1")

    async def on_submit(self, interaction: discord.Interaction):
        qtd = int(self.quantidade.value) if self.quantidade.value else 1
        add_adv(int(self.membro.value), qtd)

        await interaction.response.send_message(
            f"✅ ADV aplicado.\n📛 Total atual: **{get_adv(int(self.membro.value))}**",
            ephemeral=True
        )


class RemoveAdvModal(discord.ui.Modal, title="➖ Remover ADV"):
    membro = discord.ui.TextInput(label="ID do membro", required=True)
    quantidade = discord.ui.TextInput(label="Quantidade", required=False, placeholder="1")

    async def on_submit(self, interaction: discord.Interaction):
        qtd = int(self.quantidade.value) if self.quantidade.value else 1
        remove_adv(int(self.membro.value), qtd)

        await interaction.response.send_message(
            f"🔁 ADV removido.\n📛 Total atual: **{get_adv(int(self.membro.value))}**",
            ephemeral=True
        )


class VerAdvModal(discord.ui.Modal, title="👀 Ver ADV"):
    membro = discord.ui.TextInput(label="ID do membro", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        total = get_adv(int(self.membro.value))

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


# ================== COG ==================

class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- SLASH ----------

    @app_commands.command(name="veradv", description="Ver ADV de um membro")
    async def veradv(self, interaction: discord.Interaction, membro: discord.Member):
        await interaction.response.send_message(
            f"⚠️ {membro.mention} possui **{get_adv(membro.id)} ADV**",
            ephemeral=True
        )

    @app_commands.command(name="addadv", description="Aplicar ADV manual")
    async def addadv(self, interaction: discord.Interaction, membro: discord.Member, quantidade: int = 1):
        add_adv(membro.id, quantidade)
        await interaction.response.send_message("✅ ADV aplicado com sucesso.", ephemeral=True)

    @app_commands.command(name="removeadv", description="Remover ADV manual")
    async def removeadv(self, interaction: discord.Interaction, membro: discord.Member, quantidade: int = 1):
        remove_adv(membro.id, quantidade)
        await interaction.response.send_message("🔁 ADV removido com sucesso.", ephemeral=True)

    # ---------- PAINEL ----------

    @commands.command(name="painelstaff")
    @commands.has_permissions(manage_guild=True)
    async def painel_staff(self, ctx):
        embed = discord.Embed(
            title="🛡 PAINEL STAFF — FARM & ADV",
            description="Gerencie advertências e punições do sistema de farm.",
            color=discord.Color.red()
        )

        await ctx.send(embed=embed, view=PainelStaffView())
        await ctx.message.delete()


# ================== SETUP ==================

async def setup(bot):
    await bot.add_cog(Staff(bot))