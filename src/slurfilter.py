from datetime import timedelta
from discord.ext import commands
import discord

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command("help")


async def slur_filter(ctx, data: tuple, type="message", before=None, list_item=0):
    # Setting all needed data variables
    word_data, blacklist_data, report_channel, alert_ping = data[0], data[1], data[2], data[3]

    if (type == "nick"):  # Nickname varibale handling
        if (ctx.nick is None):
            return
        else:
            filtered_text = ctx.nick
    else:
        filtered_text, original_text = "", ctx.content
        msg_format = f"{ctx.author.mention}-{ctx.channel.mention}: \"{original_text[0:100]}\" {alert_ping}"

    # Message filtering part:
    try:
        if (filtered_text != "debugtool"):
            # Deletes duplicate letters.
            unquie_symbol = None
            for letter in ctx.content.lower():
                if (unquie_symbol != letter):
                    unquie_symbol = letter
                    filtered_text += letter

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

        # Deleting special characters from filtered_text
        for letter in filtered_text:
            if letter not in word_data["_allowed_letters"]:
                # Blacklist check.
                if (str(ctx.author.id) in blacklist_data):
                    await ctx.delete()
                    await ctx.channel.send(f"{ctx.author.mention} You cannot use special characters.", delete_after=2)
                    return

                # Deleting found special characters.
                filtered_text = filtered_text.replace(letter, "")

        # Deletes duplicate letters (again)
        unquie_symbol = None
        fully_filtered_text = ""
        for letter in filtered_text:
            if (unquie_symbol != letter):
                unquie_symbol = letter
                fully_filtered_text += letter

        filtered_text = fully_filtered_text

    except AttributeError:
        pass  # Solution to trying to .lower() nick when it's None
    
    print(f"{filtered_text} | {original_text}")

    # Taking action if word found.
    for word in word_data["_banned_words"]:
        if word in filtered_text:
            if (type == "nick"):
                # Reverts the username back to what it was before.
                await ctx.edit(nick=before.nick)

                await report_channel.send(f"{ctx.id} Tried to change his nickname to \"{filtered_text}\"")
                return

            await ctx.delete()  # Delete flagged word

            if (report_channel is not False):  # Report channel selected.
                await report_channel.send(msg_format + " [Timed out for 12 hours].")

            elif (report_channel is False):  # Error for "No selected channel"
                await ctx.channel.send(f"{msg_format} **[Please select a channel using /setchannel]**")
                break

            try:
                duration = timedelta(hours=12)
                await ctx.author.timeout(duration, reason="Said the n-word.")

            except discord.errors.Forbidden:  # Role order permission problem.
                await report_channel.send("**Failed to timeout a user, please put the bot at the top of the role list**")

            return
        
    # After this point we know they're fine.

    # Using recursion to do a second filter.
    if (list_item == 0):
        await slur_filter(ctx=ctx, data=(word_data, blacklist_data, report_channel, alert_ping), list_item=1)
