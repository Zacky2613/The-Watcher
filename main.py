from discord.ext import commands
import discord.utils
import datetime
import discord
import asyncio
import json
import os


intent = discord.Intents(messages=True, guilds=True, members=True)
bot = commands.Bot(command_prefix='!', intents=intent)
bot.remove_command("help")

server_data = {"servers": {}}

with open("./Json/words.json", "r") as f:
    data = json.load(f)

# Used to get the channel that the bot posts reports to.
async def getreportchannel(ctx: discord.message.Message):
    if (str(ctx.guild.id) in server_data["servers"]):
        return bot.get_channel(int(server_data["servers"]
                                [f"{ctx.guild.id}"]["channel"]))

    else:  # If no channel is found (aka they haven't set one)
        return False


async def slur_filter(ctx: discord.message.Message):
    report_channel = await getreportchannel(ctx)
    username = ctx.author

    filtered_text = ctx.content
    original_text = ctx.content

    if (filtered_text != "debugtool"):
        for filter_item in data["_replace_letters"]:
            filtered_text = filtered_text.lower().replace(
                filter_item[0],
                filter_item[1]
            )

    filtered_text = filtered_text.replace("🇳", "n").replace("🇮", "i") \
        .replace("🇬", "g").replace("🇦", "a") \
        .replace("🇪", "e").replace("🇷", "r")

    for word in data["_banned_words"]:
        if word in filtered_text:
            await ctx.delete()

            if (report_channel is not False):
                await report_channel.send(f"{username.mention}-{ctx.channel.mention}: \"{original_text}\"")

            elif (report_channel is False):  # Error for "No channel has been selected on the server"
                await ctx.channel.send(f"{username.mention}-{ctx.channel.mention}: \"{original_text}\" **[Please select a channel to funnel reports into]**")

        elif (str(ctx.author.id) in data["blacklist"]):  # User blacklist check.
            for letter in filtered_text:
                if letter not in data["_allowed_letters"]:
                    await ctx.delete()

                    botmsg = await ctx.channel.send(f"{username.mention} You cannot use special characters.")
                    await asyncio.sleep(2)
                    await botmsg.delete()

                    return
    
    # After this point we know they're fine.
    await bot.process_commands(ctx)


@bot.event
async def on_ready():
    activity = discord.Game(name="Watching.")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    channel = bot.get_channel(1021707102688911370)
    await channel.send("[The Watcher is online]")

    # Grabbing server & blacklist data:
    serverchannel = bot.get_channel(1031818960502525952)
    blacklistchannel = bot.get_channel(1031819046477369365)

    servers_grabbed = await serverchannel.history(limit=200).flatten()
    blacklist_grabbed = await blacklistchannel.history(limit=200).flatten()

    for i in servers_grabbed:
        guildid, channelid = i.content.split(" | ")
        server_data["servers"][f"{guildid}"] = {}
        server_data["servers"][f"{guildid}"]["channel"] = str(channelid)

    for i in blacklist_grabbed:
        data["blacklist"].append(i.content)


@bot.command()
async def blacklist(ctx, *, userid):
    blacklistchannel = bot.get_channel(1031819046477369365)

    if ctx.author.guild_permissions.administrator is True:
        userid = userid.replace("<", "").replace(">", "").replace("@", "")

        if (userid not in data["blacklist"]):
            data["blacklist"].append(userid)

            await blacklistchannel.send(userid)
            await ctx.channel.send(f"Successfully added '{await bot.fetch_user(userid)}' to blacklist.")
        else:
            await ctx.channel.send(f"User '{await bot.fetch_user(userid)}' is already on blacklist.")
            return


@bot.command()
async def setchannel(ctx):
    serverchannel = bot.get_channel(1031818960502525952)

    if ctx.author.guild_permissions.administrator is True:
        # Adding new server to server_data.
        if str(ctx.message.guild.id) not in server_data["servers"]:
            server_data["servers"][f"{ctx.message.guild.id}"] = {"channel": str(ctx.channel.id)}
            server_data["servers"][f"{ctx.message.guild.id}"] = {"channel": str(ctx.channel.id)}

            await serverchannel.send(f"{ctx.message.guild.id} | {ctx.channel.id}")
            await ctx.channel.send("Successfully added channel. Reports will be Reported here")

        # If same channel is selected already.
        elif str(ctx.channel.id) in server_data["servers"][f"{ctx.message.guild.id}"]["channel"]:
            await ctx.channel.send("This channel is already selected.")

            return

        # If different channel is already selected in the server.
        elif str(ctx.message.guild.id) in server_data["servers"]:
            server_data["servers"][f"{ctx.message.guild.id}"] = {"channel": str(ctx.channel.id)}

            await serverchannel.send(f"{ctx.message.guild.id} | {ctx.channel.id}")
            await ctx.channel.send("[WARNING: A different channel is this server is already selected and is now this channel]")

    else:
        botmsg = await ctx.channel.send("You don't have permissions to change the channel.")
        await asyncio.sleep(2)
        await botmsg.delete()


@bot.command()
async def ping(ctx):
    await ctx.send(f"I see your everymove with {round(bot.latency * 1000)}ms latency.")


@bot.command()
async def help(ctx):
    embed = discord.Embed(title=" ", description="Help Menu for the Watcher Discord Bot", color=0xff0000)
    embed.set_author(name="Help Menu\n")
    embed.add_field(name="!setchannel", value="(Admin) Set channel to send reports to.", inline=False)
    embed.add_field(name="!blacklist @user#0000", value="(Admin) User mentioned can only send assci letters.", inline=False)
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
            .replace("🇪", "e").replace("🇷", "r")

        for word in data["_banned_words"]:
            if word in filtered_text:
                # Reverts the username back to what it was before.
                await after.edit(nick=before.nick)

                await report_channel.send(f"{after.mention} Tried to change his nickname to \"{filtered_text}\"")


@bot.event
async def on_message_edit(before, after):
    await slur_filter(ctx=after)


@bot.event
async def on_message(ctx):
    if ctx.author.bot:
        return

    await slur_filter(ctx=ctx)


bot.run(os.environ["DISCORD_TOKEN"])
