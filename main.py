from discord.flags import Intents
from discord.ext import commands
import discord.utils
import datetime
import discord
import asyncio
import json
import os


bot = commands.Bot(command_prefix='!', Intents=Intents)
bot.remove_command("help")

with open("./Json/words.json", "r") as f:
    data = json.load(f)

with open("./Json/servers.json", "r") as f:
    server_data = json.load(f)


@bot.event
async def on_ready():
    activity = discord.Game(name="Watching.")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    channel = bot.get_channel(1021707102688911370)
    await channel.send("[The Watcher is online]")

async def getreportchannel(ctx: discord.message.Message):
    if (str(ctx.guild.id) in server_data["servers"]):
        return bot.get_channel(server_data["servers"]
                [f"{ctx.message.guild.id}"]["channel"])

    else:
        return False


async def slur_filter(ctx: discord.message.Message):
    time = datetime.datetime.now().strftime("%d/%m/%y %H:%M")
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
                            .replace("🇬", "g").replace("🇦", "a🇦") \
                            .replace("🇪", "e").replace("🇷", "r")

    for word in data["_banned_words"]:
        if word in filtered_text:
            await ctx.delete()

            print(f'{time} {username}: [Original]: "{original_text}" | [Filtered]: "{filtered_text}"')
            # Eg: 20/09/22 24:00 lorem#0000: [Original]: "debugtool" | [Filtered]: "debugtool"

            if (report_channel is not False):
                await report_channel.send(f"{username.mention}-{ctx.channel.mention} '{original_text}'")

            elif (report_channel is False):  # Error for "no channel found on server"
                ...

        elif (str(ctx.id) in data["_blocked_users"]):
            for letter in filtered_text:
                if letter not in data["_allowed_letters"]:
                    await ctx.delete()
                    await ctx.channel.send(f"{username.mention} You've lost the privilege of saying special characters <:trollface:938366103934103622>")

                    return  # If caught using different character.
            break

    # After this point we know they haven't said anything wrong.
    await bot.process_commands(ctx)


@bot.command()
async def blacklistuser(ctx, *, userid):
    if ctx.author.guild_permissions.administrator is True:
        userid = userid.replace("<", "").replace(">", "").replace("@", "")
        data["_blocked_users"].append(userid)

        with open("./Json/words.json", "w") as f:
            json.dump(data, f, indent=4)

        botmsg = await ctx.channel.send(f"Userid '{userid}' Succesfully added to blacklist.")
        await asyncio.sleep(2)
        await botmsg.delete()

    print(f"Added Userid to blacklist [{userid}]")


@bot.command()
async def setchannel(ctx):
    if ctx.author.guild_permissions.administrator is True:
        # Adding new server to server_data.
        if ctx.message.guild.id not in server_data:
            server_data["servers"][f"{ctx.message.guild.id}"] = {}
            server_data["servers"][f"{ctx.message.guild.id}"]["channel"] = str(ctx.channel.id)

            await ctx.channel.send("Successfully added channel. Reports will be Reported here")

        # If current channel is already selected.
        elif ctx.channel.id in server_data["servers"][f"{ctx.message.guild.id}"]["channel"]:
            await ctx.channel.send("This channel currently inuse already.")

            return

        # Changing the channel used in the server.
        elif ctx.message.guild.id in server_data["servers"][f"{ctx.message.guild.id}"]:
            server_data["servers"][f"{ctx.message.guild.id}"] = {}
            server_data["servers"][f"{ctx.message.guild.id}"]["channel"] = str(ctx.channel.id)

            await ctx.channel.send("[WARNING: this server already has a selected channel and has been changed to this]")

        with open("./Json/servers.json", "w") as f:
            json.dump(server_data, f, indent=4)
            f.close()

    else:
        botmsg = await ctx.channel.send("You do not have the permissions to change the channel.")
        await asyncio.sleep(2)
        await botmsg.delete()


@bot.command()
async def printserver(ctx):
    print(server_data)


@bot.command()
async def help(ctx):
    embed = discord.Embed(title=" ", description="Help Menu for the Watcher Discord Bot", color=0xff0000)
    embed.set_author(name="Help Menu\n")
    embed.add_field(name="!setchannel", value="(Admin Only) Set channel that the command sent into to report detected by the bot.", inline=False)
    embed.add_field(name="!blacklistuser", value="(Admin Only) Add a user to a blacklist where they can only say assci letters.", inline=False)
    embed.set_footer(text="Watching Every Conversation.")
    await ctx.send(embed=embed)


@bot.event
async def on_message_edit(before, after):
    await slur_filter(ctx=after)


@bot.event
async def on_message(ctx):
    if ctx.author.bot:
        return

    await slur_filter(ctx=ctx)


bot.run(os.environ["DISCORD_TOKEN"])
