import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from typing import Optional
import datetime


load_dotenv()
SERVER_ID = int(os.getenv('SERVER_ID'))


class MessageLoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        When bot is ready, check if the message logging directory exists, if not, create it.
        When creating any file or directory, perform the full logging process,
            with start time = datetime.datetime(1970, 1, 1)
        If the file or directory already exists, locate the most recent log file,
            and set start time to the time of the last log.
        We log messages in real time, but we only log message stats once per day.
        For message_stats, go through each channel and seek messages from the start time to the previous day.
            we record the number of messages, number of characters by each member in each channel. Record day by day.
            we record the total number + change since last day.
        For message logging, go through each channel and seek messages since last log.
            record each message + any attachment links.
        Any changes are appended to each respective log file immediately.
        """
        if not os.path.exists(os.path.join('..', 'data', 'logging', 'message_stats')):
            os.makedirs(os.path.join('..', 'data', 'logging', 'message_stats'))
        await self.bot.log(
            cog=self,
            user=None,
            user_action=None,
            channel=None,
            event='MessageLoggingCog is ready.',
            outcome=None)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        MessageLoggingCog(bot),
        guilds=[discord.Object(id=SERVER_ID)])