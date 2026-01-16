# =========================
# TICKETS.PY — SISTEMA FARM PROFISSIONAL FINAL
# =========================

import os
import json
import asyncio
import discord
from discord.ext import commands
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
            "adv_agendado": {
                "ativo": True,
                "data": None
            }
        }
    return cfg["guilds"][gid]

# ======================================================
# UTIL ADV
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
# LOOP AUTOMÁTICO ADV (ADICIONADO)
# ======================================================
async def executar_adv(bot, guild_id):
    cfg = garantir_config()
    g = garantir_guild(cfg, guild_id)

    # Reset semanal
    g["entregas_semana"].clear()
    g["entregas_aceitas"].clear()

    # Log
    canal = bot.get_channel(g["canal_logs_adv"])
    if canal:
        embed = discord.Embed(
            title="⚠️ ADV EXECUTADO",
            description="O ADV semanal foi executado automaticamente.\nEntregas resetadas.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await canal.send(embed=embed)

    # Volta para domingo padrão
    g["adv_agendado"]["data"] = None
    salvar_config(cfg)

@tasks.loop(minutes=1)
async def loop_adv(bot):
    cfg = garantir_config()
    agora = datetime.now()

    for gid, g in cfg["guilds"].items():
        if not g["adv_agendado"]["data"]:
            continue

        data_adv = datetime.fromisoformat(g["adv_agendado"]["data"])
        if agora >= data_adv:
            await executar_adv(bot, int(gid))

# ======================================================
# MODAL ENTREGA
# ======================================================
class EntregaModal(discord.ui.Modal, title="📦 Entrega de Farm"):
    quantidade = discord.ui.TextInput(label="Quantidade entregue", required=True)
    para_quem = discord.ui.TextInput(label="Para quem foi entregue (@)", required=True)

    def __init__(self, guild_id, cargo):
        super().__init__()
        self.guild_id = guild_id
        self.cargo = cargo

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)
        uid = str(interaction.user.id)

        if uid in g["entregas_semana"]:
            await interaction.response.send_message(
                "❌ Você já entregou nesta semana.",
                ephemeral=True,
                delete_after=5
            )
            return

        qtd = int(self.quantidade.value)
        meta = g["metas"][self.cargo]

        g["entregas_semana"][uid] = {
            "nome": interaction.user.display_name,
            "cargo": self.cargo,
            "quantidade": qtd,
            "meta": meta
        }
        salvar_config(cfg)

        categoria = interaction.guild.get_channel(g["categoria_analise"])
        canal = await interaction.guild.create_text_channel(
            f"analise-{interaction.user.name}",
            category=categoria
        )

        embed = discord.Embed(title="📦 Análise de Entrega", color=discord.Color.blurple())
        embed.add_field(name="👤 Membro", value=interaction.user.display_name, inline=False)
        embed.add_field(name="🥇 Cargo", value=self.cargo, inline=False)
        embed.add_field(name="🎯 Meta", value=meta, inline=False)
        embed.add_field(name="📦 Quantidade", value=qtd, inline=False)
        embed.add_field(name="📌 Para quem?", value=self.para_quem.value, inline=False)
        embed.add_field(name="📆 Data", value=datetime.now().strftime("%d/%m/%Y %H:%M"), inline=False)

        await canal.send(embed=embed, view=AnaliseView(self.guild_id))
        await interaction.response.send_message(
            "✅ Entrega enviada para análise.",
            ephemeral=True,
            delete_after=5
        )

# ======================================================
# VIEW ANÁLISE (CANAL TEMPORÁRIO)
# ======================================================
class AnaliseView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.finalizado = False

    async def finalizar(self, interaction):
        if self.finalizado:
            return
        self.finalizado = True
        await asyncio.sleep(1)
        await interaction.channel.delete()

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.green)
    async def aceitar(self, interaction: discord.Interaction, _):
        await interaction.response.defer()
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        canal = interaction.guild.get_channel(g["canal_aceitos"])
        await canal.send(embed=interaction.message.embeds[0])
        await self.finalizar(interaction)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.red)
    async def recusar(self, interaction: discord.Interaction, _):
        await interaction.response.defer()
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        canal = interaction.guild.get_channel(g["canal_recusados"])
        await canal.send(embed=interaction.message.embeds[0])
        await self.finalizar(interaction)

# ======================================================
# MODAL AGENDAR ADV
# ======================================================
class AgendarADVModal(discord.ui.Modal, title="🗓️ Agendar ADV"):
    data = discord.ui.TextInput(label="Data (DD/MM/AAAA)", required=True)
    hora = discord.ui.TextInput(label="Hora (HH:MM)", required=True)

    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        data = datetime.strptime(
            self.data.value + " " + self.hora.value,
            "%d/%m/%Y %H:%M"
        )

        g["adv_agendado"]["data"] = data.isoformat()
        salvar_config(cfg)

        await interaction.response.send_message(
            "✅ ADV agendado com sucesso.",
            ephemeral=True,
            delete_after=5
        )

