import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import datetime


load_dotenv()
SERVER_ID = int(os.getenv('SERVER_ID'))
BANNED_ROLE_ID = int(os.getenv('BANNED_ROLE_ID'))
ADMINISTRATION_ROLES_IDS = [int(role_id) for role_id in os.getenv('ADMINISTRATION_ROLES_IDS').split(',')]
REASON_OF_BAN_CHANNEL_ID = int(os.getenv('REASON_OF_BAN_CHANNEL_ID'))
AUTO_BAN_NUMBER_OF_REPEAT_IN_SAME_CHANNEL = int(os.getenv('AUTO_BAN_NUMBER_OF_REPEAT_IN_SAME_CHANNEL'))
AUTO_BAN_NUMBER_OF_DIFFERENT_CHANNEL_REPEAT = int(os.getenv('AUTO_BAN_NUMBER_OF_DIFFERENT_CHANNEL_REPEAT'))
AUTO_BAN_CHARACTER_LENGTH_MINIMUM = int(os.getenv('AUTO_BAN_CHARACTER_LENGTH_MINIMUM'))
AUTO_BAN_DETECTION_PERIOD_MINUTES = int(os.getenv('AUTO_BAN_DETECTION_PERIOD_MINUTES'))
AUTO_BAN_NEW_USER_THRESHOLD_SECONDS = int(os.getenv('AUTO_BAN_NEW_USER_THRESHOLD_SECONDS'))


class AutoBanningCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild = None
        self.user_messages_dict = {}
        self.banned_users_id_list = []
        self.banned_users_timestamp_dict = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.bot.get_guild(SERVER_ID)
        self.user_messages_dict = {}
        self.banned_users_id_list = []
        self.banned_users_timestamp_dict = {}
        await self.bot.log(
            cog=self,
            user=None,
            user_action=None,
            channel=None,
            event='AutoBanningCog is ready.',
            outcome=None)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Whenever a user sends a message, check if they have sent:
            - repeating messages in repeat_message_in_different_channel_threshold or more channels in the last time_threshold_minutes minutes
            - repeating messages in same channel for repeat_message_in_same_channel_threshold or more times in the last time_threshold_minutes minutes
        Here repeating message:
            - any message that has same content, and is >= character_length_minimum_threshold characters long
            - any message that has same attachment
            - any message that has a link to the same website
        We would be ignoring messages sent by moderators and administrators.
        It was tricky to figure out async with this, but essentially we update internal variables before any await.
        If a message was sent between the time we initiate giving @banned and the time actually receive @banned,
            we always delete the message.
        Also, we ban users who send message with link or attachment within new_user_ban_threshold_seconds seconds of joining the server. (likely bots)
        """
        repeat_message_in_same_channel_threshold = AUTO_BAN_NUMBER_OF_REPEAT_IN_SAME_CHANNEL
        repeat_message_in_different_channel_threshold = AUTO_BAN_NUMBER_OF_DIFFERENT_CHANNEL_REPEAT
        character_length_minimum_threshold = AUTO_BAN_CHARACTER_LENGTH_MINIMUM
        time_threshold_minutes = AUTO_BAN_DETECTION_PERIOD_MINUTES
        new_user_ban_threshold_seconds = AUTO_BAN_NEW_USER_THRESHOLD_SECONDS

        author_id = message.author.id

        # ignore messages sent by the bot
        if message.author == self.bot.user:
            return

        # ignore messages if message.author isn't type Member
        if not isinstance(message.author, discord.Member):
            return

        if self.guild.get_member(author_id).roles:
            for role in self.guild.get_member(author_id).roles:
                # ignore messages sent by users with administration roles
                if role.id in ADMINISTRATION_ROLES_IDS:
                    return
                # completely ignore messages sent by users with banned role but not in banned_users_id_list
                if role.id == BANNED_ROLE_ID and author_id not in self.banned_users_id_list:
                    return

        # check if user is in banned_users_id_list
        if author_id in self.banned_users_id_list:
            # check if message is sent before the timestamp
            if (message.created_at < self.banned_users_timestamp_dict[author_id]) if author_id in self.banned_users_timestamp_dict else True:
                # delete message
                await message.delete()
                # log
                await self.bot.log(
                    cog=self,
                    user=message.author,
                    user_action='sent a message',
                    channel=message.channel,
                    event='user sent another message when user just got banned, but not yet receiving the banned role',
                    outcome='deleted the message')
                return
            else:
                return

        # check if the message fulfills the criteria of repeating message
        if not (len(message.content) >= character_length_minimum_threshold or message.attachments or 'http' in message.content):
            # No need to check if the message is not a repeating message
            return

        # Perform the check for new member sending attachment / link
        if message.attachments or 'http' in message.content:
            # if member joined less than 1 minute ago, ban them
            if (discord.utils.utcnow() - message.author.joined_at).total_seconds() < new_user_ban_threshold_seconds:
                self.banned_users_id_list.append(author_id)
                # timestamp of 1 day later - stop deleting user's messages after 1 day
                self.banned_users_timestamp_dict[author_id] = discord.utils.utcnow() + datetime.timedelta(days=1)
                # give user banned role
                await self.guild.get_member(author_id).add_roles(discord.Object(id=BANNED_ROLE_ID))
                # log
                await self.bot.log(
                    cog=self,
                    user=self.guild.get_member(author_id),
                    user_action=None,
                    channel=message.channel,
                    event=f'User {self.guild.get_member(author_id).mention} joined less than {new_user_ban_threshold_seconds} seconds ago, and sent a the message: {message.content} with attachment or link',
                    outcome='Banned')
                # tell user they are banned
                reason_of_ban_channel = self.guild.get_channel(REASON_OF_BAN_CHANNEL_ID)
                # Load all attachments to files so they can be sent
                attachments = [await attachment.to_file() for attachment in message.attachments]
                await reason_of_ban_channel.send(
                    f'{self.guild.get_member(author_id).mention}\nReason -- sending suspicious message:\n{message.content}\nwith attachment or link within {new_user_ban_threshold_seconds} seconds of joining the server.', files=attachments)
                # set the timestamp to right now - as we are now sure the user is properly banned
                self.banned_users_timestamp_dict[author_id] = discord.utils.utcnow()
                await message.delete()
                await self.bot.log(
                    cog=self,
                    user=message.author,
                    user_action='sent a message',
                    channel=message.channel,
                    event=f'user sent a message with attachment or link within {new_user_ban_threshold_seconds} seconds of joining the server',
                    outcome='deleted the message')
                return

        # Due to a recent accidental ban (someone sent different images, but got flagged as "spam" because there are
        #   no content in the image message, so the system thought they were "same" message)
        # Also, we don't need to ban people for sending a lot of attachments since this is a slow way of spamming.
        # This block is placed after the new user check so that new users can still be banned for sending attachments
        if message.attachments and not message.content:
            # don't care about attachments with NO text
            return

        # load the message
        if author_id in self.user_messages_dict:
            self.user_messages_dict[author_id].append(message)
        else:
            self.user_messages_dict[author_id] = [message]
        for message_in_list in self.user_messages_dict[author_id]:
            # Remove messages from over time_threshold_minutes minutes ago. Assume the message is already sorted by time
            if message.created_at - message_in_list.created_at > datetime.timedelta(minutes=time_threshold_minutes):
                self.user_messages_dict[author_id].remove(message_in_list)

        # check if user has sent repeating messages in same channel for n or more times in the last m minutes
        # also track number of channels each message appears in
        message_channel_repeats_dict = {}
        for channel in self.guild.text_channels:
            counts_dict = {}
            for message_in_list in self.user_messages_dict[author_id]:
                # if message has link, only count the link, cuz link will repeat >= times the message includes it
                if 'http://' in message_in_list.content or 'https://' in message_in_list.content:
                    for chunk in message_in_list.content.split():
                        if 'http://' in chunk or 'https://' in chunk:
                            if chunk in message_channel_repeats_dict:
                                message_channel_repeats_dict[chunk].add(message_in_list.channel.id)
                            else:
                                message_channel_repeats_dict[chunk] = {message_in_list.channel.id}
                            if message_in_list.channel == channel:
                                counts_dict[chunk] = counts_dict.get(chunk, 0) + 1
                # Recent change: record the message itself even if there's link. Since we might want the full context
                if message_in_list.content in message_channel_repeats_dict:
                    message_channel_repeats_dict[message_in_list.content].add(message_in_list.channel.id)
                else:
                    message_channel_repeats_dict[message_in_list.content] = {message_in_list.channel.id}
                if message_in_list.channel == channel:
                    counts_dict[message_in_list.content] = counts_dict.get(message_in_list.content, 0) + 1

            # check if condition is met. Do this sorted thing to make sure the longest message is deleted first
            for message_content in sorted(counts_dict, key=lambda x: len(x), reverse=True):
                message_count = counts_dict[message_content]
                if message_count >= repeat_message_in_same_channel_threshold:
                    self.banned_users_id_list.append(author_id)
                    # timestamp of 1 day later - stop deleting user's messages after 1 day
                    self.banned_users_timestamp_dict[author_id] = discord.utils.utcnow() + datetime.timedelta(days=1)
                    # give user banned role
                    await self.guild.get_member(author_id).add_roles(discord.Object(id=BANNED_ROLE_ID))
                    # log
                    await self.bot.log(
                        cog=self,
                        user=self.guild.get_member(author_id),
                        user_action=None,
                        channel=channel,
                        event=f'User {self.guild.get_member(author_id).mention} sent repeating message {message_content} {message_count} times in last {time_threshold_minutes} minutes in the same channel.',
                        outcome='Banned')
                    # tell user they are banned
                    reason_of_ban_channel = self.guild.get_channel(REASON_OF_BAN_CHANNEL_ID)
                    await reason_of_ban_channel.send(
                        f'{self.guild.get_member(author_id).mention}\nReason -- sending repeating message:\n{message_content}\nmultiple times in the same channel.')
                    # set the timestamp to right now - as we are now sure the user is properly banned
                    self.banned_users_timestamp_dict[author_id] = discord.utils.utcnow()

                    # delete the banned messages
                    for message_in_list in self.user_messages_dict[author_id]:
                        if message_in_list.channel == channel:
                            if 'http://' in message_in_list.content or 'https://' in message_in_list.content:
                                for chunk in message_in_list.content.split():
                                    if 'http://' in chunk or 'https://' in chunk:
                                        if chunk == message_content:
                                            try:
                                                await message_in_list.delete()
                                            except discord.errors.NotFound:
                                                pass
                            else:
                                # For this, it's not necessary to make additional checks. since full message is subset
                                # of message with this link
                                if message_in_list.content == message_content:
                                    try:
                                        await message_in_list.delete()
                                    except discord.errors.NotFound:
                                        pass

                    await self.bot.log(
                        cog=self,
                        user=self.guild.get_member(author_id),
                        user_action=None,
                        channel=channel,
                        event=f'Deleted repeating message {message_content} {message_count} times in last {time_threshold_minutes} minutes in the same channel.',
                        outcome=None)
                    # delete record of the banned messages
                    del self.user_messages_dict[author_id]
                    return

        # now check if user has sent repeating messages in 3 or more channels in the last time_threshold_minutes minutes
        # Also sort by length of message to make sure the longest message is deleted first
        for message_content in sorted(message_channel_repeats_dict, key=lambda x: len(x), reverse=True):
            channel_ids = message_channel_repeats_dict[message_content]
            if len(channel_ids) >= repeat_message_in_different_channel_threshold:
                self.banned_users_id_list.append(author_id)
                # timestamp of 1 day later - stop deleting user's messages after 1 day
                self.banned_users_timestamp_dict[author_id] = discord.utils.utcnow() + datetime.timedelta(days=1)
                # give user banned role
                await self.guild.get_member(author_id).add_roles(discord.Object(id=BANNED_ROLE_ID))
                # log
                await self.bot.log(
                    cog=self,
                    user=self.guild.get_member(author_id),
                    user_action=None,
                    channel=message.channel,
                    event=f'User {self.guild.get_member(author_id).mention} sent repeating message {message_content} in {len(channel_ids)} channels in last {time_threshold_minutes} minutes.',
                    outcome='Banned')
                # tell user they are banned
                reason_of_ban_channel = self.guild.get_channel(REASON_OF_BAN_CHANNEL_ID)
                await reason_of_ban_channel.send(
                    f'{self.guild.get_member(author_id).mention}\nReason -- sending repeating message:\n{message_content}\nin multiple channels.')
                # set the timestamp to right now - as we are now sure the user is properly banned
                self.banned_users_timestamp_dict[author_id] = discord.utils.utcnow()

                # delete the banned messages
                for message_in_list in self.user_messages_dict[author_id]:
                    if 'http://' in message_in_list.content or 'https://' in message_in_list.content:
                        for chunk in message_in_list.content.split():
                            if 'http://' in chunk or 'https://' in chunk:
                                if chunk == message_content:
                                    try:
                                        await message_in_list.delete()
                                    except discord.errors.NotFound:
                                        pass
                    else:
                        if message_in_list.content == message_content:
                            try:
                                await message_in_list.delete()
                            except discord.errors.NotFound:
                                pass

                await self.bot.log(
                    cog=self,
                    user=self.guild.get_member(author_id),
                    user_action=None,
                    channel=None,
                    event=f'Deleted repeating message {message_content} in {len(channel_ids)} channels in last {time_threshold_minutes} minutes.',
                    outcome=None)
                # delete record of the banned messages
                del self.user_messages_dict[author_id]
                return

    # on role add
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """When a user is unbanned (having @banned removed), record this and update variables."""
        if BANNED_ROLE_ID in [role.id for role in before.roles] and BANNED_ROLE_ID not in [role.id for role in after.roles]:
            if after.id in self.user_messages_dict:
                del self.user_messages_dict[after.id]
            if after.id in self.banned_users_id_list:
                self.banned_users_id_list.remove(after.id)
            await self.bot.log(
                cog=self,
                user=after,
                user_action=None,
                channel=None,
                event=f'User {after.mention} was unbanned.',
                outcome=None)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        AutoBanningCog(bot),
        guilds=[discord.Object(id=SERVER_ID)])
