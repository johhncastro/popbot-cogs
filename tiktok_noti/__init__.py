from .tiktok import TikTok

async def setup(bot):
    await bot.add_cog(TikTok(bot))
