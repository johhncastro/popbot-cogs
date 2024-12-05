import discord
from redbot.core import commands
import aiohttp
import json
import time
from urllib.parse import urlencode

class TikTok(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client_key = "TIKTOK_CLIENT_KEY"
        self.client_secret = "TIKTOK_CLIENT_SECRET"
        self.redirect_uri = "http://localhost:5000/callback"
        self.access_token = None
        self.token_expiry = 0
        self.tiktok_users = []
        self.discord_channels = []

    async def generate_auth_url(self):
        # Generate the TikTok OAuth 2.0 authorization URL
        params = {
            'client_key': self.client_key,
            'response_type': 'code',
            'scope': 'user.info.basic video.list',
            'redirect_uri': self.redirect_uri,
            'state': 'random_string',  # Change this to a random string for security
        }
        auth_url = "https://www.tiktok.com/v2/auth/authorize/?" + urlencode(params)
        return auth_url

    async def fetch_access_token(self, auth_code):
        # Exchange the authorization code for an access token
        url = 'https://open.tiktokapis.com/v2/oauth/token/'
        payload = {
            'client_key': self.client_key,
            'client_secret': self.client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get('data', {}).get('access_token')
                    self.token_expiry = time.time() + data.get('data', {}).get('expires_in', 0) - 60
                    return self.access_token
                else:
                    raise Exception(f"Failed to fetch access token: {await response.text()}")

    async def refresh_access_token(self, refresh_token):
        # Refresh the access token using the refresh token
        url = 'https://open.tiktokapis.com/v2/oauth/token/'
        payload = {
            'client_key': self.client_key,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get('data', {}).get('access_token')
                    self.token_expiry = time.time() + data.get('data', {}).get('expires_in', 0) - 60
                    return self.access_token
                else:
                    raise Exception(f"Failed to refresh access token: {await response.text()}")

    async def fetch_latest_post(self, username):
        # Fetch the latest post for the TikTok user
        if self.access_token is None or time.time() > self.token_expiry:
            raise Exception("Access token is missing or expired.")
        
        url = f'https://open.tiktokapis.com/v2/video/list/'
        params = {'access_token': self.access_token, 'username': username, 'count': 1}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('data'):
                        latest_post = data['data'][0]
                        return latest_post['share_url']
                    else:
                        raise Exception("No posts found for this user.")
                else:
                    raise Exception(f"Failed to fetch posts: {await response.text()}")

    @commands.command()
    async def addtiktokuser(self, ctx, username: str):
        """Add a TikTok username to the watch list."""
        if username not in self.tiktok_users:
            self.tiktok_users.append(username)
            await ctx.send(f"Added {username} to the TikTok watch list.")
        else:
            await ctx.send(f"{username} is already in the list.")

    @commands.command()
    async def removetiktokuser(self, ctx, username: str):
        """Remove a TikTok username from the watch list."""
        if username in self.tiktok_users:
            self.tiktok_users.remove(username)
            await ctx.send(f"Removed {username} from the TikTok watch list.")
        else:
            await ctx.send(f"{username} is not in the list.")

    @commands.command()
    async def adddiscordchannel(self, ctx, channel: discord.TextChannel):
        """Add a Discord channel to receive TikTok notifications."""
        if channel.id not in [ch.id for ch in self.discord_channels]:
            self.discord_channels.append(channel)
            await ctx.send(f"Added {channel.name} to the notification list.")
        else:
            await ctx.send(f"{channel.name} is already in the list.")

    @commands.command()
    async def removediscordchannel(self, ctx, channel: discord.TextChannel):
        """Remove a Discord channel from receiving TikTok notifications."""
        if channel.id in [ch.id for ch in self.discord_channels]:
            self.discord_channels = [ch for ch in self.discord_channels if ch.id != channel.id]
            await ctx.send(f"Removed {channel.name} from the notification list.")
        else:
            await ctx.send(f"{channel.name} is not in the list.")

    @commands.command()
    async def showlists(self, ctx):
        """Show the TikTok user list and Discord channel list."""
        user_list = ", ".join(self.tiktok_users) if self.tiktok_users else "No users added."
        channel_list = ", ".join([channel.name for channel in self.discord_channels]) if self.discord_channels else "No channels added."
        await ctx.send(f"TikTok Users: {user_list}\nDiscord Channels: {channel_list}")

    @commands.command()
    async def tiktokauth(self, ctx):
        """Generate the OAuth URL for TikTok authorization."""
        auth_url = await self.generate_auth_url()
        await ctx.send(f"Click the link to authorize the bot: {auth_url}")
