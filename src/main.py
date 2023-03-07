from discord import app_commands
from discord.ext import commands
import slurfilter  # Custom import.
import discord
import json
import os


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command("help")

blacklist_data = []
server_data = {}

server_db = int(os.environ["server_db"])
blacklist_db = int(os.environ["blacklist_db"])


with open("./Json/words.json", "r", encoding="utf-8") as f:
    word_data = json.load(f)


# Used to get the channel that the bot posts reports to.
async def getreportchannel(ctx: discord.message.Message):
    if (str(ctx.guild.id) in server_data):

        # returns: reports channel + mod ping
        return bot.get_channel(int(server_data[f"{ctx.guild.id}"]["channel"])), \
                server_data[f"{ctx.guild.id}"]["alert_ping"]

    else:  # If no channel is found (aka they haven't set one)
        return False, "@set-role"


@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Succesfully synced.")

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
    Removes an item from the database.

    Parameters
    ----------
    type: str: Either  "server" or "blacklist"\n
    data: dict or list: The client side copy of the db.\n
    remove_item: any: The item to remove from the database.\n


    P.S: When type=server the guildid is passed through-
    even if it's to change the alert_ping because no matter what-
    it just deletes the message outright then replaces it with an new one.
    """
    if (type == "blacklist"):
        data.remove(remove_item)

    channel_to_grab = bot.get_channel(server_db if (type == "server") else blacklist_db)
    data_grabbed = channel_to_grab.history(limit=50)

    async for item in data_grabbed:
        # Gets guildid for server type | blacklist id for blacklist type.
        current_item = item.content.split(" | ", 1)[0]

        if (str(current_item) == str(remove_item)):
            await item.delete()

            # Successfully found and deleted item from database
            return True


@bot.tree.command(name="blacklist", description="Userid as an argument and they'll be able able to send every character found on a qwerty keyboard")
@app_commands.describe(userid="the user's id")
async def blacklist(interaction: discord.Interaction, userid: str):
    blacklistchannel = bot.get_channel(blacklist_db)

    if (interaction.permissions.administrator is True):
        userid = userid.replace("<", "").replace(">", "").replace("@", "")

        try:
            if (userid not in blacklist_data):
                blacklist_data.append(userid)

                await blacklistchannel.send(f"{userid} | \"{await bot.fetch_user(userid)}\"")
                await interaction.response.send_message(f"Successfully added \"{await bot.fetch_user(userid)}\" to blacklist.")

            else:  # If user is in blacklist.
                await db_remove(type="blacklist", data=blacklist_data, remove_item=userid)
                await interaction.response.send_message(f"Successfully removed \"{await bot.fetch_user(userid)}\" from the blacklist.")

        # Exception when userid is unknown
        except discord.errors.NotFound:
            await interaction.response.send_message("Failed to grab user from supplied id. Please check the id.", delete_after=3)


@bot.tree.command(name="setchannel", description="Set the channel to send reports into and set admin ping for reports")
@app_commands.describe(alert_ping="Role/User to alert when someone has been detected saying a slur.")
async def setchannel(interaction, alert_ping: str):
    serverchannel = bot.get_channel(server_db)

    # FORMAT: Guildid | channelid | alert_ping
    db_format = f"{interaction.guild_id} | {interaction.channel_id} | {alert_ping}"

    if (interaction.permissions.administrator is True):

        # Adding new server to db.
        if str(interaction.guild_id) not in server_data:
            server_data[f"{interaction.guild_id}"] = {"channel": str(interaction.channel_id), "alert_ping": str(alert_ping)}

            await serverchannel.send(db_format)
            await interaction.response.send_message("Successfully added channel. Reports will be Reported here")

        # Same channel and alert ping.
        elif str(interaction.channel_id) in server_data[f"{interaction.guild_id}"]["channel"] \
                and alert_ping in server_data[f"{interaction.guild_id}"]["alert_ping"]:

            await interaction.response.send_message("This channel and ping are already selected.")
            return

        # Alert ping change.
        elif str(interaction.channel_id) in server_data[f"{interaction.guild_id}"]["channel"] \
                and alert_ping != server_data[f"{interaction.guild_id}"]["alert_ping"]:

            server_data[f"{interaction.guild_id}"] = {"channel": str(interaction.channel_id), "alert_ping": str(alert_ping)}

            await db_remove(type="server", data=server_data, remove_item=interaction.guild_id)
            await serverchannel.send(db_format)

            await interaction.response.send_message("Succesfully Updated the ping role.")

        # Channel change.
        elif str(interaction.guild_id) in server_data \
                and alert_ping is not server_data[f"{interaction.guild_id}"]["alert_ping"]:
            server_data[f"{interaction.guild_id}"] = {"channel": str(interaction.channel_id), "alert_ping": str(alert_ping)}

            await db_remove(type="server", data=server_data, remove_item=interaction.guild_id)
            await serverchannel.send(db_format)

            await interaction.response.send_message("[WARNING: A different channel is this server is already selected and is now this channel]")

    else:
        await interaction.response.send_message("You don't have permissions to change the channel.", ephemeral=True)


@bot.tree.command(name="help", description="Help command for server setup")
async def help(interaction):
    embed=discord.Embed(title="Watcher Help", description=" How to setup your server.", color=0x6b6b6b)
    embed.add_field(name="1. /setchannel (mod ping)", value="to send reports to the channel you send this command in. And that's basically it. ", inline=False)
    embed.add_field(name="2. (Optional) /blacklist (userid)", value="If people say the nword using special characters run this command to restirict them to everything avaiable on the qwerty keyboard. (no emojis either)", inline=False)
    embed.set_footer(text="Someone found a bypass or a bug? Please message WalletConsumer#9046 to report this.")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_member_update(before, after):
    report_channel, alert_ping = await getreportchannel(after)

    await slurfilter.slur_filter(
                ctx=after, data=(word_data, blacklist_data, report_channel, alert_ping),
                type="nick", before=before)


@bot.event
async def on_message_edit(before, after):
    report_channel, alert_ping = await getreportchannel(after)
    await slurfilter.slur_filter(ctx=after, data=(word_data, blacklist_data, report_channel, alert_ping))


@bot.event
async def on_message(ctx):
    if ctx.author.bot:
        return

    report_channel, alert_ping = await getreportchannel(ctx)
    await slurfilter.slur_filter(ctx=ctx, data=(word_data, blacklist_data, report_channel, alert_ping))

bot.run(os.environ["DISCORD_TOKEN"])
