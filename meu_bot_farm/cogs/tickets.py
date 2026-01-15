# =========================
# TICKETS.PY — SISTEMA FARM PROFISSIONAL FINAL (CORRIGIDO)
# =========================

import os
import json
import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime

CONFIG_PATH = "meu_bot_farm/data/config_farm.json"
GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

# ======================================================
# CONFIG
# ======================================================
def garantir_config():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"guilds": {}}, f, indent=4, ensure_ascii=False)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def garantir_guild(cfg, gid):
    gid = str(gid)
    if gid not in cfg["guilds"]:
        cfg["guilds"][gid] = {
            "categoria_analise": 0,
            "canal_aceitos": 0,
            "canal_recusados": 0,
            "canal_logs_adv": 0,
            "metas": {},
            "entregas_semana": {},
            "entregas_aceitas": [],
            "adv_agendado": {"ativo": True, "data": None}
        }
    return cfg["guilds"][gid]

# ======================================================
# UTIL
# ======================================================
def cronometro(ag):
    if not ag["data"]:
        return "⏳ Domingo padrão"
    alvo = datetime.fromisoformat(ag["data"])
    delta = alvo - datetime.now()
    if delta.total_seconds() <= 0:
        return "⏳ Executando agora"
    d = delta.days
    h, r = divmod(delta.seconds, 3600)
    m, _ = divmod(r, 60)
    return f"⏳ {d}d {h}h {m}m restantes"

# ======================================================
# LOOP ADV
# ======================================================
@tasks.loop(minutes=1)
async def loop_adv(bot):
    cfg = garantir_config()
    agora = datetime.now()

    for gid, g in cfg["guilds"].items():
        if not g["adv_agendado"]["data"]:
            continue

        data_adv = datetime.fromisoformat(g["adv_agendado"]["data"])
        if agora >= data_adv:
            g["entregas_semana"].clear()
            g["entregas_aceitas"].clear()
            g["adv_agendado"]["data"] = None
            salvar_config(cfg)

# ======================================================
# PAINÉIS
# ======================================================
class PainelFarmView(discord.ui.View):
    def __init__(self, guild_id, cargos):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.cargo = None
        self.select.options = [discord.SelectOption(label=c) for c in cargos]

    @discord.ui.select(placeholder="Selecione seu cargo")
    async def select(self, interaction, select):
        self.cargo = select.values[0]
        await interaction.response.send_message(f"Cargo selecionado: **{self.cargo}**", ephemeral=True)

class PainelStaffView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

# ======================================================
# COG
# ======================================================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not loop_adv.is_running():
            loop_adv.start(bot)

    @commands.command()
    async def painelfarm(self, ctx):
        cfg = garantir_config()
        g = garantir_guild(cfg, ctx.guild.id)

        embed = discord.Embed(
            title="📦 Painel Farm",
            description=cronometro(g["adv_agendado"]),
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)

        await ctx.send(embed=embed, view=PainelFarmView(ctx.guild.id, g["metas"].keys()))

    @commands.command()
    async def painelstaff(self, ctx):
        cfg = garantir_config()
        g = garantir_guild(cfg, ctx.guild.id)

        embed = discord.Embed(
            title="📋 Painel Staff",
            description=cronometro(g["adv_agendado"]),
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=GIF_PAINEL)

        await ctx.send(embed=embed, view=PainelStaffView(ctx.guild.id))

    @app_commands.command(name="configticketfarm", description="Configura o sistema de farm")
    async def configticketfarm(
        self,
        interaction: discord.Interaction,
        meta_aviao: int,
        meta_membro: int,
        meta_recrutador: int,
        meta_gerente: int,
        categoria_analise: discord.CategoryChannel,
        canal_aceitos: discord.TextChannel,
        canal_recusados: discord.TextChannel,
        canal_adv: discord.TextChannel
    ):
        cfg = garantir_config()
        g = garantir_guild(cfg, interaction.guild.id)

        g["metas"] = {
            "aviãozinho": meta_aviao,
            "membro": meta_membro,
            "recrutador": meta_recrutador,
            "gerente": meta_gerente
        }

        g["categoria_analise"] = categoria_analise.id
        g["canal_aceitos"] = canal_aceitos.id
        g["canal_recusados"] = canal_recusados.id
        g["canal_logs_adv"] = canal_adv.id

        salvar_config(cfg)
        await interaction.response.send_message("✅ Configuração concluída.", ephemeral=True)

    @app_commands.command(name="addcargo", description="Adiciona ou atualiza a meta de um cargo")
    async def addcargo(
        self,
        interaction: discord.Interaction,
        cargo: discord.Role,
        meta: int
    ):
        cfg = garantir_config()
        g = garantir_guild(cfg, interaction.guild.id)

        g["metas"][cargo.name] = meta
        salvar_config(cfg)

        await interaction.response.send_message(
            f"✅ Cargo **{cargo.name}** configurado com meta **{meta}**.",
            ephemeral=True
        )

# ======================================================
# SETUP
# ======================================================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()
    print("🔥 SISTEMA FARM PROFISSIONAL ATIVO | SLASH SYNC OK")