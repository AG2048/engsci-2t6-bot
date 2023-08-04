import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import datetime

load_dotenv()
APPLICATION_ID = int(os.getenv('APPLICATION_ID'))
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
SERVER_ID = int(os.getenv('SERVER_ID'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=discord.Intents.all(),
            application_id=APPLICATION_ID)

    async def setup_hook(self):
        # directory is cogs/directoryname/filename.py
        for directory in os.listdir('./cogs'):
            if os.path.isdir(f'./cogs/{directory}'):
                for filename in os.listdir(f'./cogs/{directory}'):
                    if filename.endswith('.py'):
                        await self.load_extension(f'cogs.{directory}.{filename[:-3]}')

        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        await bot.tree.sync(guild=discord.Object(id=SERVER_ID))

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def log(self, cog: commands.Cog, message: str):
        print(f'{type(cog).__name__}: {message}')
        embed = discord.Embed(
            title=f'{type(cog).__name__}',
            description=message,
            timestamp=datetime.datetime.now())
        await self.get_channel(LOG_CHANNEL_ID).send(embed=embed)


bot = Bot()
bot.run(DISCORD_BOT_TOKEN)