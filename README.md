# engsci-2t6-bot
This repository houses the development of an upcoming Discord bot for the UofT EngSci 2T6 server.

# Contributing
The `main.py` file, which defines the main bot, is the only file that will be running on the server.

To streamline collaboration, we utilize [Cogs](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html) within `discord.py` to modularize the codebase. If you're looking to make changes to certain functions or add new ones, please do so in the relevant python file for the corresponding Cog. There may be occasions when creating new Cog files is appropriate, especially when introducing entirely new features.

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
