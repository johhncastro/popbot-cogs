from .kanye import KanyeQuote

async def setup(bot):
    await bot.add_cog(KanyeQuote(bot))
