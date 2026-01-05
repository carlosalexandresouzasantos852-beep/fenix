import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime

CONFIG = "meu_bot_farm/data/config_farm.json"
ENTREGAS = "meu_bot_farm/data/entregas.json"
ADVS = "meu_bot_farm/data/advs.json"


def load(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


class AdvAutomatico(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verificar_adv.start()

    def cog_unload(self):
        self.verificar_adv.cancel()

    @tasks.loop(minutes=60)
    async def verificar_adv(self):
        agora = datetime.now()

        # 6 = domingo
        if agora.weekday() != 6:
            return

        config = load(CONFIG, {})
        entregas = load(ENTREGAS, {})
        advs = load(ADVS, {})

        canal_adv_id = config.get("canal_adv")
        metas = config.get("metas", {})

        if not canal_adv_id:
            return

        for guild in self.bot.guilds:
            canal_adv = guild.get_channel(canal_adv_id)
            if not canal_adv:
                continue

            for member in guild.members:
                if member.bot:
                    continue

                # descobrir cargo válido
                cargo_membro = None
                for role in member.roles:
                    if role.name in metas:
                        cargo_membro = role.name
                        break

                if not cargo_membro:
                    continue

                meta = metas[cargo_membro]
                entregue = entregas.get(str(member.id), 0)

                if entregue < meta:
                    advs[str(member.id)] = advs.get(str(member.id), 0) + 1

                    await canal_adv.send(
                        f"⚠️ **ADV AUTOMÁTICO APLICADO**\n"
                        f"👤 {member.mention}\n"
                        f"🏷 Cargo: **{cargo_membro}**\n"
                        f"📦 Entregou: **{entregue}**\n"
                        f"🎯 Meta: **{meta}**\n"
                        f"📛 Total ADV: **{advs[str(member.id)]}**"
                    )

            # 🔥 zera entregas da semana
            save(ENTREGAS, {})
            save(ADVS, advs)

            await canal_adv.send("🔁 **Sistema resetado para nova semana de farm.**")
            break  # evita rodar mais de uma vez no mesmo domingo

    @verificar_adv.before_loop
    async def before_verificar(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(AdvAutomatico(bot))