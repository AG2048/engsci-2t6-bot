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
        log_message = str(datetime.datetime.now())
        embed = discord.Embed()
        embed.title = f'{self.user.name}{("#" + self.user.discriminator) if len(self.user.discriminator) > 1 else ""} (ID: {self.user.id})'
        log_message += f'\n\t {self.user.name}{("#" + self.user.discriminator) if len(self.user.discriminator) > 1 else ""} (ID: {self.user.id})'
        embed.timestamp = datetime.datetime.now()
        embed.set_author(name=self.user.name, icon_url=self.user.avatar.url)
        embed.description = 'Bot is ready.'
        log_message += '\n\t Bot is ready.'
        await self.get_channel(LOG_CHANNEL_ID).send(embed=embed)
        print(log_message)

    async def log(
            self,
            cog: commands.Cog,
            user: discord.User = None,
            user_action: str = None,
            channel: discord.TextChannel = None,
            event: str = None,
            outcome: str = None) -> None:
        """
        Logs an event to the log channel and prints it to the console.

        :param cog: the cog that called this function
        :param user: the user that triggered the event
        :param user_action: the action the user took
        :param channel: the channel the event occurred in
        :param event: the event that occurred
        :param outcome: the outcome of the event (only used for user actions or errors)
        :return: None
        """
        log_message = str(datetime.datetime.now())
        embed = discord.Embed()
        embed.title = f'{type(cog).__name__}'
        embed.timestamp = datetime.datetime.now()
        embed.set_author(name=self.user.name, icon_url=self.user.avatar.url)
        if user is not None:
            embed.add_field(name='User: ', value=f'{user.mention} ({user.id})')
            embed.set_footer(text=f'{user.name}{("#"+user.discriminator) if len(user.discriminator) > 1 else ""} ({user.id})', icon_url=user.avatar.url)
            log_message += f'\n\t User: {user.name}{("#"+user.discriminator) if len(user.discriminator) > 1 else ""} ({user.id})'
        if user_action is not None:
            embed.add_field(name='User Action: ', value=user_action)
            log_message += f'\n\t User Action: {user_action}'
        if channel is not None:
            embed.add_field(name='In Channel: ', value=f'{channel.mention} ({channel.id})')
            log_message += f'\n\t In Channel: {channel.name} ({channel.id})'
        if event is not None:
            embed.add_field(name='Event: ', value=event)
            log_message += f'\n\t Event: {event}'
        if outcome is not None:
            embed.add_field(name='Outcome: ', value=outcome)
            log_message += f'\n\t Outcome: {outcome}'
        await self.get_channel(LOG_CHANNEL_ID).send(embed=embed)
        print(log_message)


bot = Bot()
bot.run(DISCORD_BOT_TOKEN)