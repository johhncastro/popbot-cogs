import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redbot.core import commands, Config, checks

class TwitchNotifier(commands.Cog):
    """Notifies when Twitch streamers go live."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {"streamers": {}, "channel_ids": []}  # Store list of channels
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.scheduler.add_job(self.check_streamers, "interval", minutes=5)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())
        self.scheduler.shutdown()

    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @commands.group()
    async def twitchnotifier(self, ctx):
        """Manage Twitch notifications."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @twitchnotifier.command()
    async def setchannel(self, ctx, *channel_ids: int):
        """Set the channels for notifications."""
        await self.config.guild(ctx.guild).channel_ids.set(list(channel_ids))
        channels = ", ".join([f"<#{channel_id}>" for channel_id in channel_ids])
        await ctx.send(f"Notification channels set to {channels}.")

    @twitchnotifier.command()
    async def addstreamer(self, ctx, streamer_name: str):
        """Add a streamer to the notification list."""
        streamers = await self.config.guild(ctx.guild).streamers()
        if streamer_name in streamers:
            await ctx.send(f"{streamer_name} is already in the notification list.")
            return
        streamers[streamer_name] = False  # False indicates not live
        await self.config.guild(ctx.guild).streamers.set(streamers)
        await ctx.send(f"Added {streamer_name} to the notification list.")

    @twitchnotifier.command()
    async def removestreamer(self, ctx, streamer_name: str):
        """Remove a streamer from the notification list."""
        streamers = await self.config.guild(ctx.guild).streamers()
        if streamer_name not in streamers:
            await ctx.send(f"{streamer_name} is not in the notification list.")
            return
        del streamers[streamer_name]
        await self.config.guild(ctx.guild).streamers.set(streamers)
        await ctx.send(f"Removed {streamer_name} from the notification list.")

    @twitchnotifier.command()
    async def listchannels(self, ctx):
        """List all channels set for notifications."""
        channel_ids = await self.config.guild(ctx.guild).channel_ids()
        if not channel_ids:
            await ctx.send("No channels have been set for notifications.")
            return
        channels = ", ".join([f"<#{channel_id}>" for channel_id in channel_ids])
        await ctx.send(f"Notification channels: {channels}")

    @twitchnotifier.command()
    async def removechannel(self, ctx, channel_id: int):
        """Remove a channel from the notification list."""
        channel_ids = await self.config.guild(ctx.guild).channel_ids()
        if channel_id not in channel_ids:
            await ctx.send(f"Channel <#{channel_id}> is not in the notification list.")
            return
        channel_ids.remove(channel_id)
        await self.config.guild(ctx.guild).channel_ids.set(channel_ids)
        await ctx.send(f"Removed <#{channel_id}> from the notification list.")

    async def check_streamers(self):
        """Check if streamers are live."""
        for guild in self.bot.guilds:
            data = await self.config.guild(guild).all()
            streamers = data["streamers"]
            channel_ids = data["channel_ids"]

            if not channel_ids:
                continue

            live_streamers = await self.get_live_streamers(list(streamers.keys()))
            for streamer, is_live in streamers.items():
                if streamer in live_streamers and not is_live:
                    # Notify all channels
                    for channel_id in channel_ids:
                        channel = guild.get_channel(channel_id)
                        if channel:
                            await channel.send(f"{streamer} is now live on Twitch! Check them out: https://twitch.tv/{streamer}")
                    streamers[streamer] = True
                elif streamer not in live_streamers and is_live:
                    streamers[streamer] = False
            await self.config.guild(guild).streamers.set(streamers)

    async def get_live_streamers(self, streamer_names):
        """Get live streamers from Twitch."""
        client_id = "4f7vkp3vtrbad79bxxdrm0ut22vcfr"
        client_secret = "gmj9gobx1ew9dwjs26afifd31gj2rh"
        token_url = "https://id.twitch.tv/oauth2/token"
        streams_url = "https://api.twitch.tv/helix/streams"

        # Get OAuth token
        async with self.session.post(
            token_url,
            params={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
        ) as resp:
            token_data = await resp.json()
            access_token = token_data["access_token"]

        # Check live streamers
        headers = {
            "Client-ID": client_id,
            "Authorization": f"Bearer {access_token}",
        }
        async with self.session.get(
            streams_url,
            params={"user_login": streamer_names},
            headers=headers
        ) as resp:
            data = await resp.json()
            return [stream["user_login"] for stream in data.get("data", [])]
