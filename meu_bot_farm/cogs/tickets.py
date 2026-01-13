# =========================
# TICKETS.PY — SISTEMA FARM DEFINITIVO
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
# CONFIG GLOBAL (ISOLADO)
# =========================
def garantir_config():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"guilds": {}}, f, indent=4)
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
            "agendamento_adv": {
                "ativo": True,
                "weekday": 6,
                "hora": 0,
                "minuto": 0,
                "aviso_1h_enviado": False
            }
        }
    return cfg["guilds"][gid]

# =========================
# MODAIS ADV
# =========================
class AplicarAdvModal(discord.ui.Modal, title="➕ Aplicar ADV"):
    usuario = discord.ui.TextInput(label="ID do usuário", required=True)
    motivo = discord.ui.TextInput(label="Motivo do ADV", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        g = garantir_guild(cfg, interaction.guild.id)

        uid = self.usuario.value.strip()
        g["adv_ativos"][uid] = self.motivo.value
        g["historico_adv"].setdefault(uid, []).append(
            f"ADV manual — {self.motivo.value} — {datetime.now().strftime('%d/%m/%Y')}"
        )
        salvar_config(cfg)
        await interaction.response.send_message("✅ ADV aplicado.", ephemeral=True)

class RemoverAdvModal(discord.ui.Modal, title="➖ Remover ADV"):
    usuario = discord.ui.TextInput(label="ID do usuário", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        g = garantir_guild(cfg, interaction.guild.id)

        uid = self.usuario.value.strip()
        if uid in g["adv_ativos"]:
            del g["adv_ativos"][uid]
            g["historico_adv"].setdefault(uid, []).append(
                f"ADV removido manualmente — {datetime.now().strftime('%d/%m/%Y')}"
            )
            salvar_config(cfg)
            await interaction.response.send_message("✅ ADV removido.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Usuário sem ADV.", ephemeral=True)

# =========================
# PAINEL STAFF
# =========================
class PainelStaffView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="📅 Status ADV automático", style=discord.ButtonStyle.blurple)
    async def status(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)
        ag = g["agendamento_adv"]

        agora = datetime.now()
        alvo = agora + timedelta(
            days=(ag["weekday"] - agora.weekday()) % 7
        )
        alvo = alvo.replace(hour=ag["hora"], minute=ag["minuto"], second=0)

        delta = alvo - agora
        embed = discord.Embed(title="📅 ADV Automático", color=discord.Color.blue())
        embed.add_field(name="Ativo", value="Sim" if ag["ativo"] else "Não")
        embed.add_field(name="Próximo ADV", value=str(delta).split(".")[0])

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Cancelar ADV da semana", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)
        g["agendamento_adv"]["ativo"] = False
        salvar_config(cfg)
        await interaction.response.send_message("❌ ADV da semana cancelado.", ephemeral=True)

    @discord.ui.button(label="👀 Ver ADV ativos", style=discord.ButtonStyle.gray)
    async def ver_adv(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        embed = discord.Embed(title="⚠️ ADV Ativos", color=discord.Color.red())
        if not g["adv_ativos"]:
            embed.description = "Nenhum ADV ativo."
        else:
            for uid, motivo in g["adv_ativos"].items():
                embed.add_field(name=uid, value=motivo, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📜 Histórico ADV", style=discord.ButtonStyle.secondary)
    async def historico(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)

        embed = discord.Embed(title="📜 Histórico de ADV", color=discord.Color.dark_red())
        for uid, lista in g["historico_adv"].items():
            embed.add_field(name=uid, value="\n".join(lista[-5:]), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="➕ Aplicar ADV", style=discord.ButtonStyle.green)
    async def aplicar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(AplicarAdvModal())

    @discord.ui.button(label="➖ Remover ADV", style=discord.ButtonStyle.gray)
    async def remover(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(RemoverAdvModal())

# =========================
# COG PRINCIPAL
# =========================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop_adv.start()

    @commands.command()
    async def painelstaff(self, ctx):
        embed = discord.Embed(
            title="📋 PAINEL STAFF",
            description="Gerenciamento completo de ADV",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=PainelStaffView(ctx.guild.id))

    @tasks.loop(minutes=1)
    async def loop_adv(self):
        cfg = garantir_config()
        agora = datetime.now()

        for gid, g in cfg["guilds"].items():
            ag = g["agendamento_adv"]
            if not ag["ativo"]:
                continue

            alvo = agora.replace(hour=ag["hora"], minute=ag["minuto"], second=0)

            # AVISO 1H ANTES
            if alvo - timedelta(hours=1) <= agora < alvo and not ag["aviso_1h_enviado"]:
                guild = self.bot.get_guild(int(gid))
                canal = guild.get_channel(g["canal_logs_adv"])
                if canal:
                    await canal.send("⚠️ ADV automático será aplicado em 1 hora.")
                ag["aviso_1h_enviado"] = True
                salvar_config(cfg)

            # APLICAR ADV
            if agora.weekday() == ag["weekday"] and agora.hour == ag["hora"] and agora.minute == ag["minuto"]:
                guild = self.bot.get_guild(int(gid))
                cargos_validos = set(g["metas"].keys())

                for member in guild.members:
                    if not any(r.name in cargos_validos for r in member.roles):
                        continue
                    uid = str(member.id)
                    if uid not in g["entregas_semana"]:
                        g["adv_ativos"][uid] = "Não entregou farm"
                        g["historico_adv"].setdefault(uid, []).append(
                            f"ADV automático — {agora.strftime('%d/%m/%Y')}"
                        )

                g["entregas_semana"] = {}
                ag["aviso_1h_enviado"] = False
                salvar_config(cfg)

# =========================
# SETUP
# =========================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()
    print("✅ Tickets carregado — SISTEMA DEFINITIVO")
