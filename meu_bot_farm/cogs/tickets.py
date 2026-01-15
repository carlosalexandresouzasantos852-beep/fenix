# =========================
# TICKETS.PY — SISTEMA FARM PROFISSIONAL FINAL
# =========================

import os
import json
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

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
            "adv_ativos": {},
            "adv_agendado": {
                "ativo": True,
                "weekday": 6,
                "hora": 0,
                "minuto": 0,
                "ultima_execucao": None
            }
        }
    return cfg["guilds"][gid]

# ======================================================
# UTIL
# ======================================================
def proximo_adv(ag):
    agora = datetime.now()
    dias = (ag["weekday"] - agora.weekday()) % 7
    alvo = agora + timedelta(days=dias)
    return alvo.replace(hour=ag["hora"], minute=ag["minuto"], second=0)

def cronometro(ag):
    alvo = proximo_adv(ag)
    delta = alvo - datetime.now()
    if delta.total_seconds() <= 0:
        return "⏳ Executando agora"
    d = delta.days
    h, r = divmod(delta.seconds, 3600)
    m, _ = divmod(r, 60)
    return f"⏳ {d}d {h}h {m}m restantes"

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
                ephemeral=True
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

        await canal.send(embed=embed, view=AnaliseView(self.guild_id, embed))
        await interaction.response.send_message("✅ Enviado para análise.", ephemeral=True)

# ======================================================
# VIEW ANÁLISE (FIX DEFINITIVO)
# ======================================================
class AnaliseView(discord.ui.View):
    def __init__(self, guild_id, embed):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.embed = embed
        self.finalizado = False

    async def finalizar(self, interaction):
        if self.finalizado:
            return

        self.finalizado = True
        for item in self.children:
            item.disabled = True

        try:
            await interaction.message.edit(view=self)
        except:
            pass

        await asyncio.sleep(1)
        await interaction.channel.delete()

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.green)
    async def aceitar(self, interaction: discord.Interaction, _):
        if self.finalizado:
            return

        await interaction.response.defer()
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        canal = interaction.guild.get_channel(g["canal_aceitos"])
        msg = await canal.send(embed=self.embed)

        g["entregas_aceitas"].append({
            "membro": self.embed.fields[0].value,
            "cargo": self.embed.fields[1].value,
            "quantidade": self.embed.fields[3].value
        })
        salvar_config(cfg)

        await asyncio.sleep(86400)
        await msg.delete()
        await self.finalizar(interaction)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.red)
    async def recusar(self, interaction: discord.Interaction, _):
        if self.finalizado:
            return

        await interaction.response.defer()
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        canal = interaction.guild.get_channel(g["canal_recusados"])
        msg = await canal.send(embed=self.embed)

        await asyncio.sleep(36000)
        await msg.delete()
        await self.finalizar(interaction)

        # ======================================================
# MODAL AGENDAR ADV
# ======================================================
class AgendarADVModal(discord.ui.Modal, title="🗓️ Agendar ADV"):
    dia = discord.ui.TextInput(label="Dia da semana (0=Seg … 6=Dom)", required=True)
    hora = discord.ui.TextInput(label="Hora (HH:MM)", required=True)

    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        h, m = map(int, self.hora.value.split(":"))

        g["adv_agendado"] = {
            "ativo": True,
            "weekday": int(self.dia.value),
            "hora": h,
            "minuto": m,
            "ultima_execucao": None
        }

        salvar_config(cfg)
        await interaction.response.send_message("✅ ADV agendado com sucesso.", ephemeral=True)

# ======================================================
# PAINEL FARM
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
        await interaction.response.send_message(
            f"Cargo selecionado: **{self.cargo}**",
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
    def __init__(self, guild_id):
        super().__init__(timeout=None)
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
    def __init__(self, bot):
        self.bot = bot

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

# ======================================================
# SETUP
# ======================================================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)
    print("🔥 SISTEMA FARM PROFISSIONAL ATIVO")
