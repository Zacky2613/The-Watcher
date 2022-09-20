from discord.flags import Intents
from discord.ext import commands
import discord.utils
import datetime
import discord
import random
import json
import os


bot = commands.Bot(command_prefix='!', Intents=Intents)
bot.remove_command("help")

messagelist = [
    "🤨📸",
    "stfu",
    "life privileges removed",
    "Bro, you had 1 job",
    "Comeon man",
    "Got yo ass"
]

with open("./Json/words.json", "r") as f:
    data = json.load(f)


async def slur_filter(ctx: discord.message.Message):
    username = ctx.author
    time = datetime.datetime.now().strftime("%d/%m/%y %H:%M")

    for i in data["_replace_letters"]:
        ctx.content = ctx.content.lower().replace(
            data["_replace_letters"][i][0],
            data["_replace_letters"][i][1]
        )

    for word in data["_banned_words"]:
        if word in ctx.content:
            await ctx.delete()

            print(f'{time} {username}: "{ctx.content}" ')
            # e.g: 20/09/22 user#0000: "debugtool"

            with open('logs/logs', 'a') as f:
                f.write(f'\n{time} {username}: {ctx.content}')
                f.close()

            await ctx.channel.send(f"{username.mention} {messagelist[random.randint(0, len(messagelist)) - 1]}  <@&997059007799898172> <@&811902871029153802>")

        elif str(ctx.id) in data["_blocked_users"]:
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
    userid = userid.replace("<", "").replace(">", "").replace("@", "")
    data["_blocked_users"].append(userid)

    with open("./Json/words.json", "w") as f:
        json.dump(data, f, indent=4)


@bot.event
async def on_ready():
    print("Bot is running.")
    activity = discord.Game(name="Looking for food")
    await bot.change_presence(status=discord.Status.online, activity=activity)


@bot.event
async def on_message_edit(before, after):
    await slur_filter(ctx=after)


@bot.event
async def on_message(ctx):
    await slur_filter(ctx=ctx)

bot.run(os.environ["DISCORD_TOKEN"])
