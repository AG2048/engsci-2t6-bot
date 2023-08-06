import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from typing import Optional
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
        Any values that are empty will be set to None, except for the message_content, which will be set to 'none'
            (to avoid the bot sending an empty message)
        Check if the message exists in the channel and if the author is the bot.
            If any is false, mark the server doesn't have rules yet. (but we don't delete the existing rules info)
        If all is true, mark the server has rules.
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
                        'title': row[1] if len(row[1]) > 0 else None,
                        'description': None,
                        'thumbnail_url': None,
                        'colour': None,
                        'fields': []
                    })
                elif row[0] == 'embed_description':
                    self.server_rule_message_embeds_info_dict_list[-1]['description'] = row[1] if len(row[1]) > 0 else None
                elif row[0] == 'embed_thumbnail_url':
                    self.server_rule_message_embeds_info_dict_list[-1]['thumbnail_url'] = row[1] if len(row[1]) > 0 else None
                elif row[0] == 'embed_colour':
                    # Colours are all stored as hex strings, so we need to convert them to discord.Colour objects
                    # We can later do this by discord.Colour.from_str(hex_string)
                    # Do note that None is a valid colour, so we need to check for that
                    self.server_rule_message_embeds_info_dict_list[-1]['colour'] = row[1] if len(row[1]) > 0 else None
                elif row[0] == 'embed_field_name':
                    self.server_rule_message_embeds_info_dict_list[-1]['fields'].append({
                        'name': row[1] if len(row[1]) > 0 else None,
                        'value': None
                    })
                elif row[0] == 'embed_field_value':
                    self.server_rule_message_embeds_info_dict_list[-1]['fields'][-1]['value'] = row[1] if len(row[1]) > 0 else None

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
        description='Set an existing message sent by the bot as the server rules message. If existing rules will be overwritten, the bot will log the existing rules in the log channel.')
    @app_commands.describe(
        channel='The channel where the message is located.',
        message_id='The message ID of the message to be set as the server rules message.',
        set_action='Whether to use this message as the server rules or to overwrite this message with existing server rules stored in the bot.')
    @app_commands.choices(
        set_action=[
            Choice(name="Use This Message As Rules", value="this_message"),
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

        # Checks passed, set server has rule to True
        self.server_has_rule = True

        if set_action == 'this_message':
            # If set_action is 'this_message', set the message and its contents as the server rules message

            # Log previous rules message in the log channel
            previous_rules_embeds = []
            for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
                embed = discord.Embed()
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

            # Update server rules message in memory
            self.server_rule_channel_id = channel.id
            self.server_rule_message_id = message.id
            # Make sure the message content is not empty, otherwise it will be 'none'
            self.server_rule_message_content = message.content if len(message.content) > 0 else 'none'
            self.server_rule_message_embeds_info_dict_list = []
            for embed in message.embeds:
                embed_info_dict = {
                    'title': embed.title,
                    'description': embed.description,
                    'thumbnail_url': embed.thumbnail.url,
                    # Colour.value can be converted to a hex string. Or it can be None.
                    'colour': hex(embed.colour.value) if embed.colour is not None else None,  # Convert colour to hex
                    'fields': []
                }
                for field in embed.fields:
                    embed_info_dict['fields'].append({
                        'name': field.name,
                        'value': field.value
                    })
                self.server_rule_message_embeds_info_dict_list.append(embed_info_dict)
            # Send success message
            await interaction.response.send_message('Server rules set to this message (using this message as new rules).', ephemeral=True)

        elif set_action == 'overwrite':
            # If set_action is 'overwrite', overwrite the message with the server rules message

            # This action only changes the id of the message, so we don't need to log the previous rules message.
            self.server_rule_channel_id = channel.id
            self.server_rule_message_id = message.id
            embeds = []
            for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
                embed = discord.Embed()
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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        ServerRulesCog(bot),
        guilds=[discord.Object(id=SERVER_ID)])