# meu_bot_farm/cogs/painel_staff.py
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from meu_bot_farm.cogs.config_farm import garantir_config

class PainelStaff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = garantir_config()
        self.metas = self.config.get("metas", {})
        self.canal_aceitos = None
        self.canal_recusados = None
        self.canal_pd = None
        self.adv_cog = None

    async def cog_load(self):
        self.adv_cog = self.bot.get_cog("ADV")
        self.canal_aceitos = self.bot.get_channel(self.config.get("canal_aceitos"))
        self.canal_recusados = self.bot.get_channel(self.config.get("canal_recusados"))
        self.canal_pd = self.bot.get_channel(self.config.get("canal_pd"))

    # =======================
    # Comando de Painel Staff
    # =======================
    @commands.command(name="painelstaff")
    async def painel_staff(self, ctx):
        embed = discord.Embed(
            title="📋 Painel Staff",
            description="Use os botões abaixo para gerenciar farm e ADV",
            color=discord.Color.blue()
        )
        view = PainelStaffView(self, ctx.guild)
        await ctx.send(embed=embed, view=view)

    # =======================
    # Funções de Farm/ADV/PD
    # =======================
    async def aceitar_farm(self, membro: discord.Member, cargo: str, quantidade: int):
        meta = self.metas.get(cargo, 0)
        status_meta = "✅ Meta concluída" if quantidade >= meta else f"❌ Faltam {meta - quantidade}"
        embed = discord.Embed(
            title="Entrega de Farm Concluída",
            description=f"**Membro:** {membro.display_name}\n**Cargo:** {cargo}\n**Quantidade:** {quantidade}\n**Status:** {status_meta}",
            color=discord.Color.green()
        )
        msg = await self.canal_aceitos.send(embed=embed)
        await asyncio.sleep(24*3600)
        await msg.delete()

    async def recusar_farm(self, membro: discord.Member, cargo: str, quantidade: int):
        embed = discord.Embed(
            title="Entrega de Farm Recusada",
            description=f"**Membro:** {membro.display_name}\n**Cargo:** {cargo}\n**Quantidade:** {quantidade}",
            color=discord.Color.red()
        )
        msg = await self.canal_recusados.send(embed=embed)
        await asyncio.sleep(10*3600)
        await msg.delete()

    async def aplicar_adv_manual(self, apelido: str, qtd: int = 1):
        self.adv_cog.aplicar_adv_botao(apelido, qtd)

    async def remover_adv_manual(self, apelido: str):
        self.adv_cog.remover_adv_botao(apelido)

    async def ver_vadv(self):
        return self.adv_cog.listar_adv()

    async def aplicar_pd(self, membro: discord.Member):
        apelido = membro.display_name
        adv = self.adv_cog.adv_ativos.get(apelido, 0)
        if adv >= 5:
            await membro.kick(reason="PD automático - 5 ADV")
            if self.canal_pd:
                await self.canal_pd.send(f"⚠️ PD aplicado a {apelido} por acumular 5 ADV.")

# ===================================
# View Botões Painel Staff
# ===================================
class PainelStaffView(discord.ui.View):
    def __init__(self, cog: PainelStaff, guild: discord.Guild):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild = guild

    @discord.ui.button(label="Entrega Farm", style=discord.ButtonStyle.green)
    async def entrega_farm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Modal de entrega farm (implementação do modal necessária)", ephemeral=True)

    @discord.ui.button(label="Aplicar ADV Manual", style=discord.ButtonStyle.red)
    async def aplicar_adv(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Modal de aplicar ADV manual (implementação necessária)", ephemeral=True)

    @discord.ui.button(label="Remover ADV Manual", style=discord.ButtonStyle.grey)
    async def remover_adv(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Modal de remover ADV manual (implementação necessária)", ephemeral=True)

    @discord.ui.button(label="Ver VADV", style=discord.ButtonStyle.blurple)
    async def ver_vadv(self, interaction: discord.Interaction, button: discord.ui.Button):
        adv_ativos = await self.cog.ver_vadv()
        if adv_ativos:
            desc = "\n".join([f"{apelido}: {qtd}" for apelido, qtd in adv_ativos.items()])
        else:
            desc = "Nenhum ADV ativo no momento."
        embed = discord.Embed(title="📋 ADV Ativos (VADV)", description=desc, color=discord.Color.orange())
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Setup
async def setup(bot):
    await bot.add_cog(PainelStaff(bot))