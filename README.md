# The-Watcher

## [Add the bot to your Discord Server!](https://discord.com/api/oauth2/authorize?client_id=1002831837657317427&permissions=8&scope=bot)

A Discord bot mainly developed by Zacky2613 with help from BreakerOfWind.

This contains a real time message montioring system to look for the nword and then alert staff.

## Features

- Good filter system which is constantly being updated.
- A blacklist which blocks users from sending special characters, made for people trying to bypass the bot with unique characters.
- Real time nick-name monitorer so nicknames cannot be changed to the nword (using same filter as messages).
- A command to clear chat of previous bypasses that are now patched.
- Mod pings/Automation of punishments to offenders.
- (Upcoming) Report bypasses.

## Setup

1. After adding the bot to your server type this command into the channel you would like nword reports to be funnled into `!setchannel @admin_ping`
2. If any offenders try to bypass the bot my using special characters you can run the command `!blacklist @user#0001` or `!blacklist 11111111111 (userid)` and force them to only use the characters on the standard qwerty keyboard.

## How it works

- First, every time a new message is sent it is scanned using the bots filter.
- If it finds the nword it will timeout the user for 30 minutes and send a alert to the mods with what they said
- If that fails, then it checks if the user is on the blacklist