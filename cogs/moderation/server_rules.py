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
            'yellow': discord.Colour.yellow()
        }

    @commands.Cog.listener()
    async def on_ready(self):
        """
        When bot is ready, load the server rules from the server_rules file
        If no file exists, mark the server doesn't have rules yet.
        Check if the server rules message exists in the server, if not, mark the server doesn't have rules yet.
        """
        curr_dir = os.path.abspath(os.path.dirname(__file__))
        self.moderation_dir = os.path.join(curr_dir, '..', '..', 'data', 'moderation')
        self.server_rules_csv_full_path = os.path.join(self.moderation_dir, 'server_rules.csv')
        if not os.path.isfile(self.server_rules_csv_full_path):
            # File does not exist
            os.makedirs(self.moderation_dir, exist_ok=True)
            with open(self.server_rules_csv_full_path, 'w') as file:
                # Write header: value_name, value
                file.write('value_name,value\n')

        with open(self.server_rules_csv_full_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[0] == 'channel_id':
                    self.server_rule_channel_id = int(row[1])
                elif row[0] == 'message_id':
                    self.server_rule_message_id = int(row[1])
                elif row[0] == 'message_content':
                    self.server_rule_message_content = row[1]
                elif row[0] == 'embed_title':
                    self.server_rule_message_embeds_info_dict_list.append({
                        'title': row[1],
                        'description': None,
                        'thumbnail_url': None,
                        'colour': None,
                        'fields': []
                    })
                elif row[0] == 'embed_description':
                    self.server_rule_message_embeds_info_dict_list[-1]['description'] = row[1]
                elif row[0] == 'embed_thumbnail_url':
                    self.server_rule_message_embeds_info_dict_list[-1]['thumbnail_url'] = row[1]
                elif row[0] == 'embed_colour':
                    self.server_rule_message_embeds_info_dict_list[-1]['colour'] = row[1]
                elif row[0] == 'embed_field_name':
                    self.server_rule_message_embeds_info_dict_list[-1]['fields'].append({
                        'name': row[1],
                        'value': None
                    })
                elif row[0] == 'embed_field_value':
                    self.server_rule_message_embeds_info_dict_list[-1]['fields'][-1]['value'] = row[1]

        if self.server_rule_channel_id is not None and self.server_rule_message_id is not None:
            # Check if the message exists in the server
            channel = self.bot.get_channel(self.server_rule_channel_id)
            if channel is not None:
                message = await channel.fetch_message(self.server_rule_message_id)
                if message is not None and message.author == self.bot.user:
                    # Message exists and is by the bot
                    self.server_has_rule = True
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
            Choice(name="Use This Message As Rules", value="this_message"),
            Choice(name="Use Stored Rules", value="overwrite")])
    @app_commands.guilds(SERVER_ID)
    @app_commands.checks.has_any_role(*ADMINISTRATION_ROLES_IDS)
    async def set_rules_to_existing_message(
            self,
            interaction: discord.Interaction,
            channel: discord.TextChannel,
            message_id: int,
            set_action: str) -> None:
        """
        Set an existing message sent by the bot as the server rules message.
        Check if the message exists in the server.
        Check if the message is sent by the bot.
        If checks pass, check if set_action is 'this_message' or 'overwrite'.
            If set_action is 'this_message', set the message as the server rules message.
                Save all contents of the message to memory. Write to the server_rules file.
            If set_action is 'overwrite', overwrite the message with the server rules message.

        TODO add an error handler for all the checks above.
        """
        # check if message exists in the server
        message = await channel.fetch_message(message_id)
        if message is None:
            await interaction.response.send_message('Message does not exist in the .', ephemeral=True)
            return
        if message.author != self.bot.user:
            await interaction.response.send_message('Message is not sent by the bot.', ephemeral=True)
            return
        if set_action == 'this_message':
            # TODO write to memory and csv file
            # get all embeds of the message, save message content, save embeds
            pass
        elif set_action == 'overwrite':
            self.server_rule_channel_id = channel.id
            self.server_rule_message_id = message.id
            # TODO write to csv file
            embeds = []
            for embed_info_dict in self.server_rule_message_embeds_info_dict_list:
                embed = discord.Embed()
                embed.title = embed_info_dict['title']
                if embed_info_dict['description']:
                    embed.description = embed_info_dict['description']
                if embed_info_dict['thumbnail_url']:
                    embed.set_thumbnail(url=embed_info_dict['thumbnail_url'])
                if embed_info_dict['colour']:
                    embed.colour = self.colour_dict[embed_info_dict['colour']]
                for field in embed_info_dict['fields']:
                    embed.add_field(name=field['name'], value=field['value'], inline=False)
                embed.set_footer(text=f'Last updated ({datetime.datetime.now().astimezone().tzinfo.tzname(datetime.datetime.now().astimezone())})')
                embed.timestamp = datetime.datetime.now()
                embeds.append(embed)
            await message.edit(content=self.server_rule_message_content, embeds=embeds)
            await interaction.response.send_message('Server rules message set (overwritten from stored rules).', ephemeral=True)

    @set_rules_to_existing_message.error
    async def set_rules_to_existing_messageError(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError):
        # TODO: error handling
        pass

    # @app_commands.command(
    #     name='create_new_rules_message',
    #     description='Create a new message to be used as the server rules message.')
    # NOTE: have also have an option: create blank message or create message with stored rules



    # TODO: ANY EDITS TO THE RULES WILL ADD FOOTER OF WHO EDITED AND WHEN AND TIMEZONE
    # TODO: AUTHOR WILL ALWAYS BE THE BOT
    # TODO: BEFORE ANY COMMAND CALL, CHECK IF SERVER HAS RULES + CHECK IF RULE MESSAGE EXISTS, IF NOT MARK SERVER DOESN'T HAVE RULES YET

    # TODO: one command to create_rules (if no rules exist)
    #     This command can be used only if the server doesn't have rules yet
    #     Takes input a channel.
    #     The bot will send a message to the channel. If the rules file already contains info, the bot sends that message.

    # TODO: multiple command to add to current rules
    #     if along any point there's an error, send a message to the user with the reason of failure
    #     This command can be used only if the server already has rules
    #     Takes input a type of addition DIFFERENT COMMANDS UNDER ONE GROUP /server_rules ...
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