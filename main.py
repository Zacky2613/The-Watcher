from datetime import timedelta
from discord.ext import commands
import discord.ext.commands
import discord
import asyncio
import json
import os


intent = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intent)
bot.remove_command("help")

server_data = {"servers": {}}
server_db = os.environ["server_db"]
blacklist_db = os.environ["blacklist_db"]


with open("./Json/words.json", "r") as f:
    data = json.load(f)


# Used to get the channel that the bot posts reports to.
async def getreportchannel(ctx: discord.message.Message):
    if (str(ctx.guild.id) in server_data["servers"]):
        
        return bot.get_channel(int(server_data["servers"][f"{ctx.guild.id}"]["channel"])), \
                server_data["servers"][f"{ctx.guild.id}"]["alert_ping"]


    else:  # If no channel is found (aka they haven't set one)
        return False, False

async def slur_filter(ctx, command: bool):
    report_channel, alert_ping = await getreportchannel(ctx)
    username = ctx.author

    filtered_text, original_text = ctx.content, ctx.content

    if (filtered_text != "debugtool"):
        for filter_item in data["_replace_letters"]:
            filtered_text = filtered_text.lower().replace(
                filter_item[0],
                filter_item[1]
            )

    # Because of a reason I don't understand I have to manually-
    # Place the emoji filter here.
    filtered_text = filtered_text.replace("🇳", "n").replace("🇮", "i") \
        .replace("🇬", "g").replace("🇦", "a") \
        .replace("🇪", "e").replace("🇷", "r") \
        .replace("❗", "i")

    message_format = f"{username.mention}-{ctx.channel.mention}: \"{original_text}\" {alert_ping}"

    for word in data["_banned_words"]:
        if word in filtered_text:
            await ctx.delete()

            if (report_channel is not False):
                await report_channel.send(message_format)

            elif (report_channel is False):  # Error for "No selected channel"
                await ctx.channel.send(f"{message_format} **[Please select a channel, do `!help` for more information.]**")
                break

            try:
                duration = timedelta(minutes=30)
                await username.timeout(duration, reason="Said the n-word.")

            except discord.errors.Forbidden:  # Missing Permissions (role order)
                await report_channel.send("**I have failed to timeout someone for saying the n-word because of permission issues, please promote the-watcher role to the top of the role list.**")

            return True

        # Blacklist user check.
        elif (str(ctx.author.id) in data["blacklist"]):
            for letter in filtered_text:
                if letter not in data["_allowed_letters"]:
                    await ctx.delete()

                    if (report_channel is not False):
                        await report_channel.send(f"{message_format} [SPECIAL CHARACTER]")

                    await ctx.channel.send(f"{username.mention} You cannot use special characters.", delete_after=2)


                    return True

    # After this point we know they're fine.
    if (command is True):
        await bot.process_commands(ctx)
    else:
        return False


@bot.event
async def on_ready():
    activity = discord.Game(name="Watching.")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # Grabbing server & blacklist data:
    serverchannel = bot.get_channel(server_db)
    blacklistchannel = bot.get_channel(blacklist_db)

    servers_grabbed = serverchannel.history(limit=200)
    blacklist_grabbed = blacklistchannel.history(limit=200)

    async for i in servers_grabbed:
        guildid, channelid, alert_ping = i.content.split(" | ")
        server_data["servers"][f"{guildid}"] = {}
        server_data["servers"][f"{guildid}"]["channel"] = str(channelid)
        server_data["servers"][f"{guildid}"]["alert_ping"] = str(alert_ping)

    print(server_data)

    async for i in blacklist_grabbed:
        userid = i.content.split(" | ", 1)[0]
        data["blacklist"].append(userid)


@bot.command()
async def blacklist(ctx, *, userid):
    blacklistchannel = bot.get_channel(blacklist_db)

    if ctx.author.guild_permissions.administrator is True:
        userid = userid.replace("<", "").replace(">", "").replace("@", "")

        try:
            if (userid not in data["blacklist"]):
                data["blacklist"].append(userid)

                await blacklistchannel.send(f"{userid} | \"{await bot.fetch_user(userid)}\"")
                await ctx.channel.send(f"Successfully added \"{await bot.fetch_user(userid)}\" to blacklist.")

            else:  # If user is in blacklist.
                data["blacklist"].remove(userid)
                blacklist_grabbed = blacklistchannel.history(limit=50)

                async for i in blacklist_grabbed:
                    remove_userid = i.content.split(" | ", 1)[0]

                    if (remove_userid == userid):
                        await i.delete()
                        await ctx.channel.send(f"Successfully removed \"{await bot.fetch_user(userid)}\" from blacklist.")

                return

        # Exception when userid is unknown
        except discord.errors.NotFound:
            await ctx.channel.send("Failed to grab user from supplied user. Please check the userid.", delete_after=3)



