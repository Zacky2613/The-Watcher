from discord.flags import Intents
from discord.ext import commands
import discord.utils
import datetime
import discord
import asyncio
import random
import json
import os


bot = commands.Bot(command_prefix='$', Intents=Intents)
bot.remove_command("help")

messagelist = [
    "🤨📸",
    "stfu",
    "life privileges removed",
    "Bro, you had 1 job",
    "Come on man",
    "Got yo ass"
]

with open("./Json/words.json", "r") as f:
    data = json.load(f)


@bot.event
async def on_ready():
    activity = discord.Game(name="Defending Balloons")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    channel = bot.get_channel(1021707102688911370)
    await channel.send(f"[Bloon-Bot is online]")


async def slur_filter(ctx: discord.message.Message):
    time = datetime.datetime.now().strftime("%d/%m/%y %H:%M")
    username = ctx.author
    bot_ping_channel = bot.get_channel(1021707102688911370)

    if (ctx.content != "debugtool"):
        for filter_item in data["_replace_letters"]:
            ctx.content = ctx.content.lower().replace(
                filter_item[0],
                filter_item[1]
            )
    
    ctx.content = ctx.content.replace("🇳", "n").replace("🇮", "i").replace("🇬", "g").replace("🇦", "a🇦") \
                            .replace("🇪", "e").replace("🇷", "r")

    for word in data["_banned_words"]:
        if word in ctx.content:
            await ctx.delete()

            print(f'{time} {username}: "{ctx.content}" ')
            # e.g: 20/09/22 24:00 user#0000: "debugtool"

            await bot_ping_channel.send(f"{username.mention} {ctx.channel.mention} {messagelist[random.randint(0, len(messagelist)) - 1]}  <@&997059007799898172>")

        elif (str(ctx.id) in data["_blocked_users"]):
            for letter in ctx.content.lower().replace(" ", ""):
                if letter not in data["_allowed_letters"]:
                    await ctx.delete()
                    await ctx.channel.send(f"{username.mention} You've lost the privilege of saying special characters <:trollface:938366103934103622>")

                    break
            break
        else:
            await bot.process_commands(ctx)


@bot.command()
async def add_user(ctx, *, userid):
    if (ctx.id == 452675869366943755):
        userid = userid.replace("<", "").replace(">", "").replace("@", "")
        data["_blocked_users"].append(userid)

        with open("./Json/words.json", "w") as f:
            json.dump(data, f, indent=4)

        botmsg = await ctx.channel.send(f"`userid [{userid}] | Succesfully added to blacklist.`") 
        await asyncio.sleep(2)
        await botmsg.delete()

    print(f"Added Userid to blacklist [{userid}]")


@bot.event
async def on_message_edit(before, after):
    await slur_filter(ctx=after)


@bot.event
async def on_message(ctx):
    await slur_filter(ctx=ctx)

bot.run("MTAwMjgzMTgzNzY1NzMxNzQyNw.G-DB-6._H5YrCuBH3qtKehqPvQCns451Q9XEyDW70Rcio")