# ======================================================
# PAINEL FARM
# ======================================================
class PainelFarmView(discord.ui.View):
    def _init_(self, guild_id, cargos):
        super()._init_(timeout=None)
        self.guild_id = guild_id
        self.cargo = None
        self.select.options = [discord.SelectOption(label=c) for c in cargos]

    @discord.ui.select(placeholder="Selecione seu cargo")
    async def select(self, interaction, select):
        self.cargo = select.values[0]
        await interaction.response.send_message(
            f"Cargo selecionado: *{self.cargo}*",
            ephemeral=True
        )

    @discord.ui.button(label="📦 Entregar Farm", style=discord.ButtonStyle.green)
    async def entregar(self, interaction, _):
        if not self.cargo:
            await interaction.response.send_message(
                "❌ Selecione um cargo.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            EntregaModal(interaction.guild.id, self.cargo)
        )
        self.cargo = None

# ======================================================
# PAINEL STAFF
# ======================================================
class PainelStaffView(discord.ui.View):
    def _init_(self, guild_id):
        super()._init_(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="📦 Ver Entregas", style=discord.ButtonStyle.gray)
    async def ver_entregas(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        embed = discord.Embed(title="📦 Entregas Aceitas (Semana)", color=discord.Color.green())

        if not g["entregas_aceitas"]:
            embed.description = "Nenhuma entrega aceita."
        else:
            for e in g["entregas_aceitas"]:
                embed.add_field(name=e["membro"], value=f"{e['cargo']} • {e['quantidade']}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚠️ Ver ADV", style=discord.ButtonStyle.red)
    async def ver_adv(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        embed = discord.Embed(title="⚠️ ADV Ativos", color=discord.Color.red())
        if not g["adv_ativos"]:
            embed.description = "Nenhuma advertência."
        else:
            for adv in g["adv_ativos"].values():
                embed.add_field(name=adv["nome"], value=f"{adv['quantidade']}/5", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⏭️ Próximo ADV", style=discord.ButtonStyle.blurple)
    async def proximo(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)
        alvo = proximo_adv(g["adv_agendado"])
        await interaction.response.send_message(f"{alvo.strftime('%d/%m %H:%M')}\n{cronometro(g['adv_agendado'])}", ephemeral=True)

    @discord.ui.button(label="🗓️ Agendar ADV", style=discord.ButtonStyle.green)
    async def agendar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(AgendarADVModal(self.guild_id))

    @discord.ui.button(label="❌ Cancelar Agendamento", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        g["adv_agendado"] = {
            "ativo": True,
            "weekday": 6,
            "hora": 0,
            "minuto": 0,
            "ultima_execucao": None
        }

        salvar_config(cfg)
        await interaction.response.send_message("✅ Agendamento cancelado. Domingo voltou a ser o padrão.", ephemeral=True)

# ======================================================
# COG
# ======================================================
class Tickets(commands.Cog):
    def init(self, bot):
        self.bot = bot

    @commands.command()
    async def painelfarm(self, ctx):
        cfg = garantir_config()
        g = garantir_guild(cfg, ctx.guild.id)

        embed = discord.Embed(title="📦 Painel Farm", description=cronometro(g["adv_agendado"]), color=discord.Color.blurple())
        embed.set_image(url=GIF_PAINEL)

        await ctx.send(embed=embed, view=PainelFarmView(ctx.guild.id, g["metas"].keys()))

    @commands.command()
    async def painelstaff(self, ctx):
        cfg = garantir_config()
        g = garantir_guild(cfg, ctx.guild.id)

        embed = discord.Embed(title="📋 Painel Staff", description=cronometro(g["adv_agendado"]), color=discord.Color.dark_blue())
        embed.set_image(url=GIF_PAINEL)

        await ctx.send(embed=embed, view=PainelStaffView(ctx.guild.id))

    # ===== SLASH (NÃO MEXIDOS) =====
    @app_commands.command(name="configticketfarm")
    @app_commands.checks.has_permissions(administrator=True)
    async def configticketfarm(self, interaction: discord.Interaction, meta_aviao: int, meta_membro: int, meta_recrutador: int, meta_gerente: int, categoria_analise: discord.CategoryChannel, canal_aceitos: discord.TextChannel, canal_recusados: discord.TextChannel, canal_adv: discord.TextChannel):
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

    @app_commands.command(name="addcargo")
    @app_commands.checks.has_permissions(administrator=True)
    async def addcargo(self, interaction: discord.Interaction, cargo: discord.Role, meta: int):
        cfg = garantir_config()
        g = garantir_guild(cfg, interaction.guild.id)
        g["metas"][cargo.name] = meta
        salvar_config(cfg)
        await interaction.response.send_message("✅ Cargo adicionado.", ephemeral=True)

# ======================================================
# SETUP
# ======================================================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)
    print("🔥 SISTEMA FARM PROFISSIONAL ATIVO")