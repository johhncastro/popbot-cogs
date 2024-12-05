from .twitchnotifier import TwitchNotifier  # Import the main cog class

async def setup(bot):
    # Create an instance of your cog and add it to the bot
    await bot.add_cog(TwitchNotifier(bot))
