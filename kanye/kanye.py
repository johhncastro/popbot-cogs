import discord
from redbot.core import commands
import aiohttp

class KanyeQuote(commands.Cog):
    """Fetch Kanye West quotes using the Kanye REST API."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kanye(self, ctx):
        """Get a Kanye West quote."""
        api_url = "https://api.kanye.rest/"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    quote = data.get("quote", "Could not fetch the quote.")
                    await ctx.send(f'Kanye says: "{quote}"')
                else:
                    await ctx.send("Sorry, I couldn't fetch a Kanye quote right now.")
