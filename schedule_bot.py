import datetime
import asyncio

import discord
from discord.ext import commands
from discord.ext import tasks
import tokens
import database
import logging

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_guild_join(guild):
    print(f'Logged in as {bot.user}')

    for guild in bot.guilds:
        if guild.system_channel:
            await guild.system_channel.send('Hi! Welcome to Heroin! Type \'!help\' to get started :)')

# @bot.listen()
# async def on_message(message):
#     print(f'Message from {message.author}: {message.content}')

@bot.event
async def on_scheduled_event_create(event):
    role = 'everyone'
    if event.description and event.description.split(" ").startswith('@'):
        role = event.description.split(" ")[1]
    database.add_event(event.id, event.start_time, role, event.guild.id, event.name)

@bot.event
async def on_scheduled_event_delete(event):
    database.remove_event(event.id)

@bot.event
async def on_scheduled_event_update(before, after):
    database.remove_event(before.id)

    role = 'everyone'
    if after.description and after.description.split(" ").startswith('@'):
        role = after.description.split(" ")[1]
    database.add_event(after.id, after.start_time, role, after.guild.id, after.name)

class RemindFlags(commands.FlagConverter, prefix='-', delimiter = ' '):
    w: int = 0
    d: int = 0
    h: int = 0
    m: int = 0

@bot.command()
async def remind(ctx, *, flags: RemindFlags):
    delta = datetime.timedelta(days=(flags.d + flags.w * 7), hours=flags.h, minutes=flags.m)
    await ctx.send(f"Reminder set! I\'ll remind you {delta} before every event in this server!")
    if flags.m % 15 != 0:
        await ctx.send('''WARNING: I check the time every 15 minutes, 
        so while I can *accept* timedelta values that are not evenly divisible by 15, 
        I will still only remind you the next time I check the time, 
        rather than the time you're asking for. Sorry!''')

@bot.command(name='help')
async def custom_help(ctx):
    await ctx.send('''
    To use Heroin, type \'!remind\', followed by your desired flags.
    
    I\'ve got 4 flags:
    > \'-w\' => How many weeks before each event you want to be reminded
    > \'-d\' => How many days 
    > \'-h\' => How many hours
    > \'-m\' => How many minutes
    
    Here are some examples:
    > `!remind -w 1 -d 5 -h 2 -m 15`
    > `!remind -d 2 -h 6`
    
    NOTE: Reminders are checked every 15 minutes. Minute values indivisible by 15 are allowed, but no different from minute values rounded up to the next multiple of 15.
    ''')

@tasks.loop(minutes=15)
async def check_reminder():
    now = datetime.datetime.now(datetime.timezone.utc)
    due = database.get_due_individuals(now)
    guilds = {}
    for r in due:
        if not guilds.get(r.guild_id):
            guilds[r.guild_id] = await bot.fetch_guild(r.guild_id)

        guild = guilds[r.guild_id]
        channel = guild.system_channel

        await channel.send(f"@{r.role}"
                           f"{r.title}"
                           f"On {r.time.strftime('%I:%M %p')}"
                           f"In {r.time - now.time()}")
    database.remove_due_individuals(now)
    database.remove_due_events(now)

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