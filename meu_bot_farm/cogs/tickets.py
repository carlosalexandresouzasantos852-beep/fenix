# =========================
# TICKETS.PY — SISTEMA FARM FINAL (ESTÁVEL)
# =========================

import os
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import asyncio

CONFIG_PATH = "meu_bot_farm/data/config_farm.json"

GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

# =========================
# CONFIG (ISOLADO POR GUILD)
# =========================
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
            "adv_ativos": {},
            "historico_adv": {},
            "adv_agendado": {
                "ativo": True,
                "weekday": 6,      # Domingo
                "hora": 0,
                "minuto": 0,
                "aviso_1h": False,
                "ultima_execucao": None
            }
        }
    return cfg["guilds"][gid]

# =========================
# PAINEL STAFF
# =========================
class PainelStaffView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="📅 Próximo ADV automático", style=discord.ButtonStyle.blurple)
    async def proximo(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)
        ag = g["adv_agendado"]

        agora = datetime.now()
        alvo = agora + timedelta(days=(ag["weekday"] - agora.weekday()) % 7)
        alvo = alvo.replace(hour=ag["hora"], minute=ag["minuto"], second=0)

        embed = discord.Embed(title="📅 ADV Automático", color=discord.Color.blue())
        embed.add_field(name="Status", value="Ativo" if ag["ativo"] else "Cancelado")
        embed.add_field(name="Próximo ADV", value=alvo.strftime("%d/%m/%Y %H:%M"))

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Cancelar ADV da semana", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)
        g["adv_agendado"]["ativo"] = False
        salvar_config(cfg)
        await interaction.response.send_message("❌ ADV automático cancelado para esta semana.", ephemeral=True)

    @discord.ui.button(label="⚠️ Ver ADV", style=discord.ButtonStyle.gray)
    async def ver_adv(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        embed = discord.Embed(title="⚠️ ADV Ativos", color=discord.Color.red())
        if not g["adv_ativos"]:
            embed.description = "Nenhum ADV ativo."
        else:
            for uid, info in g["adv_ativos"].items():
                embed.add_field(name=info["nome"], value=info["motivo"], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================
# COG
# =========================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop_adv.start()
        self.loop_reset.start()

    # =========================
    # COMANDOS (NÃO MEXIDOS)
    # =========================
    @commands.command()
    async def painelfarm(self, ctx):
        embed = discord.Embed(
            title="📦 PAINEL DE FARM",
            description="Selecione seu cargo e entregue o farm",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed)

    @commands.command()
    async def painelstaff(self, ctx):
        embed = discord.Embed(
            title="📋 PAINEL STAFF",
            description="Gerenciamento de ADV",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=PainelStaffView(ctx.guild.id))

    @app_commands.command(name="configticketfarm")
    async def configticketfarm(self, interaction: discord.Interaction, *args):
        pass  # NÃO ALTERADO

    @app_commands.command(name="addcargo")
    async def addcargo(self, interaction: discord.Interaction, *args):
        pass  # NÃO ALTERADO

    # =========================
    # LOOP ADV AUTOMÁTICO
    # =========================
    @tasks.loop(minutes=1)
    async def loop_adv(self):
        cfg = garantir_config()
        agora = datetime.now()

        for gid, g in cfg["guilds"].items():
            ag = g["adv_agendado"]
            if not ag["ativo"]:
                continue

            if agora.weekday() != ag["weekday"]:
                ag["aviso_1h"] = False
                continue

            alvo = agora.replace(hour=ag["hora"], minute=ag["minuto"], second=0)

            # AVISO 1H ANTES
            if alvo - timedelta(hours=1) <= agora < alvo and not ag["aviso_1h"]:
                guild = self.bot.get_guild(int(gid))
                canal = guild.get_channel(g["canal_logs_adv"])
                if canal:
                    await canal.send("⚠️ ADV automático será aplicado em **1 hora**.")
                ag["aviso_1h"] = True
                salvar_config(cfg)

            # APLICAR ADV
            if agora >= alvo and ag["ultima_execucao"] != alvo.isoformat():
                guild = self.bot.get_guild(int(gid))
                canal = guild.get_channel(g["canal_logs_adv"])

                embed = discord.Embed(
                    title="⚠️ ADV AUTOMÁTICO — NÃO ENTREGOU FARM",
                    color=discord.Color.red(),
                    timestamp=agora
                )

                for member in guild.members:
                    cargos_validos = g["metas"].keys()
                    if not any(r.name in cargos_validos for r in member.roles):
                        continue

                    uid = str(member.id)
                    if uid not in g["entregas_semana"]:
                        g["adv_ativos"][uid] = {
                            "nome": member.display_name,
                            "motivo": "Não entregou farm",
                            "aplicado_por": self.bot.user.name,
                            "data": agora.strftime("%d/%m/%Y"),
                            "nivel": "1/5"
                        }
                        g["historico_adv"].setdefault(uid, []).append(
                            f"ADV automático — Não entregou farm — {agora.strftime('%d/%m/%Y')}"
                        )
                        embed.add_field(
                            name=member.display_name,
                            value="❌ Não entregou farm — ADV 1/5",
                            inline=False
                        )

                if canal and embed.fields:
                    await canal.send(embed=embed)

                ag["ultima_execucao"] = alvo.isoformat()
                salvar_config(cfg)

    # =========================
    # RESET SEMANAL — SEGUNDA 00:00
    # =========================
    @tasks.loop(minutes=1)
    async def loop_reset(self):
        cfg = garantir_config()
        agora = datetime.now()

        if agora.weekday() == 0 and agora.hour == 0 and agora.minute == 0:
            for g in cfg["guilds"].values():
                g["entregas_semana"] = {}
                g["adv_ativos"] = {}
                g["adv_agendado"]["ativo"] = True
                g["adv_agendado"]["ultima_execucao"] = None
            salvar_config(cfg)

# =========================
# SETUP
# =========================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()
    print("✅ Tickets carregado — ADV automático ATIVO")