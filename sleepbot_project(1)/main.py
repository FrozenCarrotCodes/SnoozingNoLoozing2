import os
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True  # Required to get voice states of members

bot = commands.Bot(command_prefix='!', intents=intents)

scheduled_shutdown = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def shutdownvc(ctx, minutes: int = 60):
    global scheduled_shutdown

    if scheduled_shutdown is not None and not scheduled_shutdown.done():
        await ctx.send("A shutdown is already scheduled. Use !cancelshutdown to cancel it first.")
        return

    async def kick_users_after_delay():
        await ctx.send(f"Voice shutdown scheduled in {minutes} minutes.")
        print(f"[DEBUG] Shutdown scheduled in {minutes} minutes.")
        await asyncio.sleep(minutes * 60)

        kicked_users = []
        for vc in ctx.guild.voice_channels:
            for member in vc.members:
                try:
                    await member.move_to(None)
                    kicked_users.append((member.display_name, vc.name))
                    print(f"[DEBUG] Kicked {member.display_name} from {vc.name}")
                except discord.Forbidden:
                    print(f"[DEBUG] Failed to kick {member.display_name} from {vc.name} (Missing Permissions)")

        if kicked_users:
            report = "\n".join([f"Kicked {user} from {channel}" for user, channel in kicked_users])
            await ctx.send(f"Shutdown complete. Users kicked:\n{report}")
        else:
            await ctx.send("Shutdown complete. No users were in voice channels.")

    scheduled_shutdown = asyncio.create_task(kick_users_after_delay())

@bot.command()
async def cancelshutdown(ctx):
    global scheduled_shutdown
    if scheduled_shutdown is not None and not scheduled_shutdown.done():
        scheduled_shutdown.cancel()
        scheduled_shutdown = None
        await ctx.send("Voice shutdown has been canceled.")
        print("[DEBUG] Shutdown task canceled.")
    else:
        await ctx.send("No shutdown is currently scheduled.")
        print("[DEBUG] No shutdown to cancel.")

@bot.command(name='commands')
async def list_commands(ctx):
    cmds = [
        "!shutdownvc [minutes] — Kicks all users from voice channels after the given number of minutes (default 60).",
        "!cancelshutdown — Cancels the scheduled voice channel shutdown.",
        "!commands — Shows this help message."
    ]
    await ctx.send("Available commands:\n" + "\n".join(cmds))

# Bot startup using Railway-provided environment variable
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
