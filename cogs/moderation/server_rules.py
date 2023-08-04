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


class ServerRulesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        When bot is ready, load the server rules from the server_rules file
        If no file exists, mark the server doesn't have rules yet.
        Check if the server rules message exists in the server, if not, mark the server doesn't have rules yet.
        """
        pass
    # TODO: ANY EDITS TO THE RULES WILL ADD FOOTER OF WHO EDITED AND WHEN AND TIMEZONE
    # TODO: AUTHOR WILL ALWAYS BE THE BOT
    # TODO: BEFORE ANY COMMAND CALL, CHECK IF SERVER HAS RULES + CHECK IF RULE MESSAGE EXISTS, IF NOT MARK SERVER DOESN'T HAVE RULES YET
    # TODO: one command to link_existing_rules
    #     This command can be used even if the server already has rules (overwrite)
    #     Takes input an message link
    #     Checks if the message exists in the server
    #     Checks if the message fulfills the format of a server rules message
    #       (one string, one or more embeds. Each embed has minimum title+description+fields)
    #       (prefer having author+icon, timestamp, footer, thumbnail, color)
    #     If all checks pass, save the message content to the server_rules file and mark the server has rules (remember channel_id/message_id)
    #     If any check fails, send a message to the user with the reason of failure
    # TODO: one command to create_rules (if no rules exist)
    #     This command can be used only if the server doesn't have rules yet
    #     Takes input a channel, a message_content
    # TODO: multiple command to add to current rules
    #     if along any point there's an error, send a message to the user with the reason of failure
    #     This command can be used only if the server already has rules
    #     Takes input a type of addition DIFFERENT COMMANDS UNDER ONE GROUP /server_rules ...
    #     user inputs:
    #         add_new_ruleset: Name of ruleset, description of ruleset
    #         remove_existing_ruleset: select from existing ruleset titles
    #         insert_new_ruleset_before: select from existing ruleset titles, new_ruleset_title, new_ruleset_description
    #         edit_rule_embed_thumbnail: select from existing ruleset titles, thumbnail_url
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