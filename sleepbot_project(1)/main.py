import discord
from discord.ext import commands, tasks
import asyncio
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

shutdown_task = None

@bot.event
async def on_ready():
    print(f'[INFO] Bot connected as {bot.user}')

@bot.command(name='shutdownvc')
async def shutdown_vc(ctx, minutes: int):
    global shutdown_task

    if shutdown_task is not None:
        await ctx.send("A shutdown is already scheduled. Use `!cancelshutdown` to stop it.")
        print("[DEBUG] Shutdown already scheduled.")
        return

    await ctx.send(f"Voice shutdown scheduled in {minutes} minute(s).")
    print(f"[DEBUG] Shutdown scheduled by {ctx.author} in {minutes} minutes.")

    async def shutdown():
        global shutdown_task
        await asyncio.sleep(minutes * 60)
        guild = ctx.guild
        kicked = []

        for vc in guild.voice_channels:
            for member in vc.members:
                try:
                    await member.move_to(None)
                    kicked.append((member.display_name, vc.name))
                    print(f"[DEBUG] Kicked {member.display_name} from {vc.name}")
                except Exception as e:
                    print(f"[ERROR] Could not kick {member.display_name} from {vc.name}: {e}")

        if kicked:
            lines = [f"**Kicked the following users from voice channels:**"]
            for name, channel in kicked:
                lines.append(f"- `{name}` from `{channel}`")
            await ctx.send("\n".join(lines))
        else:
            await ctx.send("No users were in voice channels to kick.")

        shutdown_task = None

    shutdown_task = asyncio.create_task(shutdown())

@bot.command(name='cancelshutdown')
async def cancel_shutdown(ctx):
    global shutdown_task
    if shutdown_task is None:
        await ctx.send("No shutdown is currently scheduled.")
        print("[DEBUG] Cancel attempted, but no shutdown was running.")
    else:
        shutdown_task.cancel()
        shutdown_task = None
        await ctx.send("Shutdown has been cancelled.")
        print("[DEBUG] Shutdown cancelled by user.")

@bot.command(name='help')
async def help_command(ctx):
    help_text = (
        "**SleepBot Commands:**\n"
        "`!shutdownvc <minutes>` — Kicks all users from voice channels after the given time.\n"
        "`!cancelshutdown` — Cancels a scheduled voice channel shutdown.\n"
        "`!help` — Shows this help message."
    )
    await ctx.send(help_text)
    print(f"[DEBUG] Help command triggered by {ctx.author}")

bot.run(TOKEN)