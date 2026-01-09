# =========================
# TICKETS.PY — SISTEMA FARM COMPLETO FINAL
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
# CONFIG
# =========================
def garantir_config():
    default = {
        "categoria_analise": 0,
        "canal_aceitos": 0,
        "canal_recusados": 0,
        "canal_logs_adv": 0,
        "cargos": {},                 # cargo_id: meta
        "entregas_semana": {},        # user_id: dados
        "adv_ativos": {},             # user_id: motivo
        "historico_adv": {}           # user_id: lista
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
# VIEW DE ANÁLISE
# =========================
class AnaliseView(discord.ui.View):
    def __init__(self, dados):
        super().__init__(timeout=None)
        self.dados = dados

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        canal = interaction.guild.get_channel(cfg["canal_aceitos"])

        embed = discord.Embed(
            title="📦 ENTREGA ACEITA",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )

        for k, v in self.dados.items():
            embed.add_field(name=k, value=str(v), inline=False)

        msg = await canal.send(embed=embed)
        await interaction.channel.delete()

        await asyncio.sleep(86400)
        await msg.delete()

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        canal = interaction.guild.get_channel(cfg["canal_recusados"])

        embed = discord.Embed(
            title="❌ ENTREGA RECUSADA",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )

        for k, v in self.dados.items():
            embed.add_field(name=k, value=str(v), inline=False)

        msg = await canal.send(embed=embed)
        await interaction.channel.delete()

        await asyncio.sleep(36000)
        await msg.delete()


# =========================
# MODAIS ADV
# =========================
class AplicarADVModal(discord.ui.Modal, title="⚠️ Aplicar ADV"):
    usuario = discord.ui.TextInput(label="ID ou @usuário", required=True)
    motivo = discord.ui.TextInput(label="Motivo do ADV", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        uid = self.usuario.value.strip("<@!>")

        motivo = f"{self.motivo.value} — {datetime.now().strftime('%d/%m/%Y')}"

        cfg["adv_ativos"][uid] = motivo
        cfg["historico_adv"].setdefault(uid, []).append(motivo)
        salvar_config(cfg)

        canal = interaction.guild.get_channel(cfg["canal_logs_adv"])
        if canal:
            await canal.send(f"⚠️ ADV aplicado em <@{uid}>: {motivo}")

        await interaction.response.send_message("✅ ADV aplicado.", ephemeral=True)


class RemoverADVModal(discord.ui.Modal, title="♻️ Remover ADV"):
    usuario = discord.ui.TextInput(label="ID ou @usuário", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        uid = self.usuario.value.strip("<@!>")

        if uid in cfg["adv_ativos"]:
            del cfg["adv_ativos"][uid]
            cfg["historico_adv"].setdefault(uid, []).append(
                f"ADV removido manualmente — {datetime.now().strftime('%d/%m/%Y')}"
            )
            salvar_config(cfg)
            await interaction.response.send_message("♻️ ADV removido.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Usuário não possui ADV ativo.", ephemeral=True)


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
        cfg = garantir_config()
        uid = str(interaction.user.id)

        if uid in cfg["entregas_semana"]:
            return await interaction.response.send_message(
                "❌ Você já entregou nesta semana.",
                ephemeral=True
            )

        qtd = int(self.quantidade.value)

        if qtd >= self.meta:
            status = "✅ Meta CONCLUÍDA"
        elif qtd >= self.meta / 2:
            status = f"⚠️ Faltam {self.meta - qtd}"
        else:
            status = "❌ Menos da metade da meta"
            cfg["adv_ativos"][uid] = "Entregou menos da metade da meta"
            cfg["historico_adv"].setdefault(uid, []).append(cfg["adv_ativos"][uid])

        if uid in cfg["adv_ativos"] and qtd >= self.meta * 2:
            del cfg["adv_ativos"][uid]
            cfg["historico_adv"].setdefault(uid, []).append(
                "ADV removido por compensação (farm dobrado)"
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

        cfg["entregas_semana"][uid] = dados
        salvar_config(cfg)

        categoria = interaction.guild.get_channel(cfg["categoria_analise"])
        canal = await categoria.create_text_channel(f"entrega-{interaction.user.name}")

        embed = discord.Embed(title="📦 ENTREGA EM ANÁLISE", color=discord.Color.orange())
        for k, v in dados.items():
            embed.add_field(name=k, value=str(v), inline=False)

        await canal.send(embed=embed, view=AnaliseView(dados))
        await interaction.response.send_message("✅ Entrega enviada!", ephemeral=True)


# =========================
# PAINEL FARM
# =========================
class PainelFarmView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild
        self.cargo = None
        self.meta = None

        cfg = garantir_config()
        self.select.options.clear()

        for cid, meta in cfg["cargos"].items():
            role = guild.get_role(int(cid))
            if role:
                self.select.add_option(
                    label=role.name,
                    value=f"{role.name}|{meta}"
                )

    @discord.ui.select(placeholder="Selecione seu cargo")
    async def select(self, interaction: discord.Interaction, select):
        nome, meta = select.values[0].split("|")
        self.cargo = nome
        self.meta = int(meta)

        select.placeholder = "Selecione seu cargo"
        select.values.clear()

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="📦 Entregar Farm", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        if not self.cargo:
            return await interaction.response.send_message(
                "❌ Selecione um cargo.",
                ephemeral=True
            )

        await interaction.response.send_modal(
            EntregaModal(self.cargo, self.meta)
        )


# =========================
# PAINEL STAFF
# =========================
class PainelStaffView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📦 Ver Entregas", style=discord.ButtonStyle.blurple)
    async def ver_entregas(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        embed = discord.Embed(title="📦 ENTREGAS", color=discord.Color.blue())

        if not cfg["entregas_semana"]:
            embed.description = "Nenhuma entrega registrada."
        else:
            for d in cfg["entregas_semana"].values():
                embed.add_field(
                    name=d["👤 Quem entregou"],
                    value=f'{d["🎖 Cargo"]} | {d["📊 Status"]}',
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚠️ Ver ADV", style=discord.ButtonStyle.red)
    async def ver_adv(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        embed = discord.Embed(title="⚠️ HISTÓRICO DE ADV", color=discord.Color.red())

        if not cfg["historico_adv"]:
            embed.description = "Nenhum ADV registrado."
        else:
            for uid, lista in cfg["historico_adv"].items():
                embed.add_field(
                    name=f"Usuário {uid}",
                    value="\n".join(lista),
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="➕ Aplicar ADV", style=discord.ButtonStyle.gray)
    async def aplicar_adv(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(AplicarADVModal())

    @discord.ui.button(label="♻️ Remover ADV", style=discord.ButtonStyle.gray)
    async def remover_adv(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(RemoverADVModal())


# =========================
# COG
# =========================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop_semanal.start()

    @commands.command()
    async def painelfarm(self, ctx):
        embed = discord.Embed(
            title="📦 PAINEL DE FARM",
            description="Selecione seu cargo e entregue o farm",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=PainelFarmView(ctx.guild))

    @commands.command()
    async def painelstaff(self, ctx):
        embed = discord.Embed(
            title="📋 PAINEL STAFF",
            description="Gerenciamento de farm e ADV",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=PainelStaffView())

    @app_commands.command(name="addcargo")
    async def addcargo(self, interaction: discord.Interaction, cargo: discord.Role, meta: int):
        cfg = garantir_config()
        cfg["cargos"][str(cargo.id)] = meta
        salvar_config(cfg)
        await interaction.response.send_message("✅ Cargo adicionado ao painel.", ephemeral=True)

    @app_commands.command(name="configticketfarm")
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
        config = get_config()
        config["metas"] = {
            "aviãozinho": meta_aviao,
            "membro": meta_membro,
            "recrutador": meta_recrutador,
            "gerente": meta_gerente
        }
        config["categoria_analise"] = categoria_analise.id
        config["canal_aceitos"] = canal_aceitos.id
        config["canal_recusados"] = canal_recusados.id
        config["canal_logs_adv"] = canal_adv.id
        save_json(CONFIG_PATH, config)

        await interaction.response.send_message("Configuração salva!", ephemeral=True)

    @tasks.loop(hours=1)
    async def loop_semanal(self):
        cfg = garantir_config()
        agora = datetime.now()

        if agora.weekday() == 6 and agora.hour == 0:
            for uid in cfg["cargos"]:
                if uid not in cfg["entregas_semana"]:
                    cfg["adv_ativos"][uid] = "Não entregou farm na semana"
                    cfg["historico_adv"].setdefault(uid, []).append(cfg["adv_ativos"][uid])
            salvar_config(cfg)

        if agora.weekday() == 0 and agora.hour == 0:
            cfg["entregas_semana"] = {}
            cfg["adv_ativos"] = {}
            salvar_config(cfg)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()
    print("✅ Tickets carregado e sincronizado")