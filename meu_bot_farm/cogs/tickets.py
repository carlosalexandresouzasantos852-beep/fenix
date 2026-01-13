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
# CONFIG POR GUILD
# =========================
def garantir_config():
    default = {"guilds": {}}
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

        if qtd >= self.meta:
            status = "✅ Meta CONCLUÍDA"
        elif qtd >= self.meta / 2:
            status = f"⚠️ Faltam {self.meta - qtd}"
        else:
            status = "❌ Menos da metade da meta"
            g["adv_ativos"][uid] = "Entregou menos da metade da meta"
            g["historico_adv"].setdefault(uid, []).append(
                f"{g['adv_ativos'][uid]} — {datetime.now().strftime('%d/%m/%Y')}"
            )

        # Remove ADV se entregou o dobro da meta
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
        canal = await categoria.create_text_channel(f"entrega-{interaction.user.name}")

        embed = discord.Embed(title="📦 ENTREGA EM ANÁLISE", color=discord.Color.orange())
        for k, v in dados.items():
            embed.add_field(name=k, value=str(v), inline=False)

        view = AnaliseView(uid, dados, canal.id)
        await canal.send(embed=embed, view=view)

        await interaction.response.send_message(
            "✅ Sua entrega foi enviada para análise.", ephemeral=True
        )
        await asyncio.sleep(5)
        await interaction.delete_original_response()


# =========================
# PAINEL ANALISE TEMPORÁRIO
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

        msg = await canal_aceitos.send(embed=embed)
        await msg.pin()

        canal_temp = interaction.guild.get_channel(self.canal_id)
        if canal_temp:
            await canal_temp.delete()

        await interaction.response.send_message("✅ Entrega aceita!", ephemeral=True)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.red)
    async def recusar(self, interaction: discord.Interaction, _):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, interaction.guild.id)
        canal_recusados = interaction.guild.get_channel(g["canal_recusados"])

        embed = discord.Embed(title="📦 ENTREGA RECUSADA", color=discord.Color.red())
        for k, v in self.dados.items():
            embed.add_field(name=k, value=str(v), inline=False)

        msg = await canal_recusados.send(embed=embed)
        await msg.pin()

        canal_temp = interaction.guild.get_channel(self.canal_id)
        if canal_temp:
            await canal_temp.delete()

        await interaction.response.send_message("❌ Entrega recusada!", ephemeral=True)


# =========================
# MODAL APLICAR ADV
# =========================
class AplicarAdvModal(discord.ui.Modal, title="➕ Aplicar ADV"):
    usuario = discord.ui.TextInput(label="ID do usuário", required=True)
    motivo = discord.ui.TextInput(label="Motivo", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, interaction.guild.id)
        uid = self.usuario.value.strip()
        g["adv_ativos"][uid] = self.motivo.value
        g["historico_adv"].setdefault(uid, []).append(
            f"{self.motivo.value} — {datetime.now().strftime('%d/%m/%Y')} — aplicado pelo bot"
        )
        salvar_config(cfg_total)
        await interaction.response.send_message(f"✅ ADV aplicado para {uid}", ephemeral=True)


# =========================
# MODAL REMOVER ADV
# =========================
class RemoverAdvModal(discord.ui.Modal, title="➖ Remover ADV"):
    usuario = discord.ui.TextInput(label="ID do usuário", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, interaction.guild.id)
        uid = self.usuario.value.strip()
        if uid in g["adv_ativos"]:
            del g["adv_ativos"][uid]
            salvar_config(cfg_total)
            await interaction.response.send_message(f"✅ ADV removido para {uid}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Usuário sem ADV.", ephemeral=True)


# =========================
# PAINEL FARM
# =========================
class PainelFarmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cargo = None
        self.meta = None
        self.add_item(CargoSelect(self))
        self.add_item(EntregarButton(self))


class CargoSelect(discord.ui.Select):
    def __init__(self, parent):
        cfg_total = garantir_config()
        options = [
            discord.SelectOption(label=nome, value=nome)
            for nome in cfg_total["guilds"][0]["metas"].keys()
        ]
        super().__init__(placeholder="Selecione seu cargo", options=options)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        cfg_total = garantir_config()
        g = garantir_guild(cfg_total, interaction.guild.id)
        cargo = self.values[0]
        self.parent.cargo = cargo
        self.parent.meta = g["metas"][cargo]

        await interaction.response.send_message(
            f"✅ Você selecionou o cargo {cargo}", ephemeral=True
        )
        await asyncio.sleep(5)
        await interaction.delete_original_response()
        await interaction.message.edit(view=self.parent)


class EntregarButton(discord.ui.Button):
    def __init__(self, parent):
        super().__init__(label="📦 Entregar Farm", style=discord.ButtonStyle.green)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        if not self.parent.cargo:
            return await interaction.response.send_message(
                "❌ Selecione o cargo primeiro.",
                ephemeral=True
            )
        await interaction.response.send_modal(EntregaModal(self.parent.cargo, self.parent.meta))


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
        embed = discord.Embed(title="📦 PAINEL DE FARM", description="Selecione seu cargo e entregue o farm", color=discord.Color.blurple)
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=PainelFarmView())

    @commands.command()
    async def painelstaff(self, ctx):
        embed = discord.Embed(title="📋 PAINEL STAFF", description="Gerenciamento completo de entregas e ADV", color=discord.Color.dark_blue)
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=PainelStaffView())

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