import datetime
import asyncio

import discord
from discord.ext import commands
from discord.ext import tasks
import tokens
import database
import logging
import math

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_guild_join(guild):
    print(f'Logged in as {bot.user}')

    if guild.system_channel:
        await guild.system_channel.send('Hi! Welcome to Heroin. Type \'!help\' to get started using Heroin :)')

@bot.event
async def on_ready():
    if not check_reminder.is_running():
        check_reminder.start()

# @bot.listen()
# async def on_message(message):
#     print(f'Message from {message.author}: {message.content}')

@bot.event
async def on_scheduled_event_create(event):
    role = 'everyone'
    if event.description and event.description.split(" ")[0].startswith('@'):
        role = event.description.split(" ")[1]
    database.add_event(event.id, event.start_time, role, event.guild.id, event.name)

@bot.event
async def on_scheduled_event_delete(event):
    database.remove_event(event.id)

@bot.event
async def on_scheduled_event_update(before, after):
    database.remove_event(before.id)

    role = 'everyone'
    if after.description and after.description.split(" ")[0].startswith('@'):
        role = after.description.split(" ")[1]
    database.add_event(after.id, after.start_time, role, after.guild.id, after.name)

@bot.event
async def on_command_error(ctx, error):
    print(f"Command Error: {error}")
    await ctx.send(f"Something went wrong: {error}")

class RemindFlags(commands.FlagConverter, prefix='-', delimiter = ' '):
    w: int = 0
    d: int = 0
    h: int = 0
    m: int = 0

@bot.command()
async def remind(ctx, *, flags: RemindFlags):
    minutes = flags.m
    if minutes % 15 != 0:
        minutes = (math.ceil(minutes / 15)) * 15
    delta = datetime.timedelta(days=(flags.d + flags.w * 7), hours=flags.h, minutes=minutes)

    if database.get_recurrent_by_offset(delta):
        await ctx.send(f"Reminder for {delta} already exists.")
    else:
        database.add_recurrent(delta, ctx.guild.id)
        await ctx.send(f"Reminder set. I\'ll remind you {delta} before every event in this server.")

@bot.command()
async def show_all(ctx):
    reminders = database.get_recurrents()
    offsets = [reminder.offset for reminder in reminders]
    offsets.sort()

    output = 'Here\'s a list of your currently set reminders:\n'
    for offset in offsets:
        output += f'- {offset}\n'

    await ctx.send(output)

@bot.command()
async def remove(ctx, *, flags: RemindFlags):
    delta = datetime.timedelta(days=(flags.d + flags.w * 7), hours=flags.h, minutes=flags.m)
    database.remove_recurrent_by_offset(delta)
    await ctx.send(f'Reminder for {delta} has been removed.')

@bot.command(name='help')
async def custom_help(ctx, command: str = None):
    command = command.strip().lower() if command else None
    match command:
        case None:
            await base_help(ctx)
        case 'remind':
            await help_remind(ctx)
        case 'show_all':
            await help_show_all(ctx)
        case 'remove':
            await help_remove(ctx)
        case 'help':
            await help_help(ctx)
        case _:
            ctx.send('Unrecognized command.')


async def base_help(ctx):
    await ctx.send('Heroin has 3 main commands:\n'
        + '- `remind`: Set reminders\n'
        + '- `show_all`: Show your currently set reminders\n'
        + '- `remove`: Remove a reminder\n'
        + '\n'
        + 'To learn more about a command, type `!help` followed by the command that you\'d like to learn more about.')

async def help_remind(ctx):
    await ctx.send('The `!remind` command is how you set reminders.\n'
        + 'To use, type the command followed by your desired flags.\n'
        + '\n'
        + '`!remind` has 4 flags:\n'
        + '- `-w` => How many weeks before each event you want to be reminded\n'
        + '- `-d` => How many days\n'
        + '- `-h` => How many hours\n'
        + '- `-m` => How many minutes\n'
        + '\n'
        + 'Here are some examples:\n'
        + '- `!remind -w 1 -d 5 -h 2 -m 15`\n'
        + '- `!remind -d 2 -h 6`\n'
        + '\n'
        + 'NOTE: Reminders are checked every 15 minutes. Input minute values will be rounded up to the next multiple of 15.\n'
        + '\n'
        + 'When I remind you of an event, I\'ll mention everyone. To change this, just mention the role that you want me to mention instead at the start of the event\'s description!')

async def help_show_all(ctx):
    await ctx.send('The `!show_all` command shows you all of your reminders. No additional parameters required.')

async def help_remove(ctx):
    await ctx.send('The `!remove` command is how you remove reminders.\n'
        + 'To remove a reminder, fill in the flags matching the flags you used to create the reminder.\n'
        + '\n'
        + 'For more information about the flags, see the `!remind` command.')

async def help_help(ctx):
    await ctx.send('I\'m not really sure what you want me to tell you here man.')

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
                           f"{r.event_title}"
                           f"On {r.time.strftime('%I:%M %p')}"
                           f"In {r.time - now}")
    database.remove_due_individuals(now)
    database.remove_due_events(now)

@check_reminder.before_loop
async def before_check():
    await bot.wait_until_ready()

    now = datetime.datetime.now(datetime.timezone.utc)
    min_to_next = 15 - (now.minute % 15)
    next_time = now.replace(second=0, microsecond=0) + datetime.timedelta(minutes=min_to_next)

    await asyncio.sleep((next_time - now).total_seconds())

@check_reminder.error
async def check_reminder_error(error):
    print(error)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

bot.run(tokens.bot_token, log_handler=handler)