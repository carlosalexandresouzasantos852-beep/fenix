# =========================
# TICKETS.PY — SISTEMA FARM COMPLETO (ESTÁVEL + STAFF ADV)
# =========================

import os
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
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
        "cargos": {},               # cargo_id: meta
        "entregas_semana": {},      # user_id: dados
        "adv_ativos": {},           # user_id: motivo
        "historico_adv": {}         # user_id: lista
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
# VIEW ANALISE
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
            cfg["historico_adv"].setdefault(uid, []).append(
                f"{cfg['adv_ativos'][uid]} — {datetime.now().strftime('%d/%m/%Y')}"
            )

        dados = {
            "👤 Quem entregou": interaction.user.display_name,
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
        options = []

        for cid, meta in cfg["cargos"].items():
            role = guild.get_role(int(cid))
            if role:
                options.append(
                    discord.SelectOption(
                        label=role.name,
                        value=f"{role.id}:{meta}"
                    )
                )

        self.add_item(PainelSelect(options, self))
        self.add_item(EntregarButton(self))


class PainelSelect(discord.ui.Select):
    def __init__(self, options, parent):
        super().__init__(
            placeholder="Selecione seu cargo",
            options=options,
            min_values=1,
            max_values=1
        )
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        role_id, meta = self.values[0].split(":")
        role = interaction.guild.get_role(int(role_id))

        self.parent.cargo = role.name
        self.parent.meta = int(meta)

        await interaction.response.send_message(
            f"Cargo selecionado: **{role.name}** (Meta: {meta})",
            ephemeral=True
        )


class EntregarButton(discord.ui.Button):
    def __init__(self, parent):
        super().__init__(label="📦 Entregar Farm", style=discord.ButtonStyle.green)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        if not self.parent.cargo:
            return await interaction.response.send_message(
                "❌ Selecione um cargo.",
                ephemeral=True
            )

        await interaction.response.send_modal(
            EntregaModal(self.parent.cargo, self.parent.meta)
        )


# =========================
# MODAIS ADV STAFF
# =========================
class AplicarADVModal(discord.ui.Modal, title="⚠️ Aplicar ADV"):
    usuario = discord.ui.TextInput(label="ID ou @usuário", required=True)
    motivo = discord.ui.TextInput(label="Motivo", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        uid = self.usuario.value.strip("<@!>")

        nome = interaction.guild.get_member(int(uid)).display_name
        motivo = f"{self.motivo.value} — {datetime.now().strftime('%d/%m/%Y')}"

        cfg["adv_ativos"][uid] = motivo
        cfg["historico_adv"].setdefault(uid, []).append(motivo)
        salvar_config(cfg)

        await interaction.response.send_message(
            f"⚠️ ADV aplicado em **{nome}**.",
            ephemeral=True
        )


class RemoverADVModal(discord.ui.Modal, title="♻️ Remover ADV"):
    usuario = discord.ui.TextInput(label="ID ou @usuário", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        uid = self.usuario.value.strip("<@!>")

        if uid in cfg["adv_ativos"]:
            del cfg["adv_ativos"][uid]
            salvar_config(cfg)
            await interaction.response.send_message("♻️ ADV removido.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Usuário não tem ADV.", ephemeral=True)


# =========================
# PAINEL STAFF
# =========================
class PainelStaffView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📦 Ver Entregas", style=discord.ButtonStyle.blurple)
    async def ver_entregas(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        embed = discord.Embed(title="📦 ENTREGAS DA SEMANA", color=discord.Color.blue())

        if not cfg["entregas_semana"]:
            embed.description = "Nenhuma entrega registrada."
        else:
            for uid, d in cfg["entregas_semana"].items():
                embed.add_field(
                    name=d["👤 Quem entregou"],
                    value=f'{d["🎖 Cargo"]} | {d["📊 Status"]}',
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚠️ Ver ADV", style=discord.ButtonStyle.red)
    async def ver_adv(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        embed = discord.Embed(title="⚠️ ADVs", color=discord.Color.red())

        if not cfg["adv_ativos"]:
            embed.description = "Nenhum ADV ativo."
        else:
            for uid, motivo in cfg["adv_ativos"].items():
                member = interaction.guild.get_member(int(uid))
                nome = member.display_name if member else uid
                embed.add_field(name=nome, value=motivo, inline=False)

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


    @app_commands.command(name="addcargo")
    @app_commands.checks.has_permissions(administrator=True)
    async def addcargo(self, interaction: discord.Interaction, cargo: discord.Role, meta: int):
        cfg = garantir_config()
        cfg["cargos"][str(cargo.id)] = meta
        salvar_config(cfg)
        await interaction.response.send_message("✅ Cargo adicionado ao painel.", ephemeral=True)

    @tasks.loop(hours=1)
    async def loop_semanal(self):
        cfg = garantir_config()
        agora = datetime.now()

        # Domingo 00:00 — aplica ADV automático
        if agora.weekday() == 6 and agora.hour == 0:
            for uid in cfg["entregas_semana"]:
                pass

        # Segunda 00:00 — reset
        if agora.weekday() == 0 and agora.hour == 0:
            cfg["entregas_semana"] = {}
            cfg["adv_ativos"] = {}
            salvar_config(cfg)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()
    print("✅ Tickets carregado com sucesso")