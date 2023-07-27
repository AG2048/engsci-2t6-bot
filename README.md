# engsci-2t6-bot
The soon-to-be discord bot to be used in the UofT EngSci 2T6 discord server

# Contributing
The only file the server will be running is the `main.py` file, which defines the main bot.

For easier collaboration effort, we would be using [Cogs](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html) for `discord.py` to modularize the programming process. Whenever you wish to make changes to specific functions or add new functions, make the edits in the corresponding python file for the specific Cog. At times, it may be appropriate to add new Cog files to implement completely new features.

# Functionalities
Currently we plan to include the following features into our discord bot, more functionalities can be added if we feel like it (or if YOU feel like it!):

## Utility Functions:
1. Reaction Roles:
    - The bot will give / remove a discord role to the member that reacted / unreacted to a specific reaction under a specific message.
    - The reaction emoji should be accessible by the bot (default system emoji or server emoji).
    - There can be multiple reaction role modes, such as: only adding roles, only removing roles, toggle (when user reacts, give role if user doesn't have the role, remove role if user does have the role, then remove the user's reaction).
    - One reaction should accomodate multiple reaction role settings.
    - The reaction role should be easy to set up without needing to change the code (we can use slash commands)
2. Message Archiving:
    - The bot should maintain several different .txt / .csv files and directories for each channel each day.
    - Every message sent to the server will be documented in the corresponding .txt / .csv file for the channel for that day, not including files (recording the file link is a valid option).
    - The documentation should at minimum include the sender's username, id, datetime, message's text content, message's id, channel id, if it is replying to other messages, link to all attached files.
    - Every time it runs, it should also backtrack all the unrecorded message since the last time.
    - If messages are removed / deleted, also log the message as a separate "delete" entry. Similar things should be done to editing messages. Record the original message id, channel id, datetime, sender name, sender id so it is possible to backtrack.
3. Resource Fetching:
    - When a user uses a specific command, the bot will send (privately by default, can be overwritten) a link to the resources of a specific course in the same channel.
    - This requires a function that allows users to add resources to the database of the bot. The bot records the name of resource provider, resource's name, resource's link, resource's course channel id. Then modify a specific "main" embed message in the corresponding channel.
    - When the user requests the resource, the bot will privately send a `ephemeral=True` copy of the embed to the user, or send a link to the "main embed"
4. Resource Channel Organization:
    - Using embed messages, organize the links in the resources channel into hyperlinks.
    - One embed message will correspond to one "resource category"
    - When new resources are to be added or removed, the admins should be able to add or remove the resource via a slash command.
5. Assignment Reminders:
    - In a specified channel, the bot will ping everyone with "assignment reminders" role at specified times before the assignment is due (such as 2 weeks, 1 week, 48 hours, 24 hours, 6 hours)
    - The admins should be able to add or remove new assignments to this via slash command.
    - The reminder should not trigger if the assignment is already past a reminder threshold time at the moment it is added.
6. Automatically add a restriction role to any user that is obviously a scammer or advertiser.
    - The main criterion for this is if the user sends a long message within 5 minutes of joining the server, including links or emojis.
    - The bot should also record any person who has been applied the restriction role to prevent them from leaving and joining the server to clear their roles.
    - The bot should make a copy of the suspected scammer's message and post them in the reasons-of-ban-history channel.
