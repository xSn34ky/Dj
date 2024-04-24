import discord
from discord.ext import commands
import youtube_dl
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({"format": "bestaudio", "extractaudio": True, "audioformat": "mp3", "outtmpl": "%(extract)s.%(ext)s"}).extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else youtube_dl.utils.sanitize_filename(data['title'], None) + '.mp3'
        return cls(discord.FFmpegPCMAudio(filename), data=data)

@bot.command()
async def play(ctx, *, query):
    loop = asyncio.get_event_loop()
    async with ctx.typing():
        query_parts = query.split(' - ')
        if len(query_parts) == 1:
            # Search by song name only
            search_query = f'{query} lyrics'
        else:
            # Search by artist and song name
            artist, song = query_parts
            search_query = f'{artist} - {song} lyrics'
        ydl_opts = {"format": "bestaudio", "extractaudio": True, "audioformat": "mp3", "outtmpl": "%(extract)s.%(ext)s", "noplaylist": True, "default_search": "ytsearch"}
        try:
            data = await loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(ydl_opts).extract_info(search_query, download=False))
            if 'entries' in data:
                data = data['entries'][0]
            player = await YTDLSource.from_url(data['webpage_url'], loop=bot.loop)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            await ctx.send(f'Now playing: {player.title}')
        except youtube_dl.utils.DownloadError as e:
            await ctx.send(f'Error: {e}')

@bot.command()
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
    else:
        await ctx.send("I am not connected to a voice channel.")

bot.run("YOUR_TOKEN")