@bot.command()
async def clearchat(ctx):
    await ctx.message.delete()

    channel_to_clear = bot.get_channel(ctx.channel.id)
    channel_messages = channel_to_clear.history(limit=200)

    message_count = 0
    async for msg in channel_messages:
        if msg.author.bot:
            return

        result = await slur_filter(ctx=msg, command=False)
        if (result is True):  # If slur is found
            message_count += 1


    await ctx.channel.send(f"Deleted {message_count} messages flagged with the n-word", delete_after=2)



@bot.command()
async def setchannel(ctx, *, alert_ping):
    serverchannel = bot.get_channel(server_db)

    if ctx.author.guild_permissions.administrator is True:
        # Adding new server to server_data.
        if str(ctx.message.guild.id) not in server_data["servers"]:
            server_data["servers"][f"{ctx.message.guild.id}"] = {"channel": str(ctx.channel.id), "alert_ping": str(alert_ping)}

            await serverchannel.send(f"{ctx.message.guild.id} | {ctx.channel.id} | {alert_ping}")
            await ctx.channel.send(f"Successfully added channel. Reports will be Reported here {alert_ping}")


        # If same channel and mod ping is the same
        elif str(ctx.channel.id) in server_data["servers"][f"{ctx.message.guild.id}"]["channel"] \
            and alert_ping in server_data["servers"][f"{ctx.message.guild.id}"]["alert_ping"]:

            await ctx.channel.send("This channel and ping are already selected.")


        # If same channel but different alert ping.
        elif str(ctx.channel.id) in server_data["servers"][f"{ctx.message.guild.id}"]["channel"] \
            and alert_ping is not server_data["servers"][f"{ctx.message.guild.id}"]["alert_ping"]:

            server_data["servers"][f"{ctx.message.guild.id}"] = {"channel": str(ctx.channel.id), "alert_ping": str(alert_ping)}
            await ctx.channel.send(f"")


        # If different channel is already selected in the server.
        elif str(ctx.message.guild.id) in server_data["servers"]:
            server_data["servers"][f"{ctx.message.guild.id}"] = {"channel": str(ctx.channel.id), "alert_ping": str(alert_ping)}

            await serverchannel.send(f"{ctx.message.guild.id} | {ctx.channel.id} | {alert_ping}")
            await ctx.channel.send("[WARNING: A different channel is this server is already selected and is now this channel]")

    else:
        await ctx.channel.send("You don't have permissions to change the channel.", delete_after=2)

    print(server_data)


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
    # Because of the structure of slur_filter() I've had to remake it here-
    # for it's different situation of not being messages but instead nicknames

    report_channel = await getreportchannel(after)

    filtered_text = after.nick
    if filtered_text is not None:
        if (filtered_text != "debugtool"):
            for filter_item in data["_replace_letters"]:
                filtered_text = filtered_text.lower().replace(
                    filter_item[0],
                    filter_item[1]
                )

        filtered_text = filtered_text.replace("🇳", "n").replace("🇮", "i") \
            .replace("🇬", "g").replace("🇦", "a") \
            .replace("🇪", "e").replace("🇷", "r") \
            .replace("❗", "i")

        for word in data["_banned_words"]:
            if word in filtered_text:
                # Reverts the username back to what it was before.
                await after.edit(nick=before.nick)

                await report_channel.send(f"{after.mention} Tried to change his nickname to \"{filtered_text}\"")


@bot.event
async def on_message_edit(before, after):
    await slur_filter(ctx=after, command=True)


@bot.event
async def on_message(ctx):
    if ctx.author.bot:
        return

    await slur_filter(ctx=ctx, command=True)


# bot.run(os.environ["DISCORD_TOKEN"])
bot.run("MTAwMjgzMTgzNzY1NzMxNzQyNw.GGH2cC.oH9HXSsXuJlROrWuuQi5Dr0BXk1zopOuiyw19g")
