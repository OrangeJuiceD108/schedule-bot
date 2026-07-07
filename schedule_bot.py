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

@bot.command()
async def remind(ctx, args):
    await ctx.send("nah")

@bot.command(name='help')
async def custom_help(ctx, args=None):
    await ctx.send('nah')

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