import discord
from discord.ext import commands
import json, os

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

class Metas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def meta_por_cargo(self, member, config):
        """
        Retorna a meta configurada para o cargo do membro.
        Retorna None se não houver meta configurada.
        """
        cargos = [r.name.lower() for r in member.roles]

        if "aviãozinho" in cargos:
            return config.get("meta_aviao")
        if "membro" in cargos:
            return config.get("meta_membro")
        if "recrutador" in cargos:
            return config.get("meta_recrutador")
        if "gerente" in cargos:
            return config.get("meta_gerente")
        return None

    @commands.command(name="entregar")
    async def entregar(self, ctx, quantidade: int):
        """
        Comando para registrar a entrega de farm.
        Atualiza entregas, remove ADV se meta cumprida, e envia mensagem.
        """
        config = load(CONFIG, {})
        entregas = load(ENTREGAS, {})
        advs = load(ADVS, {})

        meta = self.meta_por_cargo(ctx.author, config)
        if not meta:
            await ctx.send("❌ Seu cargo não possui meta configurada.")
            return

        uid = str(ctx.author.id)
        entregas[uid] = entregas.get(uid, 0) + quantidade

        msg = f"📦 Entrega registrada: **{quantidade}**\n🎯 Meta: **{meta}**"

        # Checa se meta foi cumprida
        if entregas[uid] >= meta:
            msg += "\n✅ Meta cumprida!"
            
            # Se entregou 2x a meta, remove 1 ADV
            if entregas[uid] >= meta * 2 and advs.get(uid, 0) > 0:
                advs[uid] -= 1
                msg += "\n🔁 1 ADV removido por compensação."

        save(ENTREGAS, entregas)
        save(ADVS, advs)

        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Metas(bot))