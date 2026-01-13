# =========================
# TICKETS.PY — SISTEMA FARM FINAL COMPLETO
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
    default = {
        "guilds": {}
    }
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)
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
                "weekday": 6,  # Domingo
                "hora": 0,
                "minuto": 0,
                "aviso_1h": False,
                "ultima_execucao": None
            }
        }
    return cfg["guilds"][gid]

# =========================
# MODAL ENTREGA
# =========================
class EntregaModal(discord.ui.Modal, title="📦 Entrega de Farm"):
    quantidade = discord.ui.TextInput(label="Quantidade entregue", required=True)
    entregue_para = discord.ui.TextInput(label="Entregou para quem?", required=True)

    def __init__(self, cargo_nome, meta):
        super().__init__()
        self.cargo_nome = cargo_nome
        self.meta = meta

    async def on_submit(self, interaction: discord.Interaction):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, interaction.guild.id)
        uid = str(interaction.user.id)

        if uid in g["entregas_semana"]:
            return await interaction.response.send_message(
                "❌ Você já realizou a entrega desta semana.",
                ephemeral=True
            )

        qtd = int(self.quantidade.value)
        status = "✅ Meta CONCLUÍDA" if qtd >= self.meta else f"⚠️ Faltam {self.meta - qtd}" if qtd >= self.meta / 2 else "❌ Menos da metade da meta"

        if status == "❌ Menos da metade da meta":
            g["adv_ativos"][uid] = "Entregou menos da metade da meta"
            g["historico_adv"].setdefault(uid, []).append(
                f"{g['adv_ativos'][uid]} — {datetime.now().strftime('%d/%m/%Y')}"
            )

        if uid in g["adv_ativos"] and qtd >= self.meta * 2:
            del g["adv_ativos"][uid]
            g["historico_adv"].setdefault(uid, []).append(
                f"ADV removido por farm dobrado — {datetime.now().strftime('%d/%m/%Y')}"
            )
            status = "♻️ ADV removido (farm dobrado)"

        dados = {
            "👤 Quem entregou": interaction.user.mention,
            "🎖 Cargo": self.cargo_nome,
            "🎯 Meta": self.meta,
            "📦 Quantidade": qtd,
            "📊 Status": status,
            "📍 Para": self.entregue_para.value,
            "📅 Data": datetime.now().strftime("%d/%m/%Y")
        }

        g["entregas_semana"][uid] = dados
        salvar_config(cfg_total)

        categoria = interaction.guild.get_channel(g["categoria_analise"])
        canal_temp = await categoria.create_text_channel(f"entrega-{interaction.user.name}")

        embed = discord.Embed(title="📦 ENTREGA EM ANÁLISE", color=discord.Color.orange())
        for k, v in dados.items():
            embed.add_field(name=k, value=str(v), inline=False)

        view = AnaliseView(uid, dados, canal_temp.id)
        await canal_temp.send(embed=embed, view=view)

        await interaction.response.send_message("✅ Sua entrega foi enviada para análise.", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.delete_original_response()

# =========================
# PAINEL DE ANÁLISE
# =========================
class AnaliseView(discord.ui.View):
    def __init__(self, uid, dados, canal_id):
        super().__init__(timeout=None)
        self.uid = uid
        self.dados = dados
        self.canal_id = canal_id

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.green)
    async def aceitar(self, interaction: discord.Interaction, _):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, interaction.guild.id)
        canal_aceitos = interaction.guild.get_channel(g["canal_aceitos"])

        embed = discord.Embed(title="📦 ENTREGA ACEITA", color=discord.Color.green())
        for k, v in self.dados.items():
            embed.add_field(name=k, value=str(v), inline=False)
        await canal_aceitos.send(embed=embed)

        canal_temp = interaction.guild.get_channel(self.canal_id)
        if canal_temp: await canal_temp.delete()
        await interaction.response.send_message("✅ Entrega aceita!", ephemeral=True)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.red)
    async def recusar(self, interaction: discord.Interaction, _):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, interaction.guild.id)
        canal_recusados = interaction.guild.get_channel(g["canal_recusados"])

        embed = discord.Embed(title="📦 ENTREGA RECUSADA", color=discord.Color.red())
        for k, v in self.dados.items():
            embed.add_field(name=k, value=str(v), inline=False)
        await canal_recusados.send(embed=embed)

        canal_temp = interaction.guild.get_channel(self.canal_id)
        if canal_temp: await canal_temp.delete()
        await interaction.response.send_message("❌ Entrega recusada!", ephemeral=True)

# =========================
# MODAL APLICAR / REMOVER ADV
# =========================
class AplicarAdvModal(discord.ui.Modal, title="➕ Aplicar ADV"):
    usuario = discord.ui.TextInput(label="Nome ou ID do usuário", required=True)
    motivo = discord.ui.TextInput(label="Motivo do ADV", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, interaction.guild.id)
        uid = self.usuario.value
        if uid.isdigit(): uid = str(uid)
        g["adv_ativos"][uid] = self.motivo.value
        g["historico_adv"].setdefault(uid, []).append(
            f"{self.motivo.value} — aplicado pelo bot em {datetime.now().strftime('%d/%m/%Y')}"
        )
        salvar_config(cfg_total)
        await interaction.response.send_message(f"✅ ADV aplicado para {self.usuario.value}", ephemeral=True)

