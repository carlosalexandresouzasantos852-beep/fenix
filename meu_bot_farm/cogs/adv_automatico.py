# meu_bot_farm/cogs/adv_automatico.py
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from meu_bot_farm.cogs.tickets import garantir_config, salvar_config  # <- alterado

class ADV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.adv_ativos = {}  # {"apelido": qtd}
        self.canal_adv_id = None
        self.canal_adv_obj = None
        self.reset_semana.start()

    async def cog_load(self):
        config = garantir_config()
        self.canal_adv_id = config.get("canal_adv")
        self.canal_adv_obj = self.bot.get_channel(self.canal_adv_id)

    # =========================
    # Aplica ADV (botão ou automação)
    # =========================
    def aplicar_adv(self, apelido: str, qtd: int = 1):
        """Aplica ADV para o jogador."""
        self.adv_ativos[apelido] = self.adv_ativos.get(apelido, 0) + qtd

    # =========================
    # Remove ADV manual
    # =========================
    def remover_adv(self, apelido: str):
        """Remove ADV manualmente."""
        if apelido in self.adv_ativos:
            del self.adv_ativos[apelido]

    # =========================
    # Lista todos ADV ativos
    # =========================
    def listar_adv(self):
        return self.adv_ativos

    # =========================
    # Envia lista de ADV ativos no canal de ADV
    # =========================
    async def enviar_adv_canal(self):
        if not self.canal_adv_obj:
            self.canal_adv_obj = self.bot.get_channel(self.canal_adv_id)
        if not self.canal_adv_obj:
            return

        await self.canal_adv_obj.purge()  # Limpa mensagens antigas
        if not self.adv_ativos:
            await self.canal_adv_obj.send("Nenhum ADV ativo no momento.")
            return

        mensagem = "**ADV da semana:**\n"
        for apelido, qtd in self.adv_ativos.items():
            mensagem += f"- {apelido} | ADV: {qtd}\n"
        await self.canal_adv_obj.send(mensagem)

    # =========================
    # Reset semanal do canal (somente mensagens)
    # =========================
    @tasks.loop(hours=24)
    async def reset_semana(self):
        """Reset diário para enviar ADV aos domingos 0h."""
        await self.bot.wait_until_ready()
        now = datetime.utcnow()
        if now.weekday() == 6 and now.hour == 0:  # Domingo 0h UTC
            await self.enviar_adv_canal()

    @reset_semana.before_loop
    async def before_reset(self):
        await self.bot.wait_until_ready()

# Setup
async def setup(bot):
    await bot.add_cog(ADV(bot))