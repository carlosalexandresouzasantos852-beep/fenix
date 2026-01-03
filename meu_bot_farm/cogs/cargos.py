import os
os.environ["DISCORD_DISABLE_VOICE"] = "1"

import discord
from discord.ext import commands

class Cargos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def subir(self, ctx):
        antigo = discord.utils.get(ctx.guild.roles, name="Aviãozinho")
        novo = discord.utils.get(ctx.guild.roles, name="Membro")

        if not antigo or not novo:
            await ctx.send("Cargos não encontrados.")
            return

        if antigo in ctx.author.roles:
            await ctx.author.remove_roles(antigo)
            await ctx.author.add_roles(novo)
            await ctx.send("Cargo atualizado automaticamente!")

async def setup(bot):
    await bot.add_cog(Cargos(bot))