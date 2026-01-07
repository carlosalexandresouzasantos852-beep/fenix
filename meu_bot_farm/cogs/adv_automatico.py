import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, date

CONFIG = "meu_bot_farm/data/config_farm.json"
ENTREGAS = "meu_bot_farm/data/entregas.json"
ADVS = "meu_bot_farm/data/advs.json"
CONTROLE = "meu_bot_farm/data/controle_adv.json"


# ================== JSON ==================

def load(path, default):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ================== COG ==================

class AdvAutomatico(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verificar_adv.start()

    def cog_unload(self):
        self.verificar_adv.cancel()

    @tasks.loop(minutes=30)
    async def verificar_adv(self):
        hoje = date.today()

        # 6 = domingo
        if hoje.weekday() != 6:
            return

        controle = load(CONTROLE, {})
        ultimo_reset = controle.get("ultimo_reset")

        # trava para não rodar mais de uma vez no mesmo domingo
        if ultimo_reset == hoje.isoformat():
            return

        config = load(CONFIG, {})
        entregas = load(ENTREGAS, {})
        advs = load(ADVS, {})

        canal_adv_id = config.get("canal_adv")
        metas = config.get("metas", {})

        if not canal_adv_id or not metas:
            return

        for guild in self.bot.guilds:
            canal_adv = guild.get_channel(canal_adv_id)
            if not canal_adv:
                continue

            for member in guild.members:
                if member.bot:
                    continue

                cargo_valido = None
                for role in member.roles:
                    if role.name in metas:
                        cargo_valido = role.name
                        break

                if not cargo_valido:
                    continue

                meta = metas[cargo_valido]
                entregue = entregas.get(str(member.id), 0)

                if entregue < meta:
                    uid = str(member.id)
                    advs[uid] = advs.get(uid, 0) + 1

                    await canal_adv.send(
                        f"⚠️ **ADV AUTOMÁTICO APLICADO**\n"
                        f"👤 {member.mention}\n"
                        f"🏷 Cargo: **{cargo_valido}**\n"
                        f"📦 Entregou: **{entregue}**\n"
                        f"🎯 Meta: **{meta}**\n"
                        f"📛 Total ADV: **{advs[uid]}**"
                    )

            # 🔁 reset semanal
            save(ENTREGAS, {})
            save(ADVS, advs)

            controle["ultimo_reset"] = hoje.isoformat()
            save(CONTROLE, controle)

            await canal_adv.send("🔁 **Sistema de farm resetado para a nova semana.**")
            break

    @verificar_adv.before_loop
    async def before_verificar(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(AdvAutomatico(bot))