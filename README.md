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
    - The bot should maintain several different .txt files and directories for each channel each day.
    - Every message sent to the server will be documented in the corresponding .txt file for the channel for that day, not including files (recording the file link is a valid option).
    - The documentation should at minimum include the sender's username, id, datetime, message's text content, message's id, channel id, if it is replying to other messages, link to all attached files.
    - Every time it runs, it should also backtrack all the unrecorded message since the last time.
    - If messages are removed / deleted, also log the message as a separate "delete" entry.
