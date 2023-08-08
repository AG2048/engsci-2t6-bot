# engsci-2t6-bot
This repository houses the development of an upcoming Discord bot for the UofT EngSci 2T6 server.

# Table of Contents
- [Contributing](#contributing)
- [Project Structure](#project-structure)
- [Functionalities](#functionalities)
  - [Utility Functions](#utility-functions)
  - ["Fun" Functions](#fun-functions)
- [Cogs](#cogs)

# Completed Functionalities
## Main Bot
### Logging:
`main.py`

We also added a `bot.log()` function that will facilitate logging to the console and to the discord server.
It takes in an organized set of information:
```py
cog: commands.Cog,
user: discord.User = None,
user_action: str = None,
channel: discord.TextChannel = None,
event: str = None,
outcome: str = None
```
And it can go through each of the information and process them according to their data type.

In the end, it sends an embed message to the log channel indicating the cog that the log is from, the user that triggered the log, the user action that triggered the log, the channel that the log is from, the event that triggered the log, and the outcome of the event. At the same time, a similar message is being displayed to the console through `print()`.

## Moderation:
Any functionality that is related to moderation of the server.
### Server Rules:
`cogs/moderation/server_rules.py`

This cog is responsible for the server rules. It allows users to display specific server rules, and allows the admins to set, add, remove, and edit rules.

**All commands are under the `/rules` command group**

The server rules are stored in a csv file in the `data/moderation` directory. The csv file has the following structure:
```csv
value_name,value
channel_id,<ID OF SERVER RULE MESSAGE'S CHANNEL>
message_id,<ID OF SERVER RULE MESSAGE>
message_content,<CONTENT OF SERVER RULE MESSAGE>
embed_title,<TITLE OF SERVER RULE MESSAGE>
embed_description,<DESCRIPTION OF SERVER RULE MESSAGE>
embed_thumbnail_url,<URL OF SERVER RULE MESSAGE'S THUMBNAIL | LEAVE BLANK FOR NO THUMBNAIL>
embed_colour,<HEX STRING OF COLOUR OF SERVER RULE MESSAGE'S EMBED | LEAVE BLANK FOR COLOUR NONE>
embed_field_name,<NAME OF EMBED FIELD>
embed_field_value,<VALUE OF EMBED FIELD>
<THERE CAN BE MULTIPLE EMBED FIELDS PER EMBED>
<THERE CAN BE MULTIPLE EMBEDS>
```
The only values in the file that can be empty are `channel_id`, `message_id`, `embed_thumbnail_url`, and `embed_colour`. 
All other values must be filled in, or being read as `'none'` when reading the csv file. Although the current code stores all empty values / `None` values as `''` (it will be read as `'none'` when reading from the csv file), also all command inputs has the default value of `variable: str = 'none'`.

Specific commands are as follows:
- `set_rules_to_existing_message`
  - Sets the server rules to an existing message that is sent by the bot (so that the bot can edit the message).
  - There are two set actions: 
    - One sets this new message's content as the rule content as well.
    - One overrides this new message's content and edits this message to be the rule content stored in the bot or in the csv file. 
- `create_new_rules_message`
  - Creates a new message with the server rules.
  - There are two create actions:
    - One creates a new message with no embeds and just one line of text.
    - One creates a new message with the rule content stored in the bot or in the csv file.
- `get_link`
  - Gets the link to the server rules message.
- `add_new_ruleset`
  - Adds a new ruleset (a new embed) to the end of server rules message's embeds.
- `add_new_field`
  - Adds a new field to a ruleset (an embed) to the end of the ruleset's (the embed's) fields.
- `insert_new_ruleset_before`
  - Inserts a new ruleset (a new embed) before a specified ruleset (embed).
- `insert_new_field_before`
  - Inserts a new field before a specified field in a specified ruleset (embed).
- `edit_ruleset_thumbnail`
  - Edits the thumbnail of a specified ruleset (embed). Can also remove the thumbnail.
- `edit_ruleset_title`
  - Edits the title of a specified ruleset (embed).
- `edit_ruleset_description`
  - Edits the description of a specified ruleset (embed).
- `edit_ruleset_colour`
  - Edits the colour of a specified ruleset (embed). Can also remove the colour.
- `edit_message_content`
  - Edits the content of the server rules message.
- `edit_field`
  - Edits the name and value of a specified field in a specified ruleset (embed).
- `remove_ruleset`
  - Removes a specified ruleset (embed).
- `remove_field`
  - Removes a specified field in a specified ruleset (embed).
- `display_rule`
  - Displays a specified rule (field in a ruleset/embed) in the server rules message.
  - This message disappears after 5 minutes.
- `remove_ruleset_by_index`
  - Removes a specified ruleset (embed) by its index.
  - This is to be used when the other functions cannot retrieve the ruleset (embed) by its name.
  - Only the remove function has the by-index version, because if we can't retrieve the ruleset (embed) by its name, then there's probably something wrong with the ruleset's name (perhaps it's too long)
- `remove_field_by_index`
  - Removes a specified field in a specified ruleset (embed) by its index.
  - This is to be used when the other functions cannot retrieve the field by its name.
  - Only the remove function has the by-index version, because if we can't retrieve the field by its name, then there's probably something wrong with the field's name (perhaps it's too long)
- `edit_message_content_to_message`
  - Retrieves the content of a specified message and sets the server rules message's content to that message's content.
  - This is to be used when the message content needs to contain multiple lines, which is not possible with the current command inputs.
Only `get_link` and `display_rule` are available to everyone. All other commands are only available to admins.

Few notable things:
- The user specifies the ruleset (embed) and field by `@app_commands.autocomplete` where the autocomplete selections includes the name and the index of the ruleset (embed) and/or field. A check is done to ensure that the user is selecting a valid ruleset (embed) and/or field.
- We write to file after every change to the server rules message. This is to ensure that the server rules message is always up to date. This is also to ensure that if the bot goes down, the server rules message can be restored to its last state.
- The cog always log the server rules before any changes are about to happen to the rules. This displays who made the change to the server rules message and when. The only exception is when the server rules message is creating a new rule message from stored content. This is because the server rules message is not changed in this case.
- The cog always display the last user who edited the server rules message and when. 

### Leaving Member Role Logging and Re-Giving:
`cogs/moderation/leaving_member_role_logging.py`

This cog is responsible for remembering all the roles a user has before they leave the server. When they rejoin the server, the bot will give them back all the roles they had before they left.

The purpose of this cog is to prevent users with "penalty roles" from clearing their penalty roles by leaving and rejoining the server.

All roles are stored in a csv file with the following structure:
```csv
user_id,role_ids
<USER ID>,"<ROLE ID 1>,<ROLE ID 2>,<ROLE ID 3>,..."
```
One thing to keep in mind is to not store the `@everyone` role in the csv file. This is because the bot will attempt to give back the `@everyone` role to the user when they rejoin the server, which is impossible and cause the bot to raise an error.

We also just keep appending to the csv file, and when we read the csv file, just let the later entries of the same user override the earlier ones.

# Contributing
The `main.py` file, which defines the main bot, is the only file that will be running on the server.

To streamline collaboration, we utilize Cogs ([Cogs Documentation](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html)) within `discord.py` to modularize the codebase. If you're looking to make changes to certain functions or add new ones, please do so in the relevant python file for the corresponding Cog. There may be occasions when creating new Cog files is appropriate, especially when introducing entirely new features.

For some examples of how to use Cogs, check the [Cogs](#cogs) section or see existing code.

In each Cog, you can log activities using `await self.bot.log(self, log_message)`

We will primarily be using the app_commands, which is the slash command feature of Discord.

For an example of app_commands, check out cogs/utility/testing.py.

# Project Structure
```
engsci-2t6-bot
├── main.py
├── cogs
│   ├── entertainment
│   ├── logging
│   ├── moderation
│   ├── resources
│   └── utility
│       └── testing.py
├── data
│   ├── entertainment
│   │   ├── counting_state.csv
│   │   └── gomoku_state.csv
│   ├── logging
│   │   ├── bot_log.txt
│   │   ├── message_stats
│   │   │   ├── users_<date>.csv
│   │   │   └── channels_<date>.csv
│   │   └── <channel_id>
│   │       └── messages_<date>.csv
│   ├── moderation
│   │   ├── server_rules.csv
│   │   └── left_users_roles.csv
│   ├── resources
│   │   ├── course_resources
│   │   │   └── <course_channel_id>.csv
│   │   └── general_resources
│   │       └── <general_resource_category_name>.csv
│   └── utility_information
│       ├── assignment_reminders.csv
│       ├── polls
│       │   └── <poll_name>.csv
│       ├── reaction_roles_current_state.csv
│       └── reaction_roles_info.csv
├── .gitignore
├── .env
├── README.md
└── requirements.txt
```
`main.py` is the main file that will be running on the server. It imports all the Cogs and runs the bot.
`cogs` is the directory that houses the Cog category (directory), each containing the Cog files (python files).
`data` is the directory that houses all the data files that the bot will be using. This includes the bot's log, message stats, resource links, etc.
`requirements.txt` is the file that contains all the dependencies that the bot will need to run. This file is used by the `pip` package manager to install all the dependencies.

TODO: explain each file's purpose and structure

# Environment Variables
The `.env` file is a file that contains all the environment variables that the bot will need to run. This includes the bot's token, the server's ID, etc. This file is not included in the repository for security reasons. If you need to run the bot locally, you will need to create this file yourself. The file should be in the same directory as `main.py`.
The content of this file should be as follows:
- APPLICATION_ID=<APPLICATION_ID>
  - The Application ID specific to the bot. This can be found in the Discord Developer Portal. 
- DISCORD_BOT_TOKEN=<TOKEN>
  - The bot's token. This can be found in the Discord Developer Portal.
- SERVER_ID=<SERVER/GUILD ID>
  - The server's ID. This can be found by right-clicking on the server icon and selecting "Copy Server ID".
- ADMINISTRATION_ROLES_IDS=<ADMIN_ROLE_ID_1>,<ADMIN_ROLE_ID_2>,...
  - The IDs of the roles that have administrative privileges. This can be found by right-clicking on the role and selecting "Copy Role ID". 
- COMMAND_PREFIX=<COMMAND_PREFIX>
  - The prefix that the bot will use to identify commands. This can be any string of characters.


# Functionalities
We plan to incorporate the following features into our Discord bot. Additional functionalities may be added as we see fit (or as you suggest!).

## Utility Functions:
1. **Reaction Roles**: 
    - The bot will assign/remove a role based on a member's reaction to a specific message.
    - The reaction emoji should be accessible by the bot (either a default system emoji or a server emoji).
    - The reaction roles could operate in various modes such as: role addition only, role removal only, or toggle mode (giving/removing roles based on the user's current roles).
    - One reaction can correspond to multiple reaction role settings.
    - Reaction roles should be easy to configure without requiring code modifications, for which we can utilize slash commands.

2. **Message Archiving and Logging**: 
    - The bot will manage various .txt/.csv files and directories for each channel daily.
    - Every message sent to the server will be documented in the corresponding .txt/.csv file for that day's channel, excluding files (though file links can be recorded).
    - The documentation should include, at minimum, the sender's username, ID, datetime, message text, message ID, channel ID, any reply details, and links to all attached files.
    - Upon launch, the bot should backtrack all unrecorded messages since its last active session.
    - Any deleted/removed messages should be logged as a separate "delete" entry, similar to message edits. This should include original message details for backtracking purposes.
    - This function should also track and record the word and character count per person per day for each channel, running in parallel with the message archiving process.

3. **Resource Fetching**:
    - When a user triggers a specific command, the bot will send a link to the resources for a specific course in the same channel (by default, sent privately; this can be overridden).
    - The bot will require a function allowing users to add resources to the database. The bot will then record the resource provider's name, resource name, resource link, and the associated course's channel ID, subsequently modifying a main embed message in the corresponding channel (which will also be pinned).
    - If the user does not specify a channel, the bot will associate the resource with the channel from which the request originated, provided it's a course-related channel.

4. **Resource Channel Organization**:
    - The bot will use embed messages to organize resource links in the resource channel.
    - Each embed message will correspond to a resource category.
    - Admins should be able to add or remove resources via a slash command.

5. **Assignment Reminders**:
    - The bot will ping all members with an "assignment reminders" role at predetermined times before an assignment is due (e.g., two weeks, one week, 48 hours, 24 hours, 6 hours).
    - Admins should be able to add or remove assignments using a slash command.
    - The reminder should not trigger if the assignment is already past its reminder threshold when it's added.

6. **Scam Detection and Role Restriction**:
    - The bot should automatically assign a restriction role to any user deemed likely to be a scammer or advertiser, based primarily on the user sending a long message, including links or emojis, within five minutes of joining the server.
    - The bot should keep a record of all users to whom it has applied the restriction role to prevent them from evading the role by leaving and rejoining the server.
    - The bot should also make a copy of any suspected scam messages and post them in a dedicated channel for recording ban reasons.

7. **Anonymous Polling**:
    - The bot should allow admins to create polls with set end dates, voting modes (single or multiple vote), the option to ping participants or not, role requirements for participation, and a list of reminder times (defaulting to 24 hours before the poll closes).
    - The bot should announce any upcoming polls and remind participants 24 hours before the poll closes.
    - Users can vote in a "polling" channel or via a slash command.
    - The bot records votes and voter identities separately, ensuring anonymous voting.
    - The bot announces the results of the poll upon its closure.

8. **Server Statistics Display**:
    - The bot should display the number of people associated with each role and present this data as a voice channel that can't be joined.
    - On request (via a slash command), the bot should return an overview of the server's messaging history, including graphs of the top "n" message senders/channels as specified by the user (default is 10).

9. **Emoji Management**:
    - The bot should allow everyone to add emojis from other servers or any png/gif files to the server using a slash command.
    - The bot should simplify the removal of emojis and impose a rate limit on emoji additions by users.

10. **Activity Logging**:
    - The bot should log all its activities in a dedicated channel, preferably using an embed format. This should include all updates, including on_ready or reaction roles.
    - The log should include: datetime, action details, initiator, result, and any errors.

## "Fun" Functions:
1. **Gomoku**: 
    - How about the bot playing Gomoku?

2. **Counting Game**: 
    - The bot can facilitate a game where users count upwards in a specific channel. The rules include: no one user can post two consecutive numbers, and each message must increment the previous number by one. The bot reacts to every correct count and announces a reset when someone breaks the chain.

3. **Music Bot Feature**: 
    - Similar to the Groovy bot, the bot should search YouTube, parse video audio, and play the audio in a specific channel.
    - Commands include: join, leave, queue, dequeue, view queue, skip. The bot joins the first "join" voice channel if the user is in a voice channel and disconnects if it's not playing music for 5 minutes.

# Cogs
A guide on how to use Cogs will be added here soon.

# Hosting
I am hosting the bot on a Raspberry Pi 4B 4GB. I am using the following method to run the bot:

1. Create a virtual environment in the project directory:
    - `python3 -m venv venv`
    - `source venv/bin/activate`
    - `pip install -r requirements.txt`
2. Create a `.env` file in the project directory and add the environment variables listed [here](#environment-variables).
3. Set up a systemctl service to run the bot in the background:
    - `sudo nano /etc/systemd/system/engsci-2t6-bot.service`
    - Paste the following into the file:
        ```
        [Unit]
        Description=EngSci 2T6 Discord Bot
        Requires=mnt-<DRIVE_THIS_BOT_RUNS_ON>.mount # If the bot is running on a mounted drive
        After=mnt-<DRIVE_THIS_BOT_RUNS_ON>.mount # If the bot is running on a mounted drive
        
        [Service]
        Type=simple
        User=<USERNAME>
        WorkingDirectory=<PATH_TO_DIRECTORY>/engsci-2t6-bot/
        EnvironmentFile=<PATH_TO_DIRECTORY>/engsci-2t6-bot/.env
        Environment="PATH=<PATH_TO_DIRECTORY>/engsci-2t6-bot/venv/bin"
        ExecStart=<PATH_TO_DIRECTORY>/engsci-2t6-bot/venv/bin/python3 <PATH_TO_DIRECTORY>/engsci-2t6-bot/main.py
        Restart=always
        [Install]
        After=mnt-<DRIVE_THIS_BOT_RUNS_ON>.mount # If the bot is running on a mounted drive
        ```
    - `sudo systemctl daemon-reload`
    - `sudo systemctl enable engsci-2t6-bot.service`
    - `sudo systemctl start engsci-2t6-bot.service`
    - `sudo systemctl status engsci-2t6-bot.service` to check the status of the service