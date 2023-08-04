import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from typing import Optional


load_dotenv()
SERVER_ID = int(os.getenv('SERVER_ID'))
ADMINISTRATION_ROLES_IDS = [int(role_id) for role_id in os.getenv('ADMINISTRATION_ROLES_IDS').split(',')]


class TestingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.bot.user:
            return
        if message.content == 'testing_ping':
            await message.channel.send('testing_pong')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.member == self.bot.user:
            return
        print(payload.emoji.name)

    @app_commands.command(
        name='app_command_name',
        description='app_command_description')
    @app_commands.describe(
        value_string="description of value_string",
        value_int="description of value_int",
        value_role="description of value_role",
        value_user="description of value_user",
        value_channel="description of value_channel",
        value_string_options="description of value_string_options",
        optional_input="description of optional_input")
    @app_commands.choices(
        value_string_options=[
            Choice(name="choice_name_1", value="choice_value_1"),
            Choice(name="choice_name_2", value="choice_value_2"),
            Choice(name="choice_name_3", value="choice_value_3")])
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def app_command_name(
            self,
            interaction: discord.Interaction,
            value_string: str,
            value_int: int,
            value_role: discord.Role,
            value_user: discord.User,
            value_channel: discord.TextChannel,
            value_string_options: str,
            optional_input: Optional[str] = None) -> None:
        await interaction.response.send_message(
            f"Value string: {value_string}\nValue int: {value_int}\nValue role: {value_role}\nValue user: {value_user}\nValue channel: {value_channel}\nValue string options: {value_string_options}\nOptional input: {optional_input}")
        # To send multiple messages:
        #    await interaction.followup.defer()
        #    await interaction.followup.send("Message 1")
        #    await interaction.followup.send("Message 2")
        # To edit the original message:
        #    await interaction.response.edit_original_message(content="New content")
        # to edit second message:
        #    msg2 = await interaction.followup.send("Message 2")
        #    await msg2.edit(content="New content")
        # to add reaction:
        #    await msg2.add_reaction("👍")

    @app_command_name.error
    async def app_command_nameError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message("Missing role/permission", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        TestingCog(bot),
        guilds=[discord.Object(id=SERVER_ID)])