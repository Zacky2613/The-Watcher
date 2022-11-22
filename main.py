from datetime import timedelta
from discord.ext import commands
import discord.ext.commands
import discord
import asyncio
import json
import os

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command("help")

blacklist_data = []
server_data = {}

# Emoji "_replace_letters" list.
emoji_list = [
    ["🇳", "n"], ["🇮", "i"], ["🇬", "g"], ["🇦", "a"],
    ["🇦", "a"], ["🇪", "e"], ["🇷", "r"], ["❗", "i"]
]

server_db = int(os.environ["server_db"])
blacklist_db = int(os.environ["blacklist_db"])

with open("./Json/words.json", "r") as f:
    word_data = json.load(f)


# Used to get the channel that the bot posts reports to.
async def getreportchannel(ctx: discord.message.Message):
    if (str(ctx.guild.id) in server_data):
        
        # returns: reports channel + mod ping
        return bot.get_channel(int(server_data[f"{ctx.guild.id}"]["channel"])), \
                server_data[f"{ctx.guild.id}"]["alert_ping"]

    else:  # If no channel is found (aka they haven't set one)
        return False, False


@bot.event
async def on_ready():
    activity = discord.Game(name="Watching.")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # Grabbing server & blacklist data:
    servers_grabbed = bot.get_channel(server_db).history(limit=200)
    blacklist_grabbed = bot.get_channel(blacklist_db).history(limit=200)

    # Getting server & blacklist databases.
    # Then appending them to the client side version of it.
    async for server in servers_grabbed:
        guildid, channelid, alert_ping = server.content.split(" | ")

        server_data[f"{guildid}"] = {}
        server_data[f"{guildid}"]["channel"] = str(channelid)
        server_data[f"{guildid}"]["alert_ping"] = str(alert_ping)

    async for blacklist in blacklist_grabbed:
        userid = blacklist.content.split(" | ", 1)[0]

        blacklist_data.append(userid)


async def db_remove(type: str, data: dict or list, remove_item: any):
    """
    Removes an item from a database.

    Parameters
    ----------
    type: str: Either  "server" or "blacklist"
    data: dict or list: The client side copy of the db.
    remove_item: any: The item to remove from the database.


    P.S: When type=server the guildid is passed through-
    even if it's to change the alert_ping because no matter what-
    it just deletes the message outright then replaces it with an new one.
    """
    if (type == "blacklist"):
        data.remove(remove_item)

    channel_to_grab = bot.get_channel(server_db if(type=="server") else blacklist_db)
    data_grabbed = channel_to_grab.history(limit=50)

    async for item in data_grabbed:
        # Gets guildid for server type | blacklist id for blacklist type.
        current_item = item.content.split(" | ", 1)[0]

        if (str(current_item) == str(remove_item)):
            await item.delete()

            # Successfully found and deleted item from database
            return True


async def slur_filter(ctx, command: bool, type="message", before=None):
    report_channel, alert_ping = await getreportchannel(ctx)

    if (type == "nick"):
        filtered_text = ctx.nick
    else:
        filtered_text, original_text = ctx.content, ctx.content
        message_format = f"{ctx.author.mention}-{ctx.channel.mention}: \"{original_text}\" {alert_ping}"

    if (filtered_text != "debugtool"):
        for filter_item in word_data["_replace_letters"]:
            filtered_text = filtered_text.lower().replace(
                filter_item[0],
                filter_item[1]
            )
        # Because of a converation issue with unicode characters in json files
        # being read to python it wrecks it up, so I have to place it here.
        for emoji_item in emoji_list:
            filtered_text = filtered_text.lower().replace(
                emoji_item[0],
                emoji_item[1]
            )

    for word in word_data["_banned_words"]:
        if word in filtered_text:
            if (type == "nick"):
                # Reverts the username back to what it was before.
                await ctx.edit(nick=before.nick)

                await report_channel.send(f"{ctx.nick} Tried to change his nickname to \"{filtered_text}\"")
                return

            await ctx.delete()

            if (report_channel is not False):
                await report_channel.send(message_format)

            elif (report_channel is False):  # Error for "No selected channel"
                await ctx.channel.send(f"{message_format} **[Please select a channel, do `!help` for more information.]**")
                break

            try:
                duration = timedelta(minutes=30)
                await ctx.author.timeout(duration, reason="Said the n-word.")

            except discord.errors.Forbidden:  # Role order problem.
                await report_channel.send("**Failed to timeout a user, please put the bot at the top of the role list**")

            return True

        # Blacklist user check.
        elif (type != "nick"):
            if (str(ctx.author.id) in blacklist_data):
                for letter in filtered_text:
                    if letter not in word_data["_allowed_letters"]:
                        await ctx.delete()

                        if (report_channel is not False):
                            await report_channel.send(f"{message_format} [SPECIAL CHARACTER]")

                        await ctx.channel.send(f"{ctx.author.mention} You cannot use special characters.", delete_after=2)

                        return True

    # After this point we know they're fine.
    if (command is True):
        await bot.process_commands(ctx)
    else:
        return False


