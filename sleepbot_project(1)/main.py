import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')  # Avoid conflict with default help

shutdown_task = None

@bot.event
async def on_ready():
    print(f"[DEBUG] Logged in as {bot.user.name} - {bot.user.id}")
    print("[DEBUG] Bot is ready.")

@bot.command(name='shutdownvc')
async def shutdown_vc(ctx, minutes: float = 60):
    global shutdown_task

    if shutdown_task and not shutdown_task.done():
        await ctx.send("A shutdown is already scheduled. Use `!cancelshutdown` to cancel it.")
        return

    delay = minutes * 60
    await ctx.send(f"Voice channel shutdown scheduled in {minutes} minute(s).")
    print(f"[DEBUG] Shutdown scheduled in {minutes} minute(s).")

    async def shutdown():
        await asyncio.sleep(delay)
        kicked_users = []
        for guild in bot.guilds:
            for vc in guild.voice_channels:
                for member in vc.members:
                    try:
                        await member.move_to(None)
                        kicked_users.append((member.name, vc.name))
                        print(f"[DEBUG] Kicked {member.name} from {vc.name}")
                    except Exception as e:
                        print(f"[ERROR] Could not kick {member.name}: {e}")

        if kicked_users:
            report = "**Voice Shutdown Complete.**\n"
            report += "\n".join([f"🔇 Kicked `{user}` from `{channel}`" for user, channel in kicked_users])
        else:
            report = "No users were in voice channels at shutdown time."

        await ctx.send(report)

    shutdown_task = asyncio.create_task(shutdown())

@bot.command(name='cancelshutdown')
async def cancel_shutdown(ctx):
    global shutdown_task
    if shutdown_task and not shutdown_task.done():
        shutdown_task.cancel()
        await ctx.send("Voice channel shutdown has been cancelled.")
        print("[DEBUG] Shutdown cancelled.")
    else:
        await ctx.send("No shutdown is currently scheduled.")

@bot.command(name='help')
async def help_command(ctx):
    help_text = (
        "**SleepBot Commands:**\n"
        "`!shutdownvc <minutes>` – Schedule a voice channel shutdown. Kicks all users from VCs after the given number of minutes.\n"
        "`!cancelshutdown` – Cancel a scheduled voice channel shutdown.\n"
        "`!help` – Show this help message."
    )
    await ctx.send(help_text)
    print("[DEBUG] Help command invoked.")

bot.run(TOKEN)
