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
2. Message Archiving and Logging:
    - The bot should maintain several different .txt / .csv files and directories for each channel each day.
    - Every message sent to the server will be documented in the corresponding .txt / .csv file for the channel for that day, not including files (recording the file link is a valid option).
    - The documentation should at minimum include the sender's username, id, datetime, message's text content, message's id, channel id, if it is replying to other messages, link to all attached files.
    - Every time it runs, it should also backtrack all the unrecorded message since the last time.
    - If messages are removed / deleted, also log the message as a separate "delete" entry. Similar things should be done to editing messages. Record the original message id, channel id, datetime, sender name, sender id so it is possible to backtrack.
    - This function should also track the number of words and the number of characters being sent in each channel by each person every day. This should be done in parallel to message archiving.
3. Resource Fetching:
    - When a user uses a specific command, the bot will send (privately by default, can be overwritten) a link to the resources of a specific course in the same channel.
    - This requires a function that allows users to add resources to the database of the bot. The bot records the name of resource provider, resource's name, resource's link, resource's course channel id. Then modify a specific "main" embed message in the corresponding channel. (The main embed is also pinned)
    - When the user requests the resource, the bot will privately send a `ephemeral=True` copy of the embed to the user, or send a link to the "main embed"
    - By default, if the user did not specify channel, the channel they sent the message is linked to the course (unless the channel is not one of the course channels)
4. Resource Channel Organization:
    - Using embed messages, organize the links in the resources channel into hyperlinks.
    - One embed message will correspond to one "resource category"
    - When new resources are to be added or removed, the admins should be able to add or remove the resource via a slash command.
5. Assignment Reminders:
    - In a specified channel, the bot will ping everyone with "assignment reminders" role at specified times before the assignment is due (such as 2 weeks, 1 week, 48 hours, 24 hours, 6 hours)
    - The admins should be able to add or remove new assignments to this via slash command.
    - The reminder should not trigger if the assignment is already past a reminder threshold time at the moment it is added.
6. Automatically add a restriction role to any user that is obviously a scammer or advertiser:
    - The main criterion for this is if the user sends a long message within 5 minutes of joining the server, including links or emojis.
    - The bot should also record any person who has been applied the restriction role to prevent them from leaving and joining the server to clear their roles.
    - The bot should make a copy of the suspected scammer's message and post them in the reasons-of-ban-history channel.
7. Anonymous Polling:
    - Allow admins to create polls with a set end date with options, voting mode (single vote or multiple vote), ping people or not, and what roles they must have to participate in the poll. Also list of reminders times (by default it's only 24 hours before poll closes).
    - The bot should also make an announcement about any upcoming poll and remind people 24 hours before it closes, (also pings the roles depends on the settings).
    - Either in a "polling channel", or as a slash command, the users can respond to the poll.
    - The bot records the votes, and who voted, but does not link the two piece of information together. (List of voters are separate from list of voted) Only one time vote allowed for each user (no changing votes later).
    - The bot announces the result of the poll. (ping or not depends on the settings of the specific poll)
8. Monitor and Display Server Statistics:
    - Number of people with every single role, display as not-joinable VC
    - Return on request (slash command) server's message history situation, with graphs including the top "n" message sender / channels depending on the user's input (default is 10)
9. Make it easier to add emojis to the server:
    - Make it such that everyone can simply use a slash command to send any other server's emoji or any png/gif and add it to the server.
    - Also make it easier to remove emotes.
    - Add a rate-limit to how many emotes everyone can add.
10. Log all the bot's activities to a specific log channel:
    - probably in embed format as well, this includes ALL updates, even when on_ready or reaction roles.
    - Includes: datetime, action-detail, initiated by, result, error

## "Fun" Functions:
1. The bot can play gomoku?
2. The bot can facilitate a "counting" game:
    - All users sends numbers in a specific channel. The same person cannot send two consecutive numbers, and the numbers must be strictly increasing by one for every message. The bot reacts to every correct counting attempt, and announces that it resets the count every time someone messes up.
3. Somehow make a music bot feature:
    - Siilar to the Groovy bot, search on youtube, parse the video audio, and play the audio in ONE channel
    - Commands includes: join, leave, queue, dequeue, view queue, skip. The bot only go to the first "join" voice channel if the user is in a voice channel. It disconnects when it's not playing music for 5 minutes.
