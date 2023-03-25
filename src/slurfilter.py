from datetime import timedelta
from discord.ext import commands
import discord

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command("help")


async def unquie_characters(text: str):
    unquie_symbol = None
    filtered_text = ""

    for letter in text.lower():
        if (unquie_symbol != letter):
            unquie_symbol = letter
            filtered_text += letter

    return filtered_text


async def slur_filter(ctx, data: tuple, type="message", before=None, list_item=0):
    # Setting all needed data variables
    word_data, blacklist_data, report_channel, alert_ping = data[0], data[1], data[2], data[3]

    if (type == "nick"):  # Nickname varibale handling
        if (ctx.nick is None):
            return
        else:
            filtered_text = ctx.nick
    else:
        filtered_text, original_text = ctx.content, ctx.content  # filtered_text is set as nothing as it's made later.
        msg_format = f"{ctx.author.mention}-{ctx.channel.mention}: \"{original_text[0:100]}\" {alert_ping}"

    # Text filtering section
    try:
        # Deleting false postive wordsa.
        for trigger_word in word_data["_flagged_words"]:
            filtered_text = filtered_text.lower().replace(
                trigger_word,
                ""
            )

        # Deleting special characters from filtered_text
        for letter in filtered_text:
            if letter not in word_data["_allowed_letters"]:
                # Blacklist check.
                if (str(ctx.author.id) in blacklist_data):
                    await ctx.delete()
                    await ctx.channel.send(f"{ctx.author.mention} You cannot use special characters.", delete_after=2)
                    return
                
                else:
                    # Deleting found special characters.
                    filtered_text = filtered_text.replace(letter, "")

        filtered_text = await unquie_characters(text=filtered_text)

        # Changing letters in the filter.
        for filter_item in word_data["_replace_letters"]:
            try:
                filtered_text = filtered_text.lower().replace(
                    filter_item[0],
                    filter_item[1]
                )

            except TypeError:  # For [[":", "i"], [":", ""]] items.
                filtered_text = filtered_text.lower().replace(
                    filter_item[list_item][0],
                    filter_item[list_item][1]
                )

    except AttributeError:
        pass  # Solution to trying to .lower() nick when it's None


    # Taking action if word found.
    for word in word_data["_banned_words"]:
        if word in filtered_text:
            if (type == "nick"):
                # Reverts the username back to what it was before.
                await ctx.edit(nick=before.nick)

                await report_channel.send(f"{ctx.id} Tried to change his nickname to \"{filtered_text}\"")
                return

            await ctx.delete()  # Delete flagged word
            

            try:
                if (report_channel is not False):  # Server has a set report channel
                    duration = timedelta(hours=12)
                    await ctx.author.timeout(duration, reason="N-word detection.")
                    await report_channel.send(f"{msg_format} [Timed out for 12 hours].")

            except discord.errors.Forbidden:  # Role order permission problem.
                await report_channel.send(f"{msg_format} **[Failed to timeout user due to permission role issue, move the bot role higher up.]**")
                return

            if (report_channel is False):  # Error for "No selected channel"
                await ctx.channel.send(f"{msg_format} **[Please select a channel using /setchannel]**")
                return
                

            return

    # Using recursion to do a second filter.
    if (list_item == 0):
        await slur_filter(ctx=ctx, data=(word_data, blacklist_data, report_channel, alert_ping), list_item=1)
