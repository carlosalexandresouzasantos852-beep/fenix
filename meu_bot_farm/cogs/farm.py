import discord, json, os
from discord.ext import commands, tasks
from datetime import datetime

PASTA = "meu_bot_farm/data"
ENTREGAS = f"{PASTA}/entregas.json"
ADVS = f"{PASTA}/advs.json"
CONFIG = f"{PASTA}/config_farm.json"

MAX_ADV = 5  # Máximo de ADV antes do kick

os.makedirs(PASTA, exist_ok=True)

# ----------------- UTIL -----------------
def load(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ----------------- COG -----------------
class FarmAuto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.analise.start()
        self.reset_semanal.start()

    # ----------------- ADV AUTOMÁTICO -----------------
    @tasks.loop(hours=24)
    async def analise(self):
        if datetime.now().weekday() != 6:  # DOMINGO
            return

        entregas = load(ENTREGAS, {})
        advs = load(ADVS, {})
        cfg = load(CONFIG, {})

        for guild in self.bot.guilds:
            canal_adv = guild.get_channel(cfg.get("canal_adv"))

            for member in guild.members:
                if member.bot:
                    continue

                # Meta configurada para o cargo do membro
                cargos = [r.name.lower() for r in member.roles]
                meta = None
                if "aviãozinho" in cargos:
                    meta = cfg.get("meta_aviao", 0)
                elif "membro" in cargos:
                    meta = cfg.get("meta_membro", 0)
                elif "recrutador" in cargos:
                    meta = cfg.get("meta_recrutador", 0)
                elif "gerente" in cargos:
                    meta = cfg.get("meta_gerente", 0)

                if not meta:
                    continue  # não aplica ADV se não houver meta

                qtd_entrega = entregas.get(str(member.id), 0)
                if qtd_entrega < meta:
                    advs[str(member.id)] = advs.get(str(member.id), 0) + 1
                    if canal_adv:
                        await canal_adv.send(
                            f"⚠️ ADV automático aplicado em {member.mention} (Meta não atingida)"
                        )

                    if advs[str(member.id)] >= MAX_ADV:
                        try:
                            await member.kick(reason="5 ADV acumulados (automático)")
                        except:
                            if canal_adv:
                                await canal_adv.send(f"❌ Não foi possível kickar {member.mention}")

        save(ADVS, advs)

    # ----------------- RESET SEMANAL -----------------
    @tasks.loop(hours=24)
    async def reset_semanal(self):
        if datetime.now().weekday() != 0:  # SEGUNDA
            return

        save(ENTREGAS, {})
        cfg = load(CONFIG, {})
        for guild in self.bot.guilds:
            canal_adv = guild.get_channel(cfg.get("canal_adv"))
            if canal_adv:
                await canal_adv.send("🔄 Reset semanal de entregas realizado.")

# ----------------- SETUP -----------------
async def setup(bot):
    await bot.add_cog(FarmAuto(bot))