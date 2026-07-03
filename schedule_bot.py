import datetime
import asyncio

import discord
from discord.ext import commands
from discord.ext import tasks
import tokens
import reminder
import logging

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

    for guild in bot.guilds:
        if guild.system_channel:
            await guild.system_channel.send('Hello!')

@bot.listen()
async def on_message(message):
    print(f'Message from {message.author}: {message.content}')

@bot.event
async def on_scheduled_event_create(event):
    if event.guild.system_channel:
        await event.guild.system_channel.send('Event created!')

@bot.event
async def on_scheduled_event_delete(event):
    if event.guild.system_channel:
        await event.guild.system_channel.send('Event deleted!')

@bot.event
async def on_scheduled_event_update(before, after):
    pass

@bot.command()
async def remind(ctx):
    await ctx.send("nah")

@tasks.loop(minutes=15)
async def check_reminder():
    now = datetime.datetime.now(datetime.timezone.utc)
    due = reminder.get(now)
    for r in due:
        channel = bot.get_channel(r.channel_id)
        # replace test with message
        await channel.send('test')
        reminder.remove(reminder.id)

    # get our reminders
    # iterate through the reminders
    # if the reminder is up, post

@check_reminder.before_loop
async def before_check():
    await bot.wait_until_ready()

    now = datetime.datetime.now(datetime.timezone.utc)
    min_to_next = 15 - (now.minute % 15)
    next_time = now.replace(second=0, microsecond=0) + datetime.timedelta(minutes=min_to_next)

    await asyncio.sleep((next_time - now).total_seconds())

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

bot.run(tokens.bot_token, log_handler=handler)

check_reminder.start()