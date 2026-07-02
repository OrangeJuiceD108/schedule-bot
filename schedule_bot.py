import discord
from discord.ext import commands
import tokens
import logging

class ScheduleBot(commands.Bot):
    pass

intents = discord.Intents.default()
intents.message_content = True

bot = ScheduleBot(command_prefix="!", intents=intents)

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
async def on_scheduled_event_update(event):
    pass

@bot.command()
async def remind(ctx):
    await ctx.send("nah")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

bot.run(tokens.bot_token, log_handler=handler)