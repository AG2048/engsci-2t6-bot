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


def embed_surpassed_limit(embeds: List[discord.Embed]) -> bool:
    """
    Embed titles are limited to 256 characters
    Embed descriptions are limited to 4096 characters
    There can be up to 25 fields
    A field's name is limited to 256 characters and its value to 1024 characters
    The footer text is limited to 2048 characters
    The author name is limited to 256 characters
    The sum of all characters from all embed structures in a message must not exceed 6000 characters
    10 embeds can be sent per message

    return True if the embeds surpass the limit
    """
    sum_characters = 0
    if len(embeds) > 10:
        return True
    for embed in embeds:
        if len(embed.title) > 256:
            return True
        if len(embed.description) > 4096:
            return True
        if len(embed.fields) > 25:
            return True
        for field in embed.fields:
            sum_characters += len(field.name) + len(field.value)
            if len(field.name) > 256:
                return True
            if len(field.value) > 1024:
                return True
        if len(embed.footer.text) > 2048:
            return True
        if len(embed.author.name) > 256:
            return True
        sum_characters += len(embed.title) + len(embed.description) + len(embed.footer.text) + len(embed.author.name)
    if sum_characters > 6000:
        return True
    return False


colour_dict = {
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
        await self.bot.log(
            cog=self,
            user=None,
            user_action=None,
            channel=None,
            event='ServerRulesCog is ready.',
            outcome=None)

    @app_commands.command(
        name='set_rules_to_existing_message',
        description='Set existing message sent by bot as rules message')
    @app_commands.describe(
        channel='The channel of the message',
        message_id='The ID of message to set as rules message',
        set_action='Use message as rules OR Overwrite message with stored rules')
    @app_commands.choices(
        set_action=[
            Choice(name="Use This Message's Contents As Rules", value="this_message"),
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
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called set_rules_to_existing_message with parameters: channel={channel}, message_id={message_id}, set_action={set_action}',
                channel=interaction.channel,
                event=None,
                outcome='Message ID is not a valid integer.')
            return

        # Check if message exists in the channel
        try:
            message = await channel.fetch_message(message_id)

            # Check if message is sent by the bot
            if message.author != self.bot.user:
                await interaction.response.send_message('Message is not sent by the bot.', ephemeral=True)
                await self.bot.log(
                    cog=self,
                    user=interaction.user,
                    user_action=f'Called set_rules_to_existing_message with parameters: channel={channel}, message_id={message_id}, set_action={set_action}',
                    channel=interaction.channel,
                    event=None,
                    outcome='Message is not sent by the bot.')
                return
        except discord.errors.NotFound:
            await interaction.response.send_message('Message does not exist in the channel.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called set_rules_to_existing_message with parameters: channel={channel}, message_id={message_id}, set_action={set_action}',
                channel=interaction.channel,
                event=None,
                outcome='Message does not exist in the channel.')
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
                        text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
                    embed.timestamp = datetime.datetime.now()
                    previous_rules_embeds.append(embed)
                log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
                # Send log message, mention it is a rule change.
                await log_channel.send(content=f'**Server Rule Changed:**')
                await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

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
            url_view = discord.ui.View()
            url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
            await interaction.response.send_message('Server rules set to this message (using this message as new rules).', ephemeral=True, view=url_view)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called set_rules_to_existing_message with parameters: channel={channel}, message_id={message_id}, set_action={set_action}',
                channel=interaction.channel,
                event=None,
                outcome='Server rules set to this message (using this message as new rules).')

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
                embed.set_footer(text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
                embed.timestamp = datetime.datetime.now()
                embeds.append(embed)
            # Update the message
            await message.edit(content=self.server_rule_message_content, embeds=embeds)
            # Send success message
            url_view = discord.ui.View()
            url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
            await interaction.response.send_message('Server rules set to this message (overwritten from stored rules).', ephemeral=True, view=url_view)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called set_rules_to_existing_message with parameters: channel={channel}, message_id={message_id}, set_action={set_action}',
                channel=interaction.channel,
                event=None,
                outcome='Server rules set to this message (overwritten from stored rules).')

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
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called set_rules_to_existing_message',
                channel=interaction.channel,
                event=None,
                outcome='User did not have any of the required roles.')

    @app_commands.command(
        name='create_new_rules_message',
        description='Create new rules message')
    @app_commands.describe(
        channel='The channel for new message',
        create_action='Create blank message OR Create message with stored rules')
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
                        text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
                    embed.timestamp = datetime.datetime.now()
                    previous_rules_embeds.append(embed)
                log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
                # Send log message, mention it is a rule change.
                await log_channel.send(content=f'**Server Rule Changed:**')
                await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

            self.server_has_rule = True
            message = await channel.send('New server rules message.')
            # Set the server rules message to the new message
            self.server_rule_channel_id = channel.id
            self.server_rule_message_id = message.id
            self.server_rule_message_content = message.content
            self.server_rule_message_embeds_info_dict_list = []
            # Send success message
            url_view = discord.ui.View()
            url_view.add_item(
                discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
            await interaction.response.send_message('Server rules set to a newly-sent blank message.', ephemeral=True, view=url_view)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called create_new_rules_message with parameters: channel={channel}, create_action={create_action}',
                channel=interaction.channel,
                event=None,
                outcome='Server rules set to a newly-sent blank message.')
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
                embed.set_footer(text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
                embed.timestamp = datetime.datetime.now()
                embeds.append(embed)
            message = await channel.send(content=self.server_rule_message_content, embeds=embeds)

            # Set the server rules message to the new message
            self.server_rule_channel_id = channel.id
            self.server_rule_message_id = message.id
            # Send success message
            url_view = discord.ui.View()
            url_view.add_item(
                discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
            await interaction.response.send_message('Server rules set to a newly-sent message (from stored rules).', ephemeral=True, view=url_view)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called create_new_rules_message with parameters: channel={channel}, create_action={create_action}',
                channel=interaction.channel,
                event=None,
                outcome='Server rules set to a newly-sent message (from stored rules).')

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
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called create_new_rules_message.',
                channel=interaction.channel,
                event=None,
                outcome='User did not have any of the required roles.')

    @app_commands.command(
        name='get_link',
        description='Get link to rules message')
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
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called get_link.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
        else:
            try:
                channel = self.bot.get_channel(self.server_rule_channel_id)
                message = await channel.fetch_message(self.server_rule_message_id)
                url_view = discord.ui.View()
                url_view.add_item(
                    discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
                await interaction.response.send_message(message.jump_url, ephemeral=True, view=url_view)
                await self.bot.log(
                    cog=self,
                    user=interaction.user,
                    user_action=f'Called get_link.',
                    channel=interaction.channel,
                    event=None,
                    outcome='Sent link to server rules message.')
            except discord.errors.NotFound:
                await interaction.response.send_message('Server rules message not found.', ephemeral=True)
                await self.bot.log(
                    cog=self,
                    user=interaction.user,
                    user_action=f'Called get_link.',
                    channel=interaction.channel,
                    event=None,
                    outcome='Server rules message not found.')
                self.server_has_rule = False

    @app_commands.command(
        name='add_new_ruleset',
        description='Add new ruleset/embed to rules message')
    @app_commands.describe(
        name='Name of ruleset',
        description='Description of ruleset')
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
        Set up a new embed with title = name and description = description.
        Check if embeds are too long, if so, send a message saying that.
        Log previous embeds.
        Load new embed to memory.
        Edit the server rules message to append the new embed message to the end of embeds.
        Write to csv file the new embed message.
        """

        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called add_new_ruleset with parameters: name={name}, description={description}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        # Edit the server rules message to append the new embed message to the end of embeds.
        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called add_new_ruleset with parameters: name={name}, description={description}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        # Set up a new embed message with title = name and description = description.
        new_embed = discord.Embed(title=name, description=description)
        new_embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        new_embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        new_embed.timestamp = datetime.datetime.now()

        embeds = message.embeds
        embeds.append(new_embed)

        if embed_surpassed_limit(embeds):
            await interaction.response.send_message('Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called add_new_ruleset with parameters: name={name}, description={description}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed (too many embeds or too many characters).')
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
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Load new embed to memory.
        self.server_rule_message_embeds_info_dict_list.append({
            'title': name,
            'description': description,
            'thumbnail_url': None,
            'colour': None,
            'fields': []
        })

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
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('New ruleset added.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called add_new_ruleset with parameters: name={name}, description={description}.',
            channel=interaction.channel,
            event=None,
            outcome='Success.')

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
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called add_new_ruleset.',
                channel=interaction.channel,
                event=None,
                outcome='User does not have any of the required roles.')

    async def ruleset_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str) -> List[app_commands.Choice[str]]:
        ruleset_titles = [f"{embed_info_dict['title']} - {i}" for i, embed_info_dict in enumerate(self.server_rule_message_embeds_info_dict_list, 1)]
        return [
            app_commands.Choice(name=ruleset_title, value=ruleset_title)
            for ruleset_title in ruleset_titles if current.lower() in ruleset_title.lower()
        ]

    @app_commands.command(
        name='add_new_field',
        description='Add new field to a ruleset/embed')
    @app_commands.describe(
        ruleset_title='Name of ruleset',
        field_name='Name of field',
        field_value='Value of field')
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
        ruleset_title lets user choose which ruleset to add the field to
        convert ruleset_title to ruleset_index
        Access the ruleset embed from the index from message.embeds.
        add_field to the ruleset embed.
        Check if the ruleset embed is too long, if so, send a message saying that the ruleset embed is too long.
        Log previous embeds.
        Load the ruleset embed to memory.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        possible_ruleset_titles = [f"{embed_info_dict['title']} - {i}" for i, embed_info_dict in enumerate(self.server_rule_message_embeds_info_dict_list, 1)]
        if ruleset_title not in possible_ruleset_titles:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called add_new_field with parameters: ruleset_title={ruleset_title}, field_name={field_name}, field_value={field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid ruleset title.')
            return
        ruleset_index = possible_ruleset_titles.index(ruleset_title)
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called add_new_field with parameters: ruleset_title={ruleset_title}, field_name={field_name}, field_value={field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called add_new_field with parameters: ruleset_title={ruleset_title}, field_name={field_name}, field_value={field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        # Set up a new array of embeds, replacing the old embed with the new embed.
        embeds = message.embeds
        embed = embeds[ruleset_index]
        embed.add_field(name=field_name, value=field_value, inline=False)
        embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        embed.timestamp = datetime.datetime.now()

        if embed_surpassed_limit(embeds):
            await interaction.response.send_message(
                'Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.',
                ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called add_new_field with parameters: ruleset_title={ruleset_title}, field_name={field_name}, field_value={field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed (too many embeds or too many characters)')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Load new embed_field to memory.
        editing_embed = self.server_rule_message_embeds_info_dict_list[ruleset_index]
        editing_embed['fields'].append({
            'name': field_name,
            'value': field_value
        })

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

        # Send a message to the user saying that the new field has been added.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('New field added.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called add_new_field with parameters: ruleset_title={ruleset_title}, field_name={field_name}, field_value={field_value}.',
            channel=interaction.channel,
            event=None,
            outcome='Success')

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
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called add_new_field.',
                channel=interaction.channel,
                event=None,
                outcome='User does not have any of the required roles.')

    @app_commands.command(
        name='insert_new_ruleset_before',
        description='Insert new ruleset before a ruleset')
    @app_commands.describe(
        ruleset_title='Name of ruleset to insert before',
        name='Name of new ruleset',
        description='Description of new ruleset')
    @app_commands.autocomplete(ruleset_title=ruleset_autocomplete)
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def insert_new_ruleset_before(
            self,
            interaction: discord.Interaction,
            ruleset_title: str,
            name: str,
            description: Optional[str] = 'none') -> None:
        """
        Insert a new embed message to rules message before ruleset_title with title = name, description = description.
        This command can be used only if the server already has rules.
        We arbitrarily set that all embeds set by this Cog will need to have a title.

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        ruleset_title lets user choose which ruleset to add the field to
        convert ruleset_title to ruleset_index
        Set up a new embed message with title = name and description = description.
        Check if the ruleset embed is too long, if so, send a message saying that the ruleset embed is too long.
        Log previous embeds.
        Insert new embed to memory.
        Edit the server rules message to insert the new embed message to index ruleset_index.
        Write to csv file the new embed message.
        """
        possible_ruleset_titles = [f"{embed_info_dict['title']} - {i}" for i, embed_info_dict in
                                   enumerate(self.server_rule_message_embeds_info_dict_list, 1)]
        if ruleset_title not in possible_ruleset_titles:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called insert_new_ruleset_before with parameters: ruleset_title={ruleset_title}, name={name}, description={description}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid ruleset title.')
            return
        ruleset_index = possible_ruleset_titles.index(ruleset_title)
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called insert_new_ruleset_before with parameters: ruleset_title={ruleset_title}, name={name}, description={description}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called insert_new_ruleset_before with parameters: ruleset_title={ruleset_title}, name={name}, description={description}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        # Set up a new embed message with title = name and description = description.
        new_embed = discord.Embed(title=name, description=description)
        new_embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        new_embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        new_embed.timestamp = datetime.datetime.now()

        # Insert new embed to message
        embeds = message.embeds
        embeds.insert(ruleset_index, new_embed)

        # Check if the ruleset embed is too long, if so, send a message saying that the ruleset embed is too long.
        if embed_surpassed_limit(embeds):
            await interaction.response.send_message(
                'Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.',
                ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called insert_new_ruleset_before with parameters: ruleset_title={ruleset_title}, name={name}, description={description}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed (too many embeds or too many characters)')
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
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Insert new embed to memory.
        self.server_rule_message_embeds_info_dict_list.insert(ruleset_index, {
            'title': name,
            'description': description,
            'thumbnail_url': None,
            'colour': None,
            'fields': []
        })

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

        # Send a message to the user saying that the new ruleset has been inserted.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('New ruleset inserted.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called insert_new_ruleset_before with parameters: ruleset_title={ruleset_title}, name={name}, description={description}.',
            channel=interaction.channel,
            event=None,
            outcome='Success')

    @insert_new_ruleset_before.error
    async def insert_new_ruleset_beforeError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for insert_new_ruleset_before command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called insert_new_ruleset_before',
                channel=interaction.channel,
                event=None,
                outcome='User did not have any of the required roles.')

    async def fields_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str) -> List[app_commands.Choice[str]]:
        ruleset_and_fields = [f"{embed_info_dict['title']} - {field['name']} ({i},{j})" for i, embed_info_dict in enumerate(self.server_rule_message_embeds_info_dict_list, 1) for j, field in enumerate(embed_info_dict['fields'], 1)]
        return [
            app_commands.Choice(name=ruleset_and_field, value=ruleset_and_field)
            for ruleset_and_field in ruleset_and_fields if current.lower() in ruleset_and_field.lower()
        ]

    @app_commands.command(
        name='insert_new_field_before',
        description='Insert new field to a ruleset before a field')
    @app_commands.describe(
        ruleset_and_field='Name of field to insert before',
        field_name='Name of new field',
        field_value='Value of new field')
    @app_commands.autocomplete(ruleset_and_field=fields_autocomplete)
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def insert_new_field_before(
            self,
            interaction: discord.Interaction,
            ruleset_and_field: str,
            field_name: Optional[str] = 'none',
            field_value: Optional[str] = 'none') -> None:
        """
        Insert a new field to an existing ruleset before a specific field.
        This command can be used only if the server already has rules.
        We set all default value to 'none' to match this cog's formatting that only colour and thumbnail url can be None

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        Find index of ruleset AND index of field.
        Access the ruleset embed from the index from message.embeds.
        insert_field_at to the embed.
        Check if the ruleset embed is too long, if so, send a message saying that the ruleset embed is too long.
        Log previous embeds.
        Insert new embed to memory.
        Edit the server rules message to insert the new embed message to index ruleset_index.
        Write to csv file the new embed message.
        """
        possible_ruleset_and_fields = [f"{embed_info_dict['title']} - {field['name']} ({i},{j})" for i, embed_info_dict in enumerate(self.server_rule_message_embeds_info_dict_list, 1) for j, field in enumerate(embed_info_dict['fields'], 1)]

        if ruleset_and_field not in possible_ruleset_and_fields:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called insert_new_field_before with parameters: ruleset_and_field={ruleset_and_field}, field_name={field_name}, field_value={field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid ruleset title.')
            return
        ruleset_index = 0
        field_index = 0
        for i in range(len(self.server_rule_message_embeds_info_dict_list)):
            for j in range(len(self.server_rule_message_embeds_info_dict_list[i]['fields'])):
                if ruleset_and_field == f"{self.server_rule_message_embeds_info_dict_list[i]['title']} - {self.server_rule_message_embeds_info_dict_list[i]['fields'][j]['name']} ({i+1},{j+1})":
                    ruleset_index = i
                    field_index = j
                    break
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called insert_new_field_before with parameters: ruleset_and_field={ruleset_and_field}, field_name={field_name}, field_value={field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called insert_new_field_before with parameters: ruleset_and_field={ruleset_and_field}, field_name={field_name}, field_value={field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        embeds = message.embeds
        embed = embeds[ruleset_index]
        embed.insert_field_at(field_index, name=field_name, value=field_value, inline=False)
        embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        embed.timestamp = datetime.datetime.now()

        if embed_surpassed_limit(embeds):
            await interaction.response.send_message(
                'Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.',
                ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called insert_new_field_before with parameters: ruleset_and_field={ruleset_and_field}, field_name={field_name}, field_value={field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed (too many embeds or too many characters)')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Insert new embed_field to memory.
        editing_embed = self.server_rule_message_embeds_info_dict_list[ruleset_index]
        editing_embed['fields'].insert(field_index, {
            'name': field_name,
            'value': field_value
        })

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

        # Send a message to the user saying that the new field has been inserted.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('New field inserted.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called insert_new_field_before with parameters: ruleset_and_field={ruleset_and_field}, field_name={field_name}, field_value={field_value}.',
            channel=interaction.channel,
            event=None,
            outcome='Success')

    @insert_new_field_before.error
    async def insert_new_field_beforeError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for insert_new_field_before command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called insert_new_field_before.',
                channel=interaction.channel,
                event=None,
                outcome='MissingAnyRole')

    @app_commands.command(
        name='edit_ruleset_thumbnail',
        description='Edit a ruleset/embed thumbnail')
    @app_commands.describe(
        ruleset_title='Name of ruleset',
        thumbnail_url='Thumbnail URL')
    @app_commands.autocomplete(ruleset_title=ruleset_autocomplete)
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def edit_ruleset_thumbnail(
            self,
            interaction: discord.Interaction,
            ruleset_title: str,
            thumbnail_url: Optional[str] = None) -> None:
        """
        Edit the thumbnail of a ruleset embed.
        This command can be used only if the server already has rules.
        thumbnail_url of None means that the thumbnail will be removed.

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        ruleset_title lets user choose which ruleset to add the field to
        convert ruleset_title to ruleset_index
        Access the ruleset embed from the index from message.embeds.
        set_thumbnail(url=thumbnail_url) of the embed.
        Check if the ruleset embed is too long, if so, send a message saying that the ruleset embed is too long.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
            if HTTPException, send a message saying that the ruleset embed is invalid
        Log previous embeds.
        Load the ruleset embed to memory.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        possible_ruleset_titles = [f"{embed_info_dict['title']} - {i}" for i, embed_info_dict in
                                   enumerate(self.server_rule_message_embeds_info_dict_list, 1)]
        if ruleset_title not in possible_ruleset_titles:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_thumbnail with parameters: ruleset_title={ruleset_title}, thumbnail_url={thumbnail_url}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid ruleset title')
            return
        ruleset_index = possible_ruleset_titles.index(ruleset_title)
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_thumbnail with parameters: ruleset_title={ruleset_title}, thumbnail_url={thumbnail_url}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have rules')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_thumbnail with parameters: ruleset_title={ruleset_title}, thumbnail_url={thumbnail_url}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found')
            self.server_has_rule = False
            return

        # Set up a new array of embeds, replacing the old embed with the new embed.
        embeds = message.embeds
        embed = embeds[ruleset_index]
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        embed.timestamp = datetime.datetime.now()

        if embed_surpassed_limit(embeds):
            await interaction.response.send_message(
                'Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.',
                ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_thumbnail with parameters: ruleset_title={ruleset_title}, thumbnail_url={thumbnail_url}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed')
            return

        try:
            # Edit the server rules message with the new embed message.
            await message.edit(content=message.content, embeds=embeds)
        except discord.errors.HTTPException:
            await interaction.response.send_message('URL is invalid.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_thumbnail with parameters: ruleset_title={ruleset_title}, thumbnail_url={thumbnail_url}.',
                channel=interaction.channel,
                event=None,
                outcome='URL is invalid')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Load new embed_field to memory.
        editing_embed = self.server_rule_message_embeds_info_dict_list[ruleset_index]
        editing_embed['thumbnail_url'] = thumbnail_url

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

        # Send a message to the user saying that the thumbnail has been updated.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Thumbnail updated.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called edit_ruleset_thumbnail with parameters: ruleset_title={ruleset_title}, thumbnail_url={thumbnail_url}.',
            channel=interaction.channel,
            event=None,
            outcome='Success')

    @edit_ruleset_thumbnail.error
    async def edit_ruleset_thumbnailError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for edit_ruleset_thumbnail command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_thumbnail.',
                channel=interaction.channel,
                event=None,
                outcome='User does not have any of the required roles.')

    @app_commands.command(
        name='edit_ruleset_title',
        description='Edit title of a ruleset/embed')
    @app_commands.describe(
        ruleset_title='Name of ruleset',
        new_title='New title')
    @app_commands.autocomplete(ruleset_title=ruleset_autocomplete)
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def edit_ruleset_title(
            self,
            interaction: discord.Interaction,
            ruleset_title: str,
            new_title: str) -> None:
        """
        Edit the title of a ruleset embed.
        This command can be used only if the server already has rules.
        title cannot be None

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        ruleset_title lets user choose which ruleset to add the field to
        convert ruleset_title to ruleset_index
        Access the ruleset embed from the index from message.embeds.
        embed.title = new_title
        Check if the ruleset embed is too long, if so, send a message saying that the ruleset embed is too long.
        Log previous embeds.
        Load the ruleset embed to memory.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        possible_ruleset_titles = [f"{embed_info_dict['title']} - {i}" for i, embed_info_dict in
                                   enumerate(self.server_rule_message_embeds_info_dict_list, 1)]
        if ruleset_title not in possible_ruleset_titles:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_title with parameters: ruleset_title={ruleset_title}, new_title={new_title}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid ruleset title.')
            return
        ruleset_index = possible_ruleset_titles.index(ruleset_title)
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_title with parameters: ruleset_title={ruleset_title}, new_title={new_title}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_title with parameters: ruleset_title={ruleset_title}, new_title={new_title}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        # Set up a new array of embeds, replacing the old embed with the new embed.
        embeds = message.embeds
        embed = embeds[ruleset_index]
        embed.title = new_title
        embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        embed.timestamp = datetime.datetime.now()

        if embed_surpassed_limit(embeds):
            await interaction.response.send_message(
                'Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.',
                ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_title with parameters: ruleset_title={ruleset_title}, new_title={new_title}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed (too many embeds or too many characters)')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Load new embed_field to memory.
        editing_embed = self.server_rule_message_embeds_info_dict_list[ruleset_index]
        editing_embed['title'] = new_title

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

        # Send a message to the user saying that the title has been updated.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Title updated.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called edit_ruleset_title with parameters: ruleset_title={ruleset_title}, new_title={new_title}.',
            channel=interaction.channel,
            event=None,
            outcome='Success')

    @edit_ruleset_title.error
    async def edit_ruleset_titleError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for edit_ruleset_title command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_title.',
                channel=interaction.channel,
                event=None,
                outcome='MissingAnyRole')

    @app_commands.command(
        name='edit_ruleset_description',
        description='Edit description of a ruleset/embed')
    @app_commands.describe(
        ruleset_title='Name of ruleset',
        new_description='New description')
    @app_commands.autocomplete(ruleset_title=ruleset_autocomplete)
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def edit_ruleset_description(
            self,
            interaction: discord.Interaction,
            ruleset_title: str,
            new_description: str) -> None:
        """
        Edit the description of a ruleset embed.
        This command can be used only if the server already has rules.
        title cannot be None

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        ruleset_title lets user choose which ruleset to add the field to
        convert ruleset_title to ruleset_index
        Access the ruleset embed from the index from message.embeds.
        embed.description = new_description
        Check if the ruleset embed is too long, if so, send a message saying that the ruleset embed is too long.
        Log previous embeds.
        Load the ruleset embed to memory.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        possible_ruleset_titles = [f"{embed_info_dict['title']} - {i}" for i, embed_info_dict in
                                   enumerate(self.server_rule_message_embeds_info_dict_list, 1)]
        if ruleset_title not in possible_ruleset_titles:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_description with parameters: ruleset_title={ruleset_title}, new_description={new_description}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid ruleset title')
            return
        ruleset_index = possible_ruleset_titles.index(ruleset_title)
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_description with parameters: ruleset_title={ruleset_title}, new_description={new_description}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have rules')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_description with parameters: ruleset_title={ruleset_title}, new_description={new_description}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found')
            self.server_has_rule = False
            return

        # Set up a new array of embeds, replacing the old embed with the new embed.
        embeds = message.embeds
        embed = embeds[ruleset_index]
        embed.description = new_description
        embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        embed.timestamp = datetime.datetime.now()

        if embed_surpassed_limit(embeds):
            await interaction.response.send_message(
                'Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.',
                ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_description with parameters: ruleset_title={ruleset_title}, new_description={new_description}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Load new embed_field to memory.
        editing_embed = self.server_rule_message_embeds_info_dict_list[ruleset_index]
        editing_embed['description'] = new_description

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

        # Send a message to the user saying that the description has been updated.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Description updated.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called edit_ruleset_description with parameters: ruleset_title={ruleset_title}, new_description={new_description}.',
            channel=interaction.channel,
            event=None,
            outcome='Success')

    @edit_ruleset_description.error
    async def edit_ruleset_descriptionError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for edit_ruleset_description command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_description.',
                channel=interaction.channel,
                event=None,
                outcome='User did not have any of the required roles.')

    @app_commands.command(
        name='edit_ruleset_colour',
        description='Edit colour of a ruleset embed')
    @app_commands.describe(
        ruleset_title='Name of ruleset',
        new_colour_1='(1/2) Colour choices',
        new_colour_2='(2/2) Colour choices')
    @app_commands.autocomplete(ruleset_title=ruleset_autocomplete)
    @app_commands.choices(
        new_colour_1=[Choice(name=colour, value=colour) for colour in list(colour_dict.keys())[:len(colour_dict.keys()) // 2]],
        new_colour_2=[Choice(name=colour, value=colour) for colour in list(colour_dict.keys())[len(colour_dict.keys()) // 2:]])
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def edit_ruleset_colour(
            self,
            interaction: discord.Interaction,
            ruleset_title: str,
            new_colour_1: Optional[str] = None,
            new_colour_2: Optional[str] = None) -> None:
        """
        Edit the description of a ruleset embed.
        This command can be used only if the server already has rules.
        title cannot be None

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        ruleset_title lets user choose which ruleset to add the field to
        convert ruleset_title to ruleset_index
        Access the ruleset embed from the index from message.embeds.
        embed.description = new_description
        Check if the ruleset embed is too long, if so, send a message saying that the ruleset embed is too long.
        Log previous embeds.
        Load the ruleset embed to memory.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        if new_colour_1:
            colour = colour_dict[new_colour_1]
        elif new_colour_2:
            colour = colour_dict[new_colour_2]
        else:
            colour = None
        possible_ruleset_titles = [f"{embed_info_dict['title']} - {i}" for i, embed_info_dict in
                                   enumerate(self.server_rule_message_embeds_info_dict_list, 1)]
        if ruleset_title not in possible_ruleset_titles:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_colour with parameters: ruleset_title={ruleset_title}, new_colour_1={new_colour_1}, new_colour_2={new_colour_2}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid ruleset title.')
            return
        ruleset_index = possible_ruleset_titles.index(ruleset_title)
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_colour with parameters: ruleset_title={ruleset_title}, new_colour_1={new_colour_1}, new_colour_2={new_colour_2}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_colour with parameters: ruleset_title={ruleset_title}, new_colour_1={new_colour_1}, new_colour_2={new_colour_2}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        # Set up a new array of embeds, replacing the old embed with the new embed.
        embeds = message.embeds
        embed = embeds[ruleset_index]
        embed.colour = colour
        embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        embed.timestamp = datetime.datetime.now()

        if embed_surpassed_limit(embeds):
            await interaction.response.send_message(
                'Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.',
                ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_colour with parameters: ruleset_title={ruleset_title}, new_colour_1={new_colour_1}, new_colour_2={new_colour_2}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed (too many embeds or too many characters)')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Load new embed_field to memory.
        editing_embed = self.server_rule_message_embeds_info_dict_list[ruleset_index]
        editing_embed['colour'] = hex(colour.value)

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

        # Send a message to the user saying that the colour have been updated.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Colour updated.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called edit_ruleset_colour with parameters: ruleset_title={ruleset_title}, new_colour_1={new_colour_1}, new_colour_2={new_colour_2}.',
            channel=interaction.channel,
            event=None,
            outcome='Colour updated.')

    @edit_ruleset_colour.error
    async def edit_ruleset_colourError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for edit_ruleset_colour command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_ruleset_colour.',
                channel=interaction.channel,
                event=None,
                outcome='User does not have any of the required roles.')

    @app_commands.command(
        name='edit_message_content',
        description='Edit rules message content of rules message')
    @app_commands.describe(
        new_content='New message content')
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def edit_message_content(
            self,
            interaction: discord.Interaction,
            new_content: str) -> None:
        """
        Edit the message content of the server rules message.
        This command can be used only if the server already has rules.
        content cannot be None. Max 2000 characters.

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        Check if the new content is too long, if so, send a message saying that the new content is too long.
        Log previous embeds and message content in the log channel.
        Load the new content to memory.
        Edit the server rules message with the new content, and same embeds.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """

        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_message_content with parameters: new_content={new_content}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_message_content with parameters: new_content={new_content}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        # Check if the new content is too long, if so, send a message saying that the new content is too long.
        if len(new_content) > 2000:
            await interaction.response.send_message('Message content is too long (max 2000 characters).', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_message_content with parameters: new_content={new_content}.',
                channel=interaction.channel,
                event=None,
                outcome='Message content is too long (max 2000 characters).')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Load new embed_field to memory.
        self.server_rule_message_content = new_content

        # Edit the server rules message with the new embed message.
        await message.edit(content=new_content, embeds=message.embeds)

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

        # Send a message to the user saying that the message content have been updated.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Server rules message content updated.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called edit_message_content with parameters: new_content={new_content}.',
            channel=interaction.channel,
            event=None,
            outcome='Server rules message content updated.')

    @edit_message_content.error
    async def edit_message_contentError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for edit_message_content command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_message_content.',
                channel=interaction.channel,
                event=None,
                outcome='Missing required role.')

    @app_commands.command(
        name='edit_message_content_to_message',
        description='Edit rules message content to an existing message\'s content')
    @app_commands.describe(
        channel='Channel of existing message',
        message_id='ID of existing message')
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def edit_message_content_to_message(
            self,
            interaction: discord.Interaction,
            channel: discord.TextChannel,
            message_id: str) -> None:
        """
        Edit the message content of the server rules message to the message content of another message.
        This command can be used only if the server already has rules.
        content cannot be None or "". Max 2000 characters.

        Check if the message_id is a valid integer.
        Check if the message exists in the channel.
        Retrieve the message from which we extract content.
        Check if the content is "" or > 2000 characters.
        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.Log previous embeds and message content in the log channel.
        Load the new content to memory.
        Edit the server rules message with the new content, and same embeds.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        # Check if message_id is a valid integer
        try:
            message_id = int(message_id)
        except ValueError:
            await interaction.response.send_message('Message ID is not a valid integer.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_message_content_to_message with parameters: channel={channel}, message_id={message_id}',
                channel=interaction.channel,
                event=None,
                outcome='Message ID is not a valid integer.')
            return

        # Check if message exists in the channel
        try:
            message_we_extract_content_from = await channel.fetch_message(message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Message does not exist in the channel.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_message_content_to_message with parameters: channel={channel}, message_id={message_id}.',
                channel=interaction.channel,
                event=None,
                outcome='Message does not exist in the channel.')
            return

        # Get the content of the message
        new_content = message_we_extract_content_from.content
        if len(new_content) > 2000 or len(new_content) == 0:
            await interaction.response.send_message('Message content is too long or empty.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_message_content_to_message with parameters: channel={channel}, message_id={message_id}.',
                channel=interaction.channel,
                event=None,
                outcome='Message content is too long or empty.')
            return


        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_message_content_to_message with parameters: channel={channel}, message_id={message_id}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_message_content_to_message with parameters: channel={channel}, message_id={message_id}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Load new embed_field to memory.
        self.server_rule_message_content = new_content

        # Edit the server rules message with the new embed message.
        await message.edit(content=new_content, embeds=message.embeds)

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

        # Send a message to the user saying that the message content have been updated.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Server rules message content updated.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called edit_message_content_to_message with parameters: channel={channel}, message_id={message_id}.',
            channel=interaction.channel,
            event=None,
            outcome='Server rules message content updated.')

    @edit_message_content_to_message.error
    async def edit_message_content_to_messageError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for edit_message_content command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_message_content.',
                channel=interaction.channel,
                event=None,
                outcome='Missing required role.')

    @app_commands.command(
        name='edit_field',
        description='Edit field in rules')
    @app_commands.describe(
        ruleset_and_field='Name of field to edit',
        new_field_name='New name',
        new_field_value='New value')
    @app_commands.autocomplete(ruleset_and_field=fields_autocomplete)
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def edit_field(
            self,
            interaction: discord.Interaction,
            ruleset_and_field: str,
            new_field_name: Optional[str] = 'none',
            new_field_value: Optional[str] = 'none') -> None:
        """
        Edit the chosen field of a ruleset embed.
        This command can be used only if the server already has rules.
        default value for new_field_name and new_field_value is 'none'

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        Find index of ruleset AND index of field.
        Access the ruleset embed from the index from message.embeds.
        embed.set_field_at to the embed.
        Check if the ruleset embed is too long, if so, send a message saying that the ruleset embed is too long.
        Log previous embeds.
        Load the ruleset embed to memory.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        possible_ruleset_and_fields = [f"{embed_info_dict['title']} - {field['name']} ({i},{j})" for i, embed_info_dict
                                       in enumerate(self.server_rule_message_embeds_info_dict_list, 1) for j, field in
                                       enumerate(embed_info_dict['fields'], 1)]

        if ruleset_and_field not in possible_ruleset_and_fields:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_field with parameters: ruleset_and_field={ruleset_and_field}, new_field_name={new_field_name}, new_field_value={new_field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid ruleset title.')
            return
        ruleset_index = 0
        field_index = 0
        for i in range(len(self.server_rule_message_embeds_info_dict_list)):
            for j in range(len(self.server_rule_message_embeds_info_dict_list[i]['fields'])):
                if ruleset_and_field == f"{self.server_rule_message_embeds_info_dict_list[i]['title']} - {self.server_rule_message_embeds_info_dict_list[i]['fields'][j]['name']} ({i + 1},{j + 1})":
                    ruleset_index = i
                    field_index = j
                    break
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_field with parameters: ruleset_and_field={ruleset_and_field}, new_field_name={new_field_name}, new_field_value={new_field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_field with parameters: ruleset_and_field={ruleset_and_field}, new_field_name={new_field_name}, new_field_value={new_field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        embeds = message.embeds
        embed = embeds[ruleset_index]
        embed.set_field_at(field_index, name=new_field_name, value=new_field_value, inline=False)
        embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        embed.timestamp = datetime.datetime.now()

        if embed_surpassed_limit(embeds):
            await interaction.response.send_message(
                'Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.',
                ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_field with parameters: ruleset_and_field={ruleset_and_field}, new_field_name={new_field_name}, new_field_value={new_field_value}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed (too many embeds or too many characters)')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Insert new embed_field to memory.
        editing_embed = self.server_rule_message_embeds_info_dict_list[ruleset_index]
        editing_embed['fields'][field_index] = {
            'name': new_field_name,
            'value': new_field_value
        }

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

        # Send a message to the user saying that the field has been edited.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Field edited.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called edit_field with parameters: ruleset_and_field={ruleset_and_field}, new_field_name={new_field_name}, new_field_value={new_field_value}.',
            channel=interaction.channel,
            event=None,
            outcome='Success')

    @edit_field.error
    async def edit_fieldError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for insert_new_field_before command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called edit_field.',
                channel=interaction.channel,
                event=None,
                outcome='User does not have any of the required roles.')

    @app_commands.command(
        name='remove_ruleset',
        description='Remove a ruleset/embed')
    @app_commands.describe(
        ruleset_title='Name of ruleset')
    @app_commands.autocomplete(ruleset_title=ruleset_autocomplete)
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def remove_ruleset(
            self,
            interaction: discord.Interaction,
            ruleset_title: str) -> None:
        """
        Remove a ruleset embed.
        This command can be used only if the server already has rules.

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        ruleset_title lets user choose which ruleset to add the field to
        convert ruleset_title to ruleset_index
        Access the ruleset embed from the index from message.embeds.
        pop the ruleset embed from the embeds list.
        Log previous embeds.
        Load the ruleset embed to memory.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        possible_ruleset_titles = [f"{embed_info_dict['title']} - {i}" for i, embed_info_dict in
                                   enumerate(self.server_rule_message_embeds_info_dict_list, 1)]
        if ruleset_title not in possible_ruleset_titles:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_ruleset with parameters: ruleset_title={ruleset_title}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid ruleset title.')
            return
        ruleset_index = possible_ruleset_titles.index(ruleset_title)
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_ruleset with parameters: ruleset_title={ruleset_title}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_ruleset with parameters: ruleset_title={ruleset_title}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        # Remove the ruleset embed from the embeds list.
        embeds = message.embeds
        embeds.pop(ruleset_index)

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
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Remove the ruleset embed from the self.server_rule_message_embeds_info_dict_list
        self.server_rule_message_embeds_info_dict_list.pop(ruleset_index)

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

        # Send a message to the user saying that the ruleset has been deleted.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Ruleset deleted.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called remove_ruleset with parameters: ruleset_title={ruleset_title}.',
            channel=interaction.channel,
            event=None,
            outcome='Success.')

    @remove_ruleset.error
    async def remove_rulesetError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for remove_ruleset command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_ruleset.',
                channel=interaction.channel,
                event=None,
                outcome='User does not have any of the required roles.')

    @app_commands.command(
        name='remove_ruleset_by_index',
        description='Remove a ruleset embed (index starts on 0)')
    @app_commands.describe(
        ruleset_index='Index (starts on 0)')
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def remove_ruleset_by_index(
            self,
            interaction: discord.Interaction,
            ruleset_index: int) -> None:
        """
        Remove a ruleset embed.
        This command can be used only if the server already has rules.

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        Access the ruleset embed from the index from message.embeds.
        pop the ruleset embed from the embeds list.
        Log previous embeds.
        Load the ruleset embed to memory.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        if ruleset_index >= len(self.server_rule_message_embeds_info_dict_list):
            await interaction.response.send_message('Ruleset index out of range.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_ruleset_by_index with parameters: ruleset_index={ruleset_index}.',
                channel=interaction.channel,
                event=None,
                outcome='Ruleset index out of range.')
            return
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_ruleset_by_index with parameters: ruleset_index={ruleset_index}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_ruleset_by_index with parameters: ruleset_index={ruleset_index}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        # Remove the ruleset embed from the embeds list.
        embeds = message.embeds
        embeds.pop(ruleset_index)

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
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Remove the ruleset embed from the self.server_rule_message_embeds_info_dict_list
        self.server_rule_message_embeds_info_dict_list.pop(ruleset_index)

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

        # Send a message to the user saying that the ruleset has been deleted.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Ruleset deleted.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called remove_ruleset_by_index with parameters: ruleset_index={ruleset_index}.',
            channel=interaction.channel,
            event=None,
            outcome='Success.')

    @remove_ruleset_by_index.error
    async def remove_ruleset_by_indexError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for remove_ruleset_by_index command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_ruleset_by_index.',
                channel=interaction.channel,
                event=None,
                outcome='User does not have any of the required roles.')

    @app_commands.command(
        name='remove_field',
        description='Remove a field')
    @app_commands.describe(
        ruleset_and_field='Name of field')
    @app_commands.autocomplete(ruleset_and_field=fields_autocomplete)
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def remove_field(
            self,
            interaction: discord.Interaction,
            ruleset_and_field: str) -> None:
        """
        Remove the chosen field of a ruleset embed.
        This command can be used only if the server already has rules.

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        Find index of ruleset AND index of field.
        Access the ruleset embed from the index from message.embeds.
        embed.remove_field(index of field)
        Check if embeds are too long (due to username in footer), if so, send a message saying that.
        Log previous embeds.
        Load the ruleset embed to memory.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        possible_ruleset_and_fields = [f"{embed_info_dict['title']} - {field['name']} ({i},{j})" for i, embed_info_dict
                                       in enumerate(self.server_rule_message_embeds_info_dict_list, 1) for j, field in
                                       enumerate(embed_info_dict['fields'], 1)]

        if ruleset_and_field not in possible_ruleset_and_fields:
            await interaction.response.send_message('Invalid ruleset title.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field with parameters: ruleset_and_field={ruleset_and_field}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid ruleset title.')
            return
        ruleset_index = 0
        field_index = 0
        for i in range(len(self.server_rule_message_embeds_info_dict_list)):
            for j in range(len(self.server_rule_message_embeds_info_dict_list[i]['fields'])):
                if ruleset_and_field == f"{self.server_rule_message_embeds_info_dict_list[i]['title']} - {self.server_rule_message_embeds_info_dict_list[i]['fields'][j]['name']} ({i + 1},{j + 1})":
                    ruleset_index = i
                    field_index = j
                    break
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field with parameters: ruleset_and_field={ruleset_and_field}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field with parameters: ruleset_and_field={ruleset_and_field}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        # Remove the field from the embed
        embeds = message.embeds
        embed = embeds[ruleset_index]
        embed.remove_field(field_index)
        embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        embed.timestamp = datetime.datetime.now()

        if embed_surpassed_limit(embeds):
            await interaction.response.send_message(
                'Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.\n(In this case it\'s probably your username is too long in the footer)',
                ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field with parameters: ruleset_and_field={ruleset_and_field}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed (too many embeds or too many characters)')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Remove the field from the embed
        editing_embed = self.server_rule_message_embeds_info_dict_list[ruleset_index]
        editing_embed['fields'].pop(field_index)

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

        # Send a message to the user saying that the field has been removed.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Field removed.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called remove_field with parameters: ruleset_and_field={ruleset_and_field}.',
            channel=interaction.channel,
            event=None,
            outcome='Field removed.')

    @remove_field.error
    async def remove_fieldError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for remove_field command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field.',
                channel=interaction.channel,
                event=None,
                outcome='Missing required role.')

    @app_commands.command(
        name='remove_field_by_index',
        description='Remove a field (index starts on 0)')
    @app_commands.describe(
        ruleset_index='Ruleset/embed index (index starts on 0)',
        field_index='Field index (index starts on 0)')
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def remove_field_by_index(
            self,
            interaction: discord.Interaction,
            ruleset_index: int,
            field_index: int) -> None:
        """
        Remove the chosen field of a ruleset embed.
        This command can be used only if the server already has rules.

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        embed.remove_field(index of field)
        Check if embeds are too long (due to username in footer), if so, send a message saying that.
        Log previous embeds.
        Load the ruleset embed to memory.
        Edit the server rules message to replace the old ruleset embed with the new ruleset embed.
        Write to csv file. Since this could be in the middle of the file, we need to write the whole ruleset again.
        """
        if ruleset_index >= len(self.server_rule_message_embeds_info_dict_list):
            await interaction.response.send_message('Ruleset index out of range.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field_by_index with parameters: ruleset_index={ruleset_index}, field_index={field_index}.',
                channel=interaction.channel,
                event=None,
                outcome='Ruleset index out of range.')
            return

        if field_index >= len(self.server_rule_message_embeds_info_dict_list[ruleset_index]['fields']):
            await interaction.response.send_message('Field index out of range.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field_by_index with parameters: ruleset_index={ruleset_index}, field_index={field_index}.',
                channel=interaction.channel,
                event=None,
                outcome='Field index out of range.')
            return

        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field_by_index with parameters: ruleset_index={ruleset_index}, field_index={field_index}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have a rules message linked to the bot yet.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field_by_index with parameters: ruleset_index={ruleset_index}, field_index={field_index}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        # Remove the field from the embed
        embeds = message.embeds
        embed = embeds[ruleset_index]
        embed.remove_field(field_index)
        embed.set_footer(
            text=f'Last updated by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
        embed.timestamp = datetime.datetime.now()

        if embed_surpassed_limit(embeds):
            await interaction.response.send_message(
                'Embed limit surpassed (too many embeds or too many characters)\nThe max number of embeds is 10 and the max number of characters is 6000.\n(In this case it\'s probably your username is too long in the footer)',
                ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field_by_index with parameters: ruleset_index={ruleset_index}, field_index={field_index}.',
                channel=interaction.channel,
                event=None,
                outcome='Embed limit surpassed (too many embeds or too many characters)')
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
            embed.colour = discord.Colour.from_str(embed_info_dict['colour']) if embed_info_dict[
                'colour'] else None
            for field in embed_info_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=False)
            embed.set_footer(
                # This tells us who updated the rules and when
                text=f'Before update by {interaction.user.name + (("#" + interaction.user.discriminator) if len(interaction.user.discriminator) > 1 else "")}: ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
            embed.timestamp = datetime.datetime.now()
            previous_rules_embeds.append(embed)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        # Send log message, mention it is a rule change.
        await log_channel.send(content=f'**Server Rule Changed:**')
        await log_channel.send(content=self.server_rule_message_content, embeds=previous_rules_embeds)

        # Remove the field from the embed
        editing_embed = self.server_rule_message_embeds_info_dict_list[ruleset_index]
        editing_embed['fields'].pop(field_index)

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

        # Send a message to the user saying that the field has been removed.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message('Field removed.', ephemeral=True, view=url_view)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called remove_field_by_index with parameters: ruleset_index={ruleset_index}, field_index={field_index}.',
            channel=interaction.channel,
            event=None,
            outcome='Field removed.')

    @remove_field_by_index.error
    async def remove_field_by_indexError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for remove_field command.
        Currently only handles MissingAnyRole error, where the user does not have any of the required roles.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message('You need to be an administrator to use this command.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called remove_field.',
                channel=interaction.channel,
                event=None,
                outcome='Missing required role.')

    @app_commands.command(
        name='display_rule',
        description='Display a rule for 2 minutes')
    @app_commands.describe(
        rule_name='The ruleset and title of the rule to display')
    @app_commands.autocomplete(rule_name=fields_autocomplete)
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.cooldown(1, 10.0)
    async def display_rule(
            self,
            interaction: discord.Interaction,
            rule_name: str) -> None:
        """
        Display the chosen rule for 2 minutes.
        Display embed includes:
            Author, thumbnail, Colour, Title, Field, Footnote

        Check if the server has rules, if not, send a message saying that the server does not have rules.
        Check if server rules message still exists, if not, send a message saying that.
        Find index of ruleset AND index of field.
        Load that embed from the rules message
        Create new embed with Author, thumbnail, colour, title, field, footnote, timestamp
        Display it with delete_after=300
        """
        possible_ruleset_and_fields = [f"{embed_info_dict['title']} - {field['name']} ({i},{j})" for i, embed_info_dict
                                       in enumerate(self.server_rule_message_embeds_info_dict_list, 1) for j, field in
                                       enumerate(embed_info_dict['fields'], 1)]

        if rule_name not in possible_ruleset_and_fields:
            await interaction.response.send_message('Invalid rule name.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called display_rule with parameters: rule_name={rule_name}.',
                channel=interaction.channel,
                event=None,
                outcome='Invalid rule name.')
            return
        ruleset_index = 0
        field_index = 0
        for i in range(len(self.server_rule_message_embeds_info_dict_list)):
            for j in range(len(self.server_rule_message_embeds_info_dict_list[i]['fields'])):
                if rule_name == f"{self.server_rule_message_embeds_info_dict_list[i]['title']} - {self.server_rule_message_embeds_info_dict_list[i]['fields'][j]['name']} ({i + 1},{j + 1})":
                    ruleset_index = i
                    field_index = j
                    break
        # Check if the server has rules, if not, send a message saying that the server does not have rules.
        if not self.server_has_rule:
            await interaction.response.send_message('Server does not have a rules message linked to the bot yet.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called display_rule with parameters: rule_name={rule_name}.',
                channel=interaction.channel,
                event=None,
                outcome='Server does not have rules.')
            return

        try:
            channel = self.bot.get_channel(self.server_rule_channel_id)
            message = await channel.fetch_message(self.server_rule_message_id)
        except discord.errors.NotFound:
            await interaction.response.send_message('Server rules message not found.', ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called display_rule with parameters: rule_name={rule_name}.',
                channel=interaction.channel,
                event=None,
                outcome='Server rules message not found.')
            self.server_has_rule = False
            return

        embeds = message.embeds
        embed = embeds[ruleset_index]

        display_embed = discord.Embed(title=embed.title)
        display_embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        display_embed.set_thumbnail(url=embed.thumbnail.url)
        display_embed.colour = embed.colour
        display_embed.add_field(name=embed.fields[field_index].name, value=embed.fields[field_index].value, inline=False)
        display_embed.set_footer(text=f'Rule display should disappear after 2 minutes: ({(datetime.datetime.now()+datetime.timedelta(minutes=2)).astimezone().tzinfo.tzname((datetime.datetime.now()+datetime.timedelta(minutes=2)).astimezone())})')
        display_embed.timestamp = datetime.datetime.now()+datetime.timedelta(minutes=2)

        # Send a message to the user saying that the field has been edited.
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Go to Rules Message', style=discord.ButtonStyle.url, url=message.jump_url))
        await interaction.response.send_message(embed=display_embed, view=url_view, delete_after=120)
        await self.bot.log(
            cog=self,
            user=interaction.user,
            user_action=f'Called display_rule with parameters: rule_name={rule_name}.',
            channel=interaction.channel,
            event=None,
            outcome='Displayed rule.')

    @display_rule.error
    async def display_ruleError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        """
        Error handler for insert_new_field_before command.
        Currently only handles CommandOnCooldown error, where the user tried to use the command before the cooldown is up.
        """
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message('Command is on cooldown. Please try again later.',
                                                    ephemeral=True)
            await self.bot.log(
                cog=self,
                user=interaction.user,
                user_action=f'Called display_rule.',
                channel=interaction.channel,
                event=None,
                outcome='Command is on cooldown.')


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        ServerRulesCog(bot),
        guilds=[discord.Object(id=SERVER_ID)])
