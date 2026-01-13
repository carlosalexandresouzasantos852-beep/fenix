# =========================
# TICKETS.PY — SISTEMA FARM FINAL FUNCIONAL
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
        "metas": {
            "aviãozinho": 0,
            "membro": 0,
            "recrutador": 0,
            "gerente": 0
        },
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

        # Bloqueio de entrega por semana
        if uid in cfg["entregas_semana"]:
            return await interaction.response.send_message(
                "❌ Você já realizou a entrega desta semana.",
                ephemeral=True
            )

        qtd = int(self.quantidade.value)

        # Avaliação da meta
        status = ""
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

        # ADV removido se entregou farm dobrado
        if uid in cfg["adv_ativos"] and qtd >= self.meta * 2:
            del cfg["adv_ativos"][uid]
            cfg["historico_adv"].setdefault(uid, []).append(
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

        cfg["entregas_semana"][uid] = dados
        salvar_config(cfg)

        categoria = interaction.guild.get_channel(cfg["categoria_analise"])
        canal = await categoria.create_text_channel(f"entrega-{interaction.user.name}")

        embed = discord.Embed(title="📦 ENTREGA EM ANÁLISE", color=discord.Color.orange())
        for k, v in dados.items():
            embed.add_field(name=k, value=str(v), inline=False)

        # Botões aceitar/recusar
        view = AnaliseView(uid, dados, canal.id)
        await canal.send(embed=embed, view=view)

        await interaction.response.send_message(
            "✅ Sua entrega foi enviada para análise.", ephemeral=True
        )
        await asyncio.sleep(5)
        await interaction.delete_original_response()


# =========================
# PAINEL DE ANÁLISE — Aceitar / Recusar
# =========================
class AnaliseView(discord.ui.View):
    def __init__(self, uid, dados, canal_id):
        super().__init__(timeout=None)
        self.uid = uid
        self.dados = dados
        self.canal_id = canal_id

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.green)
    async def aceitar(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        canal_aceitos = interaction.guild.get_channel(cfg["canal_aceitos"])

        embed = discord.Embed(title="📦 ENTREGA ACEITA", color=discord.Color.green())
        for k, v in self.dados.items():
            embed.add_field(name=k, value=str(v), inline=False)

        msg = await canal_aceitos.send(embed=embed)
        await msg.pin()

        # Deleta o canal temporário
        canal_temp = interaction.guild.get_channel(self.canal_id)
        if canal_temp:
            await canal_temp.delete()

        await interaction.response.send_message("✅ Entrega aceita!", ephemeral=True)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.red)
    async def recusar(self, interaction: discord.Interaction, _):
        cfg = garantir_config()
        canal_recusados = interaction.guild.get_channel(cfg["canal_recusados"])

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
# MODAIS ADV
# =========================
class AplicarAdvModal(discord.ui.Modal, title="➕ Aplicar ADV"):
    usuario = discord.ui.TextInput(label="Nome ou ID do usuário", required=True)
    motivo = discord.ui.TextInput(label="Motivo do ADV", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        uid = self.usuario.value
        cfg["adv_ativos"][uid] = self.motivo.value
        cfg["historico_adv"].setdefault(uid, []).append(
            f"{self.motivo.value} — aplicado pelo bot — {datetime.now().strftime('%d/%m/%Y')}"
        )
        salvar_config(cfg)
        await interaction.response.send_message(f"✅ ADV aplicado para {uid}", ephemeral=True)


class RemoverAdvModal(discord.ui.Modal, title="➖ Remover ADV"):
    usuario = discord.ui.TextInput(label="Nome ou ID do usuário", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        cfg = garantir_config()
        uid = self.usuario.value
        if uid in cfg["adv_ativos"]:
            del cfg["adv_ativos"][uid]
            salvar_config(cfg)
            await interaction.response.send_message(f"✅ ADV removido para {uid}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Nenhum ADV encontrado para {uid}", ephemeral=True)


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
        cfg = garantir_config()
        options = [
            discord.SelectOption(label=nome, value=nome)
            for nome in cfg["metas"].keys()
        ]
        super().__init__(placeholder="Selecione seu cargo", options=options)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        cfg = garantir_config()
        cargo = self.values[0]
        self.parent.cargo = cargo
        self.parent.meta = cfg["metas"][cargo]

        await interaction.response.send_message(f"✅ Cargo selecionado: {cargo}", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.delete_original_response()


class EntregarButton(discord.ui.Button):
    def __init__(self, parent):
        super().__init__(label="📦 Entregar Farm", style=discord.ButtonStyle.green)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        if not self.parent.cargo:
            return await interaction.response.send_message(
                "❌ Selecione o cargo antes de entregar.", ephemeral=True
            )

        await interaction.response.send_modal(
            EntregaModal(self.parent.cargo, self.parent.meta)
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
        embed = discord.Embed(title="⚠️ HISTÓRICO DE ADV", color=discord.Color.red())

        if not cfg["historico_adv"]:
            embed.description = "Nenhum ADV registrado."
        else:
            for uid, lista in cfg["historico_adv"].items():
                embed.add_field(name=uid, value="\n".join(lista), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="➕ Aplicar ADV", style=discord.ButtonStyle.green)
    async def aplicar_adv(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(AplicarAdvModal())

    @discord.ui.button(label="➖ Remover ADV", style=discord.ButtonStyle.gray)
    async def remover_adv(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(RemoverAdvModal())



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

    @app_commands.command(name="configticketfarm")
    @app_commands.checks.has_permissions(administrator=True)
    async def configticketfarm(
        self, interaction: discord.Interaction,
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
        await interaction.response.send_message("✅ Configuração do farm salva com sucesso.", ephemeral=True)

    @app_commands.command(name="addcargo")
    @app_commands.checks.has_permissions(administrator=True)
    async def addcargo(self, interaction: discord.Interaction, cargo: discord.Role, meta: int):
        cfg = garantir_config()
        cfg["metas"][cargo.name] = meta
        salvar_config(cfg)
        await interaction.response.send_message(f"✅ Cargo `{cargo.name}` adicionado com meta `{meta}` ao Painel Farm.", ephemeral=True)

    # =========================
    # LOOP ADV AUTOMÁTICO
    # =========================
    @tasks.loop(minutes=1)
    async def loop_adv(self):
        cfg = garantir_config()
        agora = datetime.now()
        canal_adv = self.bot.get_channel(cfg["canal_logs_adv"])

        # AVISO 1H ANTES
        if cfg["adv_agendado"]["ativo"]:
            alvo = agora.replace(hour=cfg["adv_agendado"]["hora"], minute=cfg["adv_agendado"]["minuto"], second=0)
            dias = (cfg["adv_agendado"]["weekday"] - agora.weekday()) % 7
            alvo += timedelta(days=dias)

            if 0 <= (alvo - agora).total_seconds() <= 3600 and not cfg["adv_agendado"]["aviso_1h"]:
                if canal_adv:
                    await canal_adv.send("⚠️ ADV automático será aplicado em **1 hora**.")
                cfg["adv_agendado"]["aviso_1h"] = True
                salvar_config(cfg)

            # EXECUTA ADV
            if agora >= alvo:
                guild = self.bot.get_guild(canal_adv.guild.id if canal_adv else 0)
                if guild:
                    cargos_validos = set(cfg["metas"].keys())
                    for member in guild.members:
                        if not any(r.name in cargos_validos for r in member.roles):
                            continue
                        uid = str(member.id)
                        if uid not in cfg["entregas_semana"]:
                            cfg["adv_ativos"][uid] = "Não entregou farm"
                            cfg["historico_adv"].setdefault(uid, []).append(
                                f"ADV automático — {datetime.now().strftime('%d/%m/%Y')} (bot)"
                            )
                    if canal_adv:
                        embed = discord.Embed(title="⚠️ ADV AUTOMÁTICO", color=discord.Color.red())
                        for uid, motivo in cfg["adv_ativos"].items():
                            membro = guild.get_member(int(uid))
                            nome = membro.display_name if membro else f"Usuário {uid}"
                            embed.add_field(name=nome, value=motivo, inline=False)
                        await canal_adv.send(embed=embed)
                cfg["adv_agendado"]["aviso_1h"] = False
                salvar_config(cfg)

    # =========================
    # RESET SEMANAL SEGUNDA 00:00
    # =========================
    @tasks.loop(minutes=5)
    async def loop_reset(self):
        cfg = garantir_config()
        agora = datetime.now()
        if agora.weekday() == 0 and agora.hour == 0:
            cfg["entregas_semana"] = {}
            cfg["adv_agendado"]["aviso_1h"] = False
            salvar_config(cfg)


# =========================
# SETUP
# =========================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()
    print("✅ Tickets carregado e sincronizado")