@bot.command()
async def blacklist(ctx, *, userid):
    blacklistchannel = bot.get_channel(blacklist_db)

    if ctx.author.guild_permissions.administrator is True:
        userid = userid.replace("<", "").replace(">", "").replace("@", "")

        try:
            if (userid not in blacklist_data):
                blacklist_data.append(userid)

                await blacklistchannel.send(f"{userid} | \"{await bot.fetch_user(userid)}\"")
                await ctx.channel.send(f"Successfully added \"{await bot.fetch_user(userid)}\" to blacklist.")

            else:  # If user is in blacklist.
                await db_remove(type="blacklist", data=blacklist_data, remove_item=userid)

        # Exception when userid is unknown
        except discord.errors.NotFound:
            await ctx.channel.send("Failed to grab user from supplied id. Please check the id.", delete_after=3)


@bot.command()
async def clearchat(ctx):
    await ctx.message.delete()

    channel_messages = bot.get_channel(ctx.channel.id).history(limit=200)

    message_count = 0
    async for msg in channel_messages:
        if msg.author.bot:
            return

        result = await slur_filter(ctx=msg, command=False)
        if (result is True):  # If slur is found
            message_count += 1

    # At the end report how many messages were deleted.
    await ctx.channel.send(f"Deleted {message_count} messages flagged with the n-word", delete_after=4)


@bot.command()
async def setchannel(ctx, *, alert_ping):
    serverchannel = bot.get_channel(server_db)

    # FORMAT: Guildid | channelid | alert_ping
    db_format = f"{ctx.message.guild.id} | {ctx.channel.id} | {alert_ping}"

    if ctx.author.guild_permissions.administrator is True:

        # Adding new server to db.
        if str(ctx.message.guild.id) not in server_data:
            server_data[f"{ctx.message.guild.id}"] = {"channel": str(ctx.channel.id), "alert_ping": str(alert_ping)}

            await serverchannel.send(db_format)
            await ctx.channel.send("Successfully added channel. Reports will be Reported here")

        # Same channel and alert ping.
        elif str(ctx.channel.id) in server_data[f"{ctx.message.guild.id}"]["channel"] \
            and alert_ping in server_data[f"{ctx.message.guild.id}"]["alert_ping"]:

            await ctx.channel.send("This channel and ping are already selected.")
            return

        # Alert ping change.
        elif str(ctx.channel.id) in server_data[f"{ctx.message.guild.id}"]["channel"] \
            and alert_ping != server_data[f"{ctx.message.guild.id}"]["alert_ping"]:

            server_data[f"{ctx.message.guild.id}"] = {"channel": str(ctx.channel.id), "alert_ping": str(alert_ping)}

            await db_remove(type="server", data=server_data, remove_item=ctx.message.guild.id)
            await serverchannel.send(db_format)

            await ctx.channel.send("Succesfully Updated the ping role.")

        # Channel change.
        elif str(ctx.message.guild.id) in server_data \
            and alert_ping is not server_data[f"{ctx.message.guild.id}"]["alert_ping"]:
            server_data[f"{ctx.message.guild.id}"] = {"channel": str(ctx.channel.id), "alert_ping": str(alert_ping)}

            await db_remove(type="server", data=server_data, remove_item=ctx.message.guild.id)
            await serverchannel.send(db_format)

            await ctx.channel.send("[WARNING: A different channel is this server is already selected and is now this channel]")

    else:
        await ctx.channel.send("You don't have permissions to change the channel.", delete_after=2)


@bot.command()
async def ping(ctx):
    await ctx.send(f"I see your everymove with {round(bot.latency * 1000)}ms latency.")


@bot.command()
async def help(ctx):
    embed = discord.Embed(title=" ", description="Help Menu for the Watcher Discord Bot", color=0xff0000)
    embed.set_author(name="Help Menu\n")
    embed.add_field(name="!setchannel", value="(Admin) Set channel to send reports to.", inline=False)
    embed.add_field(name="!blacklist @user#0001", value="(Admin) User mentioned can only send assci letters.", inline=False)
    embed.add_field(name="!clearchat", value="(Admin) Use this command to clear out any previous nword messages in the channel the command is sent in.", inline=False)
    embed.add_field(name="!ping", value="Shows the bot's ping.", inline=False)
    embed.set_footer(text="Watching Every Conversation.")
    await ctx.send(embed=embed)


@bot.event
async def on_member_update(before, after):
    await slur_filter(ctx=after, command=True, type="nick", before=before)


@bot.event
async def on_message_edit(before, after):
    await slur_filter(ctx=after, command=True)


@bot.event
async def on_message(ctx):
    if ctx.author.bot:
        return

    await slur_filter(ctx=ctx, command=True)


bot.run(os.environ["DISCORD_TOKEN"])
