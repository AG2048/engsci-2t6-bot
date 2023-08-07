import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from typing import Optional, List
import datetime
import csv


load_dotenv()
SERVER_ID = int(os.getenv('SERVER_ID'))
ADMINISTRATION_ROLES_IDS = [int(role_id) for role_id in os.getenv('ADMINISTRATION_ROLES_IDS').split(',')]
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))

class ServerRulesCog(commands.GroupCog, name='rules'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()  # this is required for the group cog to work
        self.moderation_dir = None
        self.server_rules_csv_full_path = None
        self.server_has_rule = False
        self.server_rule_channel_id = None
        self.server_rule_message_id = None
        self.server_rule_message_content = 'none'
        self.server_rule_message_embeds_info_dict_list = []
        self.colour_dict = {
            'blue': discord.Colour.blue(),
            'blurple': discord.Colour.blurple(),
            'brand_green': discord.Colour.brand_green(),
            'brand_red': discord.Colour.brand_red(),
            'dark_blue': discord.Colour.dark_blue(),
            'dark_embed': discord.Colour.dark_embed(),
            'dark_gold': discord.Colour.dark_gold(),
            'dark_gray': discord.Colour.dark_gray(),
            'dark_green': discord.Colour.dark_green(),
            'dark_grey': discord.Colour.dark_grey(),
            'dark_magenta': discord.Colour.dark_magenta(),
            'dark_orange': discord.Colour.dark_orange(),
            'dark_purple': discord.Colour.dark_purple(),
            'dark_red': discord.Colour.dark_red(),
            'dark_teal': discord.Colour.dark_teal(),
            'dark_theme': discord.Colour.dark_theme(),
            'darker_gray': discord.Colour.darker_gray(),
            'darker_grey': discord.Colour.darker_grey(),
            'default': discord.Colour.default(),
            'fuchsia': discord.Colour.fuchsia(),
            'gold': discord.Colour.gold(),
            'green': discord.Colour.green(),
            'greyple': discord.Colour.greyple(),
            'light_embed': discord.Colour.light_embed(),
            'light_gray': discord.Colour.light_gray(),
            'light_grey': discord.Colour.light_grey(),
            'lighter_gray': discord.Colour.lighter_gray(),
            'lighter_grey': discord.Colour.lighter_grey(),
            'magenta': discord.Colour.magenta(),
            'og_blurple': discord.Colour.blurple(),
            'orange': discord.Colour.orange(),
            'pink': discord.Colour.pink(),
            'purple': discord.Colour.purple(),
            'random': discord.Colour.random(),
            'red': discord.Colour.red(),
            'teal': discord.Colour.teal(),
            'yellow': discord.Colour.yellow(),
            'none': None
        }

    @commands.Cog.listener()
    async def on_ready(self):
        """
        When bot is ready, check if server rules file exists.
        If the file does not exist, create one, but with empty values.
        Then load the server rules from the file
            - channel_id, message_id
            - message_content
            - embeds (title, description, thumbnail_url, colour, fields (name and value))
        We will enforce everything to be 'none' except for colour and thumbnail_url.
            When storing the values, we will store them as '' in the csv if they are None.
            So that next time we load, they will be converted to 'none' (except for colour and thumbnail_url)
            Ensure we don't add an empty "embed_field_name," and "embed_field_value," to the csv file.
                As this creates an empty "none, none" field when reading the csv file.
        Check if the message exists in the channel and if the author is the bot.
            If any is false, mark the server doesn't have rules yet. (but we don't delete the existing rules info)
        If all is true, mark the server has rules.
        """

        """
        The server rules file is a csv file with the following format:
        value_name,value
        channel_id,123456789012345678
        message_id,123456789012345678
        message_content,This is the message content
        embed_title,This is the embed title
        embed_description,This is the embed description
        embed_thumbnail_url,https://example.com/image.png
        embed_colour,0x000000
        embed_field_name,This is the field name
        embed_field_value,This is the field value
        embed_field_name,This is another field name
        embed_field_value,This is another field value
        embed_title,This is another embed title
        embed_description,
        embed_thumbnail_url,
        embed_colour,
        embed_field_name,This is the field name
        embed_field_value,
        
        Any values that are empty will be set to None, except for the message_content, which will be set to 'none'
        """

        # Get the current directory and the moderation directory
        curr_dir = os.path.abspath(os.path.dirname(__file__))
        self.moderation_dir = os.path.join(curr_dir, '..', '..', 'data', 'moderation')
        self.server_rules_csv_full_path = os.path.join(self.moderation_dir, 'server_rules.csv')

        # Check if the server rules file exists
        if not os.path.isfile(self.server_rules_csv_full_path):
            # File does not exist
            os.makedirs(self.moderation_dir, exist_ok=True)
            # Create a new file with only the headers
            with open(self.server_rules_csv_full_path, 'w') as file:
                file.write('value_name,value\n')

        # Load the server rules from the file
        with open(self.server_rules_csv_full_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[0] == 'channel_id':
                    self.server_rule_channel_id = int(row[1]) if len(row[1]) > 0 else None
                elif row[0] == 'message_id':
                    self.server_rule_message_id = int(row[1]) if len(row[1]) > 0 else None
                elif row[0] == 'message_content':
                    self.server_rule_message_content = row[1] if len(row[1]) > 0 else 'none'
                elif row[0] == 'embed_title':
                    # An embed_title field indicates a new embed, even if it's empty
                    self.server_rule_message_embeds_info_dict_list.append({
                        'title': row[1] if len(row[1]) > 0 else "none",
                        'description': 'none',
                        'thumbnail_url': None,
                        'colour': None,
                        'fields': []
                    })
                elif row[0] == 'embed_description':
                    self.server_rule_message_embeds_info_dict_list[-1]['description'] = row[1] if len(row[1]) > 0 else 'none'
                elif row[0] == 'embed_thumbnail_url':
                    self.server_rule_message_embeds_info_dict_list[-1]['thumbnail_url'] = row[1] if len(row[1]) > 0 else None
                elif row[0] == 'embed_colour':
                    # Colours are all stored as hex strings, so we need to convert them to discord.Colour objects
                    # We can later do this by discord.Colour.from_str(hex_string)
                    # Do note that None is a valid colour, so we need to check for that
                    self.server_rule_message_embeds_info_dict_list[-1]['colour'] = row[1] if len(row[1]) > 0 else None
                elif row[0] == 'embed_field_name':
                    self.server_rule_message_embeds_info_dict_list[-1]['fields'].append({
                        'name': row[1] if len(row[1]) > 0 else 'none',
                        'value': 'none'
                    })
                elif row[0] == 'embed_field_value':
                    self.server_rule_message_embeds_info_dict_list[-1]['fields'][-1]['value'] = row[1] if len(row[1]) > 0 else 'none'

        # New update: We now enforce title to be "none" if it's empty

        # Check if the file has the channel_id and message_id
        if self.server_rule_channel_id and self.server_rule_message_id:
            # Check if the channel AND message exists in the server using try-except
            try:
                channel = self.bot.get_channel(self.server_rule_channel_id)
                if channel is not None:
                    message = await channel.fetch_message(self.server_rule_message_id)
                    if message is not None and message.author == self.bot.user:
                        # Message exists and is by the bot
                        self.server_has_rule = True
            except discord.errors.NotFound:
                # Channel or message does not exist
                pass
        print('ServerRulesCog is ready.')

    @app_commands.command(
        name='set_rules_to_existing_message',
        description='Set an existing message sent by the bot as the server rules message.')
    @app_commands.describe(
        channel='The channel where the message is located.',
        message_id='The message ID of the message to be set as the server rules message.',
        set_action='Whether to use this message as the server rules or to overwrite this message with existing server rules stored in the bot.')
    @app_commands.choices(
        set_action=[
            Choice(name="Use This Message As Rules (bot logs cached rules)", value="this_message"),
            Choice(name="Overwrite This Message And Use Stored Rules", value="overwrite")])
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def set_rules_to_existing_message(
            self,
            interaction: discord.Interaction,
            channel: discord.TextChannel,
            message_id: str,
            set_action: str) -> None:
        """
        Convert the message_id to an integer, since app_command doesn't recognize integers that long.
            Check if the message_id is a valid integer. If not, send an error message.
        Find the message object using the channel and message_id.
            Check if the message exists in the given channel. If not, send an error message.
            Check if the message is sent by the bot. If not, send an error message.
        Set server has rule to True.
        If set_action is 'this_message', set the message as the server rules message.
            We first log the existing server rules in the log channel, as this will overwrite the existing server rules.
                The log sends: "**Server Rules Changed**" and footer: "Before update by {author} at {time}"
            Save all contents of the message (ids, content, embeds) to memory.
            No need to add footer to indicate last updated, as this message itself is not changed by this action.
            Send a success message.
        If set_action is 'overwrite', overwrite the message with the server rules message.
            No need to log the existing server rules, as we are overwriting the message with the existing server rules.
            Load the server rules embeds from memory.
            Edit/Overwrite the message with the server rules message.
            Send a success message.
        Write to the server_rules file in the correct format, since both actions will change something:
            channel_id and message_id, and/or the embeds.
        """

        # Check if message_id is a valid integer
        try:
            message_id = int(message_id)
        except ValueError:
            await interaction.response.send_message('Message ID is not a valid integer.', ephemeral=True)
            return

        # Check if message exists in the channel
        try:
            message = await channel.fetch_message(message_id)

            # Check if message is sent by the bot
            if message.author != self.bot.user:
                await interaction.response.send_message('Message is not sent by the bot.', ephemeral=True)
                return
        except discord.errors.NotFound:
            await interaction.response.send_message('Message does not exist in the channel.', ephemeral=True)
            return

        if set_action == 'this_message':
            # If set_action is 'this_message', set the message and its contents as the server rules message

            if self.server_has_rule:
                # Log previous rules message in the log channel, only if the server previously has rules
                previous_rules_embeds = []
                for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
                    embed = discord.Embed()
                    embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
                    embed.title = embed_info_dict['title']
                    embed.description = embed_info_dict['description']
                    embed.set_thumbnail(url=embed_info_dict['thumbnail_url'])
                    # Colour is a hex string, so we convert it to a discord.Colour object. If it is None, we set it to None.
                    embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict['colour'] else None
                    for field in embed_info_dict['fields']:
                        embed.add_field(name=field['name'], value=field['value'], inline=False)
                    embed.set_footer(
                        # This tells us who updated the rules and when
                        text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")} at ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
                    embed.timestamp = datetime.datetime.now()
                    previous_rules_embeds.append(embed)
                log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
                # Send log message, mention it is a rule change.
                await log_channel.send(content=f'**Server Rule Changed:**\n{self.server_rule_message_content}', embeds=previous_rules_embeds)

            # Checks passed, set server has rule to True (After we log the previous rules)
            self.server_has_rule = True

            # Update server rules message in memory
            self.server_rule_channel_id = channel.id
            self.server_rule_message_id = message.id
            # Make sure the message content is not empty, otherwise it will be 'none'
            self.server_rule_message_content = message.content if len(message.content) > 0 else 'none'
            self.server_rule_message_embeds_info_dict_list = []
            for embed in message.embeds:
                embed_info_dict = {
                    'title': embed.title if embed.title is not None else 'none',
                    'description': embed.description if embed.description is not None else 'none',
                    'thumbnail_url': embed.thumbnail.url,
                    # Colour.value can be converted to a hex string. Or it can be None.
                    'colour': hex(embed.colour.value) if embed.colour is not None else None,  # Convert colour to hex
                    'fields': []
                }
                for field in embed.fields:
                    embed_info_dict['fields'].append({
                        'name': field.name if field.name is not None else 'none',
                        'value': field.value if field.value is not None else 'none'
                    })
                self.server_rule_message_embeds_info_dict_list.append(embed_info_dict)
            # Send success message
            await interaction.response.send_message('Server rules set to this message (using this message as new rules).', ephemeral=True)

        elif set_action == 'overwrite':
            # If set_action is 'overwrite', overwrite the message with the server rules message

            # Checks passed, set server has rule to True
            self.server_has_rule = True

            # This action only changes the id of the message, so we don't need to log the previous rules message.
            self.server_rule_channel_id = channel.id
            self.server_rule_message_id = message.id
            embeds = []
            for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
                embed = discord.Embed()
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
                embed.title = embed_info_dict['title']
                embed.description = embed_info_dict['description']
                embed.set_thumbnail(url=embed_info_dict['thumbnail_url'])
                embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict['colour'] else None
                for field in embed_info_dict['fields']:
                    embed.add_field(name=field['name'], value=field['value'], inline=False)
                # This tells us who updated the rules and when
                embed.set_footer(text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")} at ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
                embed.timestamp = datetime.datetime.now()
                embeds.append(embed)
            # Update the message
            await message.edit(content=self.server_rule_message_content, embeds=embeds)
            # Send success message
            await interaction.response.send_message('Server rules set to this message (overwritten from stored rules).', ephemeral=True)

        # Write to file any changes
        # Any None values are converted to empty strings
        with open(self.server_rules_csv_full_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['value_name', 'value'])
            writer.writerow(['channel_id', self.server_rule_channel_id])
            writer.writerow(['message_id', self.server_rule_message_id])
            writer.writerow(['message_content', self.server_rule_message_content])
            for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
                writer.writerow(['embed_title', embed_info_dict['title'] if embed_info_dict['title'] else ''])
                writer.writerow(
                    ['embed_description', embed_info_dict['description'] if embed_info_dict['description'] else ''])
                writer.writerow(['embed_thumbnail_url',
                                 embed_info_dict['thumbnail_url'] if embed_info_dict['thumbnail_url'] else ''])
                writer.writerow(['embed_colour', embed_info_dict['colour'] if embed_info_dict['colour'] else ''])
                for field in embed_info_dict['fields']:
                    writer.writerow(['embed_field_name', field['name'] if field['name'] else ''])
                    writer.writerow(['embed_field_value', field['value'] if field['value'] else ''])

    @set_rules_to_existing_message.error
    async def set_rules_to_existing_messageError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for set_rules_to_existing_message command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.', ephemeral=True)

    @app_commands.command(
        name='create_new_rules_message',
        description='Create a new message to be used as the server rules message.')
    @app_commands.describe(
        channel='The channel where the message should be created.',
        create_action='Whether to create a blank message or create a message with stored rules.')
    @app_commands.choices(
        create_action=[
            Choice(name="Create Blank Message", value="blank"),
            Choice(name="Create Message With Stored Rules", value="stored_rules")])
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def create_new_rules_message(
            self,
            interaction: discord.Interaction,
            channel: discord.TextChannel,
            create_action: str) -> None:
        """
        If create_action is 'blank', create a blank message.
            Since this message could overwrite the current rules message, log the previous rules message.
            Set server has rule to True.
            Send a new message, store the message id and channel id, and message content.
            Send a success message.
        If create_action is 'stored_rules', create a message with the stored rules.
            No need to log the existing server rules, as we are writing new message with the existing server rules.
            Load the server rules embeds from memory.
            Write the message with the server rules message.
            Send a success message.
        """

        # The server will have rules no matter what

        if create_action == 'blank':
            # If create_action is 'blank', create a blank message

            if self.server_has_rule:
                # Log previous rules message in the log channel, only if the server previously has rules
                previous_rules_embeds = []
                for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
                    embed = discord.Embed()
                    embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
                    embed.title = embed_info_dict['title']
                    embed.description = embed_info_dict['description']
                    embed.set_thumbnail(url=embed_info_dict['thumbnail_url'])
                    # Colour is a hex string, so we convert it to a discord.Colour object. If it is None, we set it to None.
                    embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                        'colour'] else None
                    for field in embed_info_dict['fields']:
                        embed.add_field(name=field['name'], value=field['value'], inline=False)
                    embed.set_footer(
                        # This tells us who updated the rules and when
                        text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")} at ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
                    embed.timestamp = datetime.datetime.now()
                    previous_rules_embeds.append(embed)
                log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
                # Send log message, mention it is a rule change.
                await log_channel.send(content=f'**Server Rule Changed:**\n{self.server_rule_message_content}',
                                       embeds=previous_rules_embeds)

            self.server_has_rule = True
            message = await channel.send('New server rules message.')
            # Set the server rules message to the new message
            self.server_rule_channel_id = channel.id
            self.server_rule_message_id = message.id
            self.server_rule_message_content = message.content
            self.server_rule_message_embeds_info_dict_list = []
            # Send success message
            await interaction.response.send_message('Server rules set to a newly-sent blank message.', ephemeral=True)
        elif create_action == 'stored_rules':
            # If create_action is 'stored_rules', create a message with the stored rules
            self.server_has_rule = True
            embeds = []
            for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
                embed = discord.Embed()
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
                embed.title = embed_info_dict['title']
                embed.description = embed_info_dict['description']
                embed.set_thumbnail(url=embed_info_dict['thumbnail_url'])
                # Colour is a hex string, so we convert it to a discord.Colour object. If it is None, we set it to None.
                embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict['colour'] else None
                for field in embed_info_dict['fields']:
                    embed.add_field(name=field['name'], value=field['value'], inline=False)
                embed.set_footer(text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")} at ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
                embed.timestamp = datetime.datetime.now()
                embeds.append(embed)
            message = await channel.send(content=self.server_rule_message_content, embeds=embeds)

            # Set the server rules message to the new message
            self.server_rule_channel_id = channel.id
            self.server_rule_message_id = message.id
            # Send success message
            await interaction.response.send_message('Server rules set to a newly-sent message (from stored rules).', ephemeral=True)

        # Write to file any changes
        # Any None values are converted to empty strings
        with open(self.server_rules_csv_full_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['value_name', 'value'])
            writer.writerow(['channel_id', self.server_rule_channel_id])
            writer.writerow(['message_id', self.server_rule_message_id])
            writer.writerow(['message_content', self.server_rule_message_content])
            for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
                writer.writerow(['embed_title', embed_info_dict['title'] if embed_info_dict['title'] else ''])
                writer.writerow(
                    ['embed_description', embed_info_dict['description'] if embed_info_dict['description'] else ''])
                writer.writerow(['embed_thumbnail_url',
                                 embed_info_dict['thumbnail_url'] if embed_info_dict['thumbnail_url'] else ''])
                writer.writerow(['embed_colour', embed_info_dict['colour'] if embed_info_dict['colour'] else ''])
                for field in embed_info_dict['fields']:
                    writer.writerow(['embed_field_name', field['name'] if field['name'] else ''])
                    writer.writerow(['embed_field_value', field['value'] if field['value'] else ''])

    @create_new_rules_message.error
    async def create_new_rules_messageError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for create_new_rules_message command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)

    @app_commands.command(
        name='get_link',
        description='Get the link to the server rules message.')
    @app_commands.guilds(SERVER_ID)
    async def get_link(
            self,
            interaction: discord.Interaction) -> None:
        """
        Get the link to the server rules message.
        If the server does not have rules, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        """
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.', ephemeral=True)
        else:
            try:
                channel = self.bot.get_channel(self.server_rule_channel_id)
                message = await channel.fetch_message(self.server_rule_message_id)
                await interaction.response.send_message(message.jump_url, ephemeral=True)
            except discord.errors.NotFound:
                await interaction.response.send_message('Server rules message not found.', ephemeral=True)
                self.server_has_rule = False

    @app_commands.command(
        name='add_new_ruleset',
        description='Add a new embed ruleset to the server rules message.')
    @app_commands.describe(
        name='The name of the ruleset.',
        description='(Optional) The description of the ruleset.')
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def add_new_ruleset(
            self,
            interaction: discord.Interaction,
            name: str,
            description: Optional[str] = 'none') -> None:
        """
        Add a new embed message to the server rules message with title = name and description = description.
        This command can be used only if the server already has rules.
        We arbitrarily set that all embeds set by this Cog will need to have a title.

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        Log previous embeds.
        Set up a new embed message with title = name and description = description.
        Load new embed to memory.
        Edit the server rules message to append the new embed message to the end of embeds.
        Write to csv file the new embed message (append should be fine).
        """

        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.', ephemeral=True)
            return

        # Edit the server rules message to append the new embed message to the end of embeds.
        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            self.server_has_rule = False
            return

        # Log previous rules message in the log channel, only if the server previously has rules
        previous_rules_embeds = []
        for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
            embed = discord.Embed()
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
            embed.title = embed_info_dict['title']
            embed.description = embed_info_dict['description']
            embed.set_thumbnail(url=embed_info_dict['thumbnail_url'])
            # Colour is a hex string, so we convert it to a discord.Colour object. If it is None, we set it to None.
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict['colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")} at ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**\n{self.server_rule_message_content}',
                               embeds=previous_rules_embeds)

        # Set up a new embed message with title = name and description = description.
        new_embed = discord.Embed(title=name, description=description)
        new_embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        new_embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")} at ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        new_embed.timestamp = datetime.datetime.now()

        # Load new embed to memory.
        self.server_rule_message_embeds_info_dict_list.append({
            'title': name,
            'description': description,
            'thumbnail_url': None,
            'colour': None,
            'fields': []
        })

        await message.edit(content=message.content, embeds=message.embeds + [new_embed])

        # Write to csv file the new embed message (append should be fine).
        with open(self.server_rules_csv_full_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['embed_title', name])
            writer.writerow(['embed_description', description if description else ''])
            writer.writerow(['embed_thumbnail_url', ''])
            writer.writerow(['embed_colour', ''])

        # Send a message to the user saying that the new ruleset has been added.
        await interaction.response.send_message('New ruleset added.', ephemeral=True)

    @add_new_ruleset.error
    async def add_new_rulesetError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for add_new_ruleset command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)

    async def ruleset_autocomplete(self,
            interaction: discord.Interaction,
            current: str) -> List[app_commands.Choice[str]]:
        ruleset_titles = [f"{embed_info_dict['title']} - {i}" for i, embed_info_dict in enumerate(self.server_rule_message_embeds_info_dict_list, 1)]
        return [
            app_commands.Choice(name=ruleset_title, value=ruleset_title)
            for ruleset_title in ruleset_titles if current.lower() in ruleset_title.lower()
        ]

    @app_commands.command(
        name='add_new_field',
        description='Add a new embed field with set name and value to a ruleset embed.')
    @app_commands.describe(
        ruleset_title='The name of the ruleset.',
        field_name='The name of the field.',
        field_value='The value of the field.')
    @app_commands.autocomplete(ruleset_title=ruleset_autocomplete)
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def add_new_field(
            self,
            interaction: discord.Interaction,
            ruleset_title: str,
            field_name: Optional[str] = 'none',
            field_value: Optional[str] = 'none') -> None:
        """
        Add a new embed field with set name and value to a ruleset embed.
        This command can be used only if the server already has rules.
        We set all default value to 'none' to match this cog's formatting that only colour and thumbnail url can be None

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        Log previous embeds.
        ruleset_title lets user choose which ruleset to add the field to, and its value is the index of the ruleset.
        ruleset_title is actually an index value!!!
        Access the ruleset embed from the index from memory.
        add_field to the ruleset embed.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        possible_ruleset_titles = [f"{embed_info_dict['title']} - {i}" for i, embed_info_dict in enumerate(self.server_rule_message_embeds_info_dict_list, 1)]
        if ruleset_title not in possible_ruleset_titles:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            return
        ruleset_index = possible_ruleset_titles.index(ruleset_title)
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            self.server_has_rule = False
            return

        # Log previous rules message in the log channel, only if the server previously has rules
        previous_rules_embeds = []
        for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
            embed = discord.Embed()
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
            embed.title = embed_info_dict['title']
            embed.description = embed_info_dict['description']
            embed.set_thumbnail(url=embed_info_dict['thumbnail_url'])
            # Colour is a hex string, so we convert it to a discord.Colour object. If it is None, we set it to None.
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict['colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")} at ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**\n{self.server_rule_message_content}',
                               embeds=previous_rules_embeds)

        # Set up a new embed message with title = name and description = description.
        # Load new embed to memory.
        editing_embed = self.server_rule_message_embeds_info_dict_list[ruleset_index]
        editing_embed['fields'].append({
            'name': field_name,
            'value': field_value
        })
        # Set up a new array of embeds, replacing the old embed with the new embed.
        embeds = message.embeds
        for i, embed in enumerate(embeds):
            if i == ruleset_index:
                embed.add_field(name=field_name, value=field_value, inline=False)
                embed.set_footer(
                    text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")} at ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
                embed.timestamp = datetime.datetime.now()

        # Edit the server rules message with the new embed message.
        await message.edit(content=message.content, embeds=embeds)

        # Write to file any changes
        # Any None values are converted to empty strings
        with open(self.server_rules_csv_full_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['value_name', 'value'])
            writer.writerow(['channel_id', self.server_rule_channel_id])
            writer.writerow(['message_id', self.server_rule_message_id])
            writer.writerow(['message_content', self.server_rule_message_content])
            for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
                writer.writerow(['embed_title', embed_info_dict['title'] if embed_info_dict['title'] else ''])
                writer.writerow(
                    ['embed_description', embed_info_dict['description'] if embed_info_dict['description'] else ''])
                writer.writerow(['embed_thumbnail_url',
                                 embed_info_dict['thumbnail_url'] if embed_info_dict['thumbnail_url'] else ''])
                writer.writerow(['embed_colour', embed_info_dict['colour'] if embed_info_dict['colour'] else ''])
                for field in embed_info_dict['fields']:
                    writer.writerow(['embed_field_name', field['name'] if field['name'] else ''])
                    writer.writerow(['embed_field_value', field['value'] if field['value'] else ''])

        # Send a message to the user saying that the new ruleset has been added.
        await interaction.response.send_message('New ruleset added.', ephemeral=True)

    @add_new_field.error
    async def add_new_fieldError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for add_new_field command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)

    # TODO: check if I spelled color or colour
    # TODO: make a write_to_csv function

    # TODO: ANY EDITS TO THE RULES WILL ADD FOOTER OF WHO EDITED AND WHEN AND TIMEZONE
    # TODO: AUTHOR WILL ALWAYS BE THE BOT
    # TODO: BEFORE ANY COMMAND CALL, CHECK IF SERVER HAS RULES + CHECK IF RULE MESSAGE EXISTS, IF NOT MARK SERVER DOESN'T HAVE RULES YET


    # TODO: multiple command to add to current rules
    #     if along any point there's an error, send a message to the user with the reason of failure
    #     This command can be used only if the server already has rules
    #     Takes input a type of addition DIFFERENT COMMANDS UNDER ONE GROUP /server_rules ...
    #     Ordering the commands:
    #       add_new:
    #           --ruleset--, field
    #       insert_new_before:
    #           ruleset, field
    #       edit:
    #           ruleset thumbnail, ruleset title, ruleset description, ruleset colour, field
    #       remove:
    #           ruleset, (WE DON'T WANT TO REMOVE TITLE) ruleset title, ruleset description, ruleset colour, field
    #     user inputs:
    #         add_new_ruleset: Name of ruleset, description of ruleset
    #         remove_existing_ruleset: select from existing ruleset titles
    #         insert_new_ruleset_before: select from existing ruleset titles, new_ruleset_title, new_ruleset_description
    #         edit_rule_embed_thumbnail: select from existing ruleset titles, thumbnail_url
    #         edit_rule_embed_title: select from existing ruleset titles, title
    #         edit_rule_embed_description: select from existing ruleset titles, description
    #         remove_rule_embed_description: select from existing ruleset titles
    #         add_new_field (note that any role/user mention will need to be in proper format of <@....>): select from existing ruleset titles, field_title, field_content (inline always false)
    #         insert_new_field_before (note that any role/user mention will need to be in proper format of <@....>): select from existing ruleset titles-field_title, new_field_title, new_field_content.
    #         edit_existing_field (note that any role/user mention will need to be in proper format of <@....>): select from ruleset titles-field_title, OPTIONAL (non-empty): new_field_title, new_field_content.
    #         remove_existing_field: select from ruleset titles-field_title
    #         edit_rule_embed_color: select from existing ruleset titles, color
    #         remove_rule_embed_thumbnail: select from existing ruleset titles
    # TODO: one command to retrieve ONE specific rule (display in channel and disappear after 5 minutes)
    #     This command can be used only if the server already has rules
    #     Has cooldown unless the user is a moderator
    #     Takes input a ruleset title-rule_field_title
    #     outputs: embed with rule title, rule description, rule_field (specific to the rule), rule_thumbnail, rule_color


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        ServerRulesCog(bot),
        guilds=[discord.Object(id=SERVER_ID)])