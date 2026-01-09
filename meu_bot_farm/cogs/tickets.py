# =========================
# TICKETS.PY — SISTEMA FARM COMPLETO (ESTÁVEL + ADV AUTOMÁTICO)
# =========================

import os
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime

CONFIG_PATH = "meu_bot_farm/data/config_farm.json"

GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

# =========================
# CONFIG
# =========================
def garantir_config():
    default = {
        "categoria_analise": 0,
        "canal_aceitos": 0,
        "canal_recusados": 0,
        "canal_logs_adv": 0,
        "cargos": {},
        "entregas_semana": {},
        "adv_ativos": {},
        "historico_adv": {}
    }

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)
        return default

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


# =========================
# COG
# =========================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop_semanal.start()

    # =========================
    # PAINÉIS
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
            description="Gerenciamento de farm e ADV",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed)

    # =========================
    # SLASH CONFIG
    # =========================
    @app_commands.command(name="configticketfarm")
    @app_commands.checks.has_permissions(administrator=True)
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

        cfg["metas"] = {
            "aviãozinho": meta_aviao,
            "membro": meta_membro,
            "recrutador": meta_recrutador,
            "gerente": meta_gerente
        }

        cfg["categoria_analise"] = categoria_analise.id
        cfg["canal_aceitos"] = canal_aceitos.id
        cfg["canal_recusados"] = canal_recusados.id
        cfg["canal_logs_adv"] = canal_adv.id

        salvar_config(cfg)

        await interaction.response.send_message(
            "✅ Configuração do Ticket Farm salva com sucesso.",
            ephemeral=True
        )

    # =========================
    # SLASH ADD CARGO
    # =========================
    @app_commands.command(name="addcargo")
    @app_commands.checks.has_permissions(administrator=True)
    async def addcargo(self, interaction: discord.Interaction, cargo: discord.Role, meta: int):
        cfg = garantir_config()
        cfg["cargos"][str(cargo.id)] = meta
        salvar_config(cfg)

        await interaction.response.send_message(
            f"✅ Cargo **{cargo.name}** adicionado com meta **{meta}**.",
            ephemeral=True
        )

    # =========================
    # LOOP SEMANAL (ADV AUTOMÁTICO)
    # =========================
    @tasks.loop(minutes=1)
    async def loop_semanal(self):
        cfg = garantir_config()
        agora = datetime.now()

        # =========================
        # DOMINGO 00:00 — ADV AUTOMÁTICO
        # =========================
        if agora.weekday() == 6 and agora.hour == 0 and agora.minute == 0:
            guild = self.bot.guilds[0]
            canal_adv = guild.get_channel(cfg["canal_logs_adv"])

            if not canal_adv:
                return

            texto = []
            entregou = set(cfg["entregas_semana"].keys())

            for cargo_id in cfg["cargos"]:
                role = guild.get_role(int(cargo_id))
                if not role:
                    continue

                for member in role.members:
                    uid = str(member.id)

                    if uid in entregou:
                        continue

                    if uid in cfg["adv_ativos"]:
                        continue

                    motivo = f"Não entregou farm na semana — {agora.strftime('%d/%m/%Y')}"
                    cfg["adv_ativos"][uid] = motivo
                    cfg["historico_adv"].setdefault(uid, []).append(motivo)

                    texto.append(f"• {member.display_name}")

            salvar_config(cfg)

            if texto:
                embed = discord.Embed(
                    title="⚠️ ADV AUTOMÁTICO — NÃO ENTREGARAM FARM",
                    description="\n".join(texto),
                    color=discord.Color.red(),
                    timestamp=agora
                )
                await canal_adv.send(embed=embed)

        # =========================
        # SEGUNDA 00:00 — RESET
        # =========================
        if agora.weekday() == 0 and agora.hour == 0 and agora.minute == 0:
            cfg["entregas_semana"] = {}
            cfg["adv_ativos"] = {}
            salvar_config(cfg)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()
    print("✅ Tickets carregado com ADV automático funcionando")