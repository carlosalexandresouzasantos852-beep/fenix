# =========================
# TICKETS.PY — SISTEMA FARM PROFISSIONAL FINAL
# =========================

import os
import json
import asyncio
import discord
from discord.ext import commands, tasks
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
                "aviso_1h": False,
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
            await interaction.response.send_message("❌ Você já entregou nesta semana.", ephemeral=True)
            await asyncio.sleep(5)
            return await interaction.delete_original_response()

        qtd = int(self.quantidade.value)
        meta = g["metas"][self.cargo]

        status = "✅ Meta concluída" if qtd >= meta else f"❌ Faltaram {meta - qtd}"

        g["entregas_semana"][uid] = True
        salvar_config(cfg)

        guild = interaction.guild
        categoria = guild.get_channel(g["categoria_analise"])
        canal = await guild.create_text_channel(f"analise-{interaction.user.name}", category=categoria)

        embed = discord.Embed(title="📦 Análise de Entrega", color=discord.Color.blurple())
        embed.add_field(name="👤 Membro", value=interaction.user.display_name, inline=False)
        embed.add_field(name="🥇 Cargo", value=self.cargo, inline=False)
        embed.add_field(name="🎯 Meta", value=str(meta), inline=False)
        embed.add_field(name="📦 Quantidade", value=str(qtd), inline=False)
        embed.add_field(name="📊 Status", value=status, inline=False)
        embed.add_field(name="📌 Para quem?", value=self.para_quem.value, inline=False)
        embed.add_field(name="📆 Data", value=datetime.now().strftime("%d/%m/%Y %H:%M"), inline=False)

        await canal.send(embed=embed, view=AnaliseView(self.guild_id, embed))

        await interaction.response.send_message("✅ Entrega enviada para análise da staff.", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.delete_original_response()

# ======================================================
# VIEW ANÁLISE
# ======================================================
class AnaliseView(discord.ui.View):
    def __init__(self, guild_id, embed):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.embed = embed

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.green)
    async def aceitar(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)
        canal = interaction.guild.get_channel(g["canal_aceitos"])

        msg = await canal.send(embed=self.embed)
        g["entregas_aceitas"].append(self.embed.fields[0].value)
        salvar_config(cfg)

        await asyncio.sleep(86400)
        await msg.delete()
        await interaction.channel.delete()

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.red)
    async def recusar(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)
        canal = interaction.guild.get_channel(g["canal_recusados"])

        msg = await canal.send(embed=self.embed)
        await asyncio.sleep(36000)
        await msg.delete()
        await interaction.channel.delete()

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
    async def select(self, interaction: discord.Interaction, select):
        self.cargo = select.values[0]
        await interaction.response.send_message(f"Cargo selecionado: **{self.cargo}**", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.delete_original_response()

    @discord.ui.button(label="📦 Entregar Farm", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        if not self.cargo:
            await interaction.response.send_message("❌ Selecione um cargo.", ephemeral=True)
            await asyncio.sleep(5)
            return await interaction.delete_original_response()

        await interaction.response.send_modal(EntregaModal(interaction.guild.id, self.cargo))
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
            for nome in g["entregas_aceitas"]:
                embed.add_field(name="👤 Membro", value=nome, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Cancelar Agendamento", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        g["adv_agendado"]["weekday"] = 6
        g["adv_agendado"]["hora"] = 0
        g["adv_agendado"]["minuto"] = 0
        salvar_config(cfg)

        await interaction.response.send_message("✅ Agendamento cancelado. Domingo voltou a ser o padrão.", ephemeral=True)

# ======================================================
# COG
# ======================================================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop_adv.start()
        self.loop_reset.start()

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

    # ===== COMANDOS MANTIDOS =====
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
        await asyncio.sleep(5)
        await interaction.delete_original_response()

    @app_commands.command(name="addcargo")
    @app_commands.checks.has_permissions(administrator=True)
    async def addcargo(self, interaction: discord.Interaction, cargo: discord.Role, meta: int):
        cfg = garantir_config()
        g = garantir_guild(cfg, interaction.guild.id)
        g["metas"][cargo.name] = meta
        salvar_config(cfg)

        await interaction.response.send_message("Cargo adicionado.", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.delete_original_response()

# ======================================================
# SETUP
# ======================================================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()
    print("✅ Sistema FARM PROFISSIONAL ATIVO")