class RemoverAdvModal(discord.ui.Modal, title="➖ Remover ADV"):
    usuario = discord.ui.TextInput(label="Nome ou ID do usuário", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, interaction.guild.id)
        uid = self.usuario.value
        if uid.isdigit(): uid = str(uid)
        if uid in g["adv_ativos"]:
            del g["adv_ativos"][uid]
            salvar_config(cfg_total)
            await interaction.response.send_message(f"✅ ADV removido para {self.usuario.value}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Nenhum ADV encontrado para {self.usuario.value}", ephemeral=True)

# =========================
# PAINEL FARM
# =========================
class CargoSelect(discord.ui.Select):
    def __init__(self, parent):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, parent.guild.id if hasattr(parent, "guild") else 0)
        options = [discord.SelectOption(label=cargo, value=cargo) for cargo in g["metas"].keys()]
        super().__init__(placeholder="Selecione seu cargo", options=options, min_values=1, max_values=1)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, interaction.guild.id)
        cargo = self.values[0]
        self.parent.cargo = cargo
        self.parent.meta = g["metas"][cargo]
        await interaction.response.send_message(f"✅ Cargo selecionado: {cargo}", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.delete_original_response()

class EntregarButton(discord.ui.Button):
    def __init__(self, parent):
        super().__init__(label="📦 Entregar Farm", style=discord.ButtonStyle.green)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        if not getattr(self.parent, "cargo", None):
            return await interaction.response.send_message("❌ Selecione o cargo primeiro.", ephemeral=True)
        await interaction.response.send_modal(EntregaModal(self.parent.cargo, self.parent.meta))

class PainelFarmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cargo = None
        self.meta = None
        self.add_item(CargoSelect(self))
        self.add_item(EntregarButton(self))

# =========================
# PAINEL STAFF (VERSÃO ATUALIZADA COM CONFIG ADV)
# =========================
# Use PainelStaffView que enviei no último bloco

# =========================
# COG PRINCIPAL
# =========================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop_adv.start()
        self.loop_reset.start()

    @commands.command()
    async def painelfarm(self, ctx):
        embed = discord.Embed(title="📦 PAINEL DE FARM", description="Selecione seu cargo e entregue o farm", color=discord.Color.blurple())
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=PainelFarmView())

    @commands.command()
    async def painelstaff(self, ctx):
        embed = discord.Embed(title="📋 PAINEL STAFF", description="Gerenciamento de entregas e ADV", color=discord.Color.dark_blue())
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=PainelStaffView())

    # =========================
    # LOOP ADV AUTOMÁTICO — DOMINGO 00:00 + AVISO 1H
    # =========================
    @tasks.loop(minutes=1)
    async def loop_adv(self):
        cfg_total = garantir_config()
        agora = datetime.now()

        for gid, g in cfg_total["guilds"].items():
            ag = g["adv_agendado"]
            guild = self.bot.get_guild(int(gid))
            if not guild: continue

            # RESET aviso se não é o dia do ADV
            if agora.weekday() != ag["weekday"]:
                ag["aviso_1h"] = False
                continue

            alvo = agora.replace(hour=ag["hora"], minute=ag["minuto"], second=0)

            # AVISO 1H ANTES
            if alvo - timedelta(hours=1) <= agora < alvo and not ag["aviso_1h"]:
                canal_logs = guild.get_channel(g["canal_logs_adv"])
                if canal_logs:
                    await canal_logs.send("⚠️ ADV automático será aplicado em **1 hora**.")
                ag["aviso_1h"] = True
                salvar_config(cfg_total)

            # APLICAR ADV
            if agora >= alvo and ag["ultima_execucao"] != alvo.isoformat() and ag["ativo"]:
                canal_logs = guild.get_channel(g["canal_logs_adv"])
                for member in guild.members:
                    for cargo_nome in g["metas"].keys():
                        if any(r.name == cargo_nome for r in member.roles):
                            uid = str(member.id)
                            if uid not in g["entregas_semana"]:
                                g["adv_ativos"][uid] = "Não entregou farm"
                                g["historico_adv"].setdefault(uid, []).append(
                                    f"ADV automático — {datetime.now().strftime('%d/%m/%Y')} (Bot)"
                                )
                # Envia lista de ADV
                if canal_logs:
                    embed = discord.Embed(title="⚠️ ADV AUTOMÁTICO", color=discord.Color.red())
                    for uid, motivo in g["adv_ativos"].items():
                        membro = guild.get_member(int(uid))
                        nome = membro.display_name if membro else f"Usuário {uid}"
                        embed.add_field(name=nome, value=motivo, inline=False)
                    await canal_logs.send(embed=embed)
                ag["ultima_execucao"] = alvo.isoformat()
                salvar_config(cfg_total)

    # =========================
    # LOOP RESET SEMANAL — SEGUNDA 00:00
    # =========================
    @tasks.loop(minutes=5)
    async def loop_reset(self):
        cfg_total = garantir_config()
        agora = datetime.now()
        for gid, g in cfg_total["guilds"].items():
            if agora.weekday() == 0 and agora.hour == 0 and agora.minute < 5:
                g["entregas_semana"] = {}
                salvar_config(cfg_total)

# =========================
# SETUP
# =========================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()
    print("✅ Tickets carregado e sincronizado")