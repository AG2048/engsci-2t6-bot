import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import csv


load_dotenv()
SERVER_ID = int(os.getenv('SERVER_ID'))
ADMINISTRATION_ROLES_IDS = [int(role_id) for role_id in os.getenv('ADMINISTRATION_ROLES_IDS').split(',')]
DO_NOT_RE_GIVE_ROLES_IDS = [int(role_id) for role_id in os.getenv('DO_NOT_RE_GIVE_ROLES_IDS').split(',')]

class LeavingMemberRoleLoggingAndRegivingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.moderation_dir = None
        self.left_users_roles_csv_full_path = None
        self.users_ids_roles_ids = {}

    @commands.Cog.listener()
    async def on_ready(self):
        """
        On ready, check of a role logging file exists, if not, create it.
        Load the file into memory. Newer entries about the same user will overwrite older entries.
        """

        """
        The role logging file is a csv file with the following format:
        user_id,role_ids
        <USER_ID>,"<ROLE_ID_1>,<ROLE_ID_2>,<ROLE_ID_3>,<ROLE_ID_4>,<ROLE_ID_5>"
        <USER_ID>,"<ROLE_ID_1>,<ROLE_ID_2>"
        <USER_ID>,"<ROLE_ID_1>"
        """

        # Get file path
        curr_dir = os.path.abspath(os.path.dirname(__file__))
        self.moderation_dir = os.path.join(curr_dir, '..', '..', 'data', 'moderation')
        self.left_users_roles_csv_full_path = os.path.join(self.moderation_dir, 'left_users_roles.csv')

        # Check if file exists
        if not os.path.isfile(self.left_users_roles_csv_full_path):
            # File does not exist
            os.makedirs(self.moderation_dir, exist_ok=True)
            with open(self.left_users_roles_csv_full_path, 'w') as file:
                # Write header: user_id, role_ids
                file.write('user_id,role_ids\n')

        # Load file into memory
        with open(self.left_users_roles_csv_full_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                # This way of storing the data will overwrite older entries about the same user
                self.users_ids_roles_ids[int(row[0])] = [int(role_id) for role_id in row[1].split(',')] if len(row[1]) > 0 else []
        await self.bot.log(
            cog=self,
            user=None,
            user_action=None,
            channel=None,
            event='LeavingMemberRoleLoggingCog is ready.',
            outcome=None)

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent) -> None:
        """
        On member remove, log the member's roles and the time of removal.
        Exclude @everyone role (the first role in the list), as it is not a role that can be given back.
        """
        user_id = payload.user.id
        role_ids = [role.id for role in payload.user.roles][1:]  # exclude @everyone
        self.users_ids_roles_ids[user_id] = role_ids
        with open(self.left_users_roles_csv_full_path, 'a') as file:
            file.write(f'{user_id},"{",".join([str(role_id) for role_id in role_ids])}"\n')
        await self.bot.log(
            cog=self,
            user=payload.user,
            user_action="Left the server",
            channel=None,
            event=f'Has the following roles: {[role.mention for role in payload.user.roles[1:]]}',
            outcome=None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        On member join, check if the member has left before, if so, give them their roles back.
        """
        if member.id in self.users_ids_roles_ids:
            guild = member.guild
            for role_id in self.users_ids_roles_ids[member.id]:
                # Don't give back certain roles
                if role_id in DO_NOT_RE_GIVE_ROLES_IDS or role_id in ADMINISTRATION_ROLES_IDS:
                    continue
                try:
                    role = guild.get_role(role_id)
                    await member.add_roles(role)
                except Exception as e:
                    await self.bot.log(
                        cog=self,
                        user=member,
                        user_action="Rejoined the server",
                        channel=None,
                        event=f'Failed to give role: {role_id}',
                        outcome=None
                    )

            await self.bot.log(
                cog=self,
                user=member,
                user_action="Rejoined the server",
                channel=None,
                event=f'Given roles: {[guild.get_role(role_id).mention for role_id in self.users_ids_roles_ids[member.id]]}',
                outcome=None
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        LeavingMemberRoleLoggingAndRegivingCog(bot),
        guilds=[discord.Object(id=SERVER_ID)])