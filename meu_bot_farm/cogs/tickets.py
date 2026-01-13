# =========================
# TICKETS.PY — SISTEMA FARM FINAL DEFINITIVO
# =========================

import os
import json
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

CONFIG_PATH = "meu_bot_farm/data/config_farm.json"

GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

# =========================
# CONFIG
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

def garantir_guild(cfg, guild_id):
    gid = str(guild_id)
    if gid not in cfg["guilds"]:
        cfg["guilds"][gid] = {
            "categoria_analise": 0,
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
                "aviso_enviado": False
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

    @discord.ui.button(label="📅 Status ADV Automático", style=discord.ButtonStyle.blurple)
    async def status_adv(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)
        ag = g["agendamento_adv"]

        now = datetime.now()
        target = now + timedelta(
            days=(ag["weekday"] - now.weekday()) % 7
        )
        target = target.replace(hour=ag["hora"], minute=ag["minuto"], second=0)

        if target < now:
            target += timedelta(days=7)

        restante = target - now
        dias, resto = divmod(restante.seconds, 86400)
        horas, resto = divmod(resto, 3600)
        minutos = resto // 60

        embed = discord.Embed(title="📅 ADV Automático", color=discord.Color.blue())
        embed.add_field(name="Ativo", value="Sim" if ag["ativo"] else "Não")
        embed.add_field(name="Próximo ADV em", value=f"{restante.days}d {horas}h {minutos}m")
        embed.add_field(name="Dia", value="Domingo")
        embed.add_field(name="Hora", value="00:00")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Cancelar ADV da Semana", style=discord.ButtonStyle.red)
    async def cancelar_adv(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        g = garantir_guild(cfg, self.guild_id)
        g["agendamento_adv"]["ativo"] = False
        salvar_config(cfg)

        await interaction.response.send_message("❌ ADV automático desta semana cancelado.", ephemeral=True)

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
            description="Gerenciamento de ADV e entregas",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=PainelStaffView(ctx.guild.id))

    @tasks.loop(minutes=1)
    async def loop_adv(self):
        cfg = garantir_config()
        agora = datetime.now()

        for gid, g in cfg["guilds"].items():
            guild = self.bot.get_guild(int(gid))
            if not guild:
                continue

            ag = g["agendamento_adv"]

            # AVISO 1H ANTES
            if ag["ativo"]:
                aviso_time = agora.replace(
                    hour=ag["hora"], minute=ag["minuto"], second=0
                ) - timedelta(hours=1)

                if agora.weekday() == ag["weekday"] and agora.hour == aviso_time.hour and agora.minute == aviso_time.minute:
                    if not ag["aviso_enviado"]:
                        canal = guild.get_channel(g["canal_logs_adv"])
                        if canal:
                            await canal.send("⚠️ **ADV automático será aplicado em 1 hora!**")
                        ag["aviso_enviado"] = True
                        salvar_config(cfg)

            # APLICA ADV
            if ag["ativo"] and agora.weekday() == ag["weekday"] and agora.hour == ag["hora"] and agora.minute == ag["minuto"]:
                cargos_validos = set(g["metas"].keys())
                entregou = set(g["entregas_semana"].keys())

                for member in guild.members:
                    if not any(r.name in cargos_validos for r in member.roles):
                        continue

                    uid = str(member.id)
                    if uid in entregou or uid in g["adv_ativos"]:
                        continue

                    g["adv_ativos"][uid] = "Não entregou farm"
                    g["historico_adv"].setdefault(uid, []).append(
                        f"ADV automático — {agora.strftime('%d/%m/%Y')}"
                    )

                salvar_config(cfg)

            # RESET SEGUNDA 00:00
            if agora.weekday() == 0 and agora.hour == 0 and agora.minute == 0:
                g["entregas_semana"] = {}
                g["agendamento_adv"]["ativo"] = True
                g["agendamento_adv"]["aviso_enviado"] = False
                salvar_config(cfg)

# =========================
# SETUP
# =========================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
    print("✅ Tickets carregado — ADV, reset e contador OK")
