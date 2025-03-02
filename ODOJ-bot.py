import discord
from discord.ext import commands, tasks
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import os
import json
from flask import Flask
from threading import Thread
import logging
from asyncio import sleep

# Setup bot
# DC bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

TOKEN = os.environ["DISCORD_BOT_TOKEN"]

bot = commands.Bot(command_prefix="!", intents=intents)
LOG_CHANNEL_ID = 1345452618264350751  # Replace with your private log channel ID

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")


# Function to send logs to Discord
async def send_log_to_discord(message):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"📝 {message}")


@bot.event
async def on_command_error(ctx, error):
    await send_log_to_discord(f"❌ Error: {error}")
    logger.error(f"Error: {error}")


# Keeping bot alive
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running!"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    server = Thread(target=run)
    server.start()


# Get current UTC time properly
utc_now = datetime.now(pytz.UTC)

# Convert to Indonesia Time (WIB, WITA, or WIT)
indonesia_tz = pytz.timezone("Asia/Jakarta")  # WIB (UTC+7)
local_time = utc_now.astimezone(indonesia_tz)

# G Sheets setup
creds_json = os.getenv("GSPREAD_CREDENTIALS")

if creds_json is None:
    raise ValueError("GSPREAD_CREDENTIALS is missing!")

creds_dict = json.loads(creds_json)  # Convert JSON string back to dict

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
daily_sheet = client.open("ODOJ_database").worksheet("daily")
khatam_sheet = client.open("ODOJ_database").worksheet("khatam")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

    await send_log_to_discord("✅ Bot is online!")
    logger.info("Bot is running!")

    """Re-add reactions to the role message when the bot starts."""
    if role_message_id:
        for guild in bot.guilds:
            for channel in guild.text_channels:
                try:
                    message = await channel.fetch_message(role_message_id)
                    for emoji in emoji_to_role.keys():
                        await message.add_reaction(emoji)
                    await send_log_to_discord(
                        "✅ Ensured reactions on role assignment message."
                    )
                    return  # Stop searching once found
                except:
                    continue


# Load existing role message ID (if any)
def load_role_message():
    try:
        with open("role_config.json", "r") as file:
            return json.load(file).get("role_message_id", None)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_role_message(message_id):
    with open("role_config.json", "w") as file:
        json.dump({"role_message_id": message_id}, file)


role_message_id = load_role_message()  # Load saved message ID

emoji_to_role = {
    "👳‍♀️": 1345361603805319288,  # Replace with actual role IDs
    "🧕": 1345361683845222441,
}


@bot.command()
@commands.has_role("admin")
async def setrolemessage(ctx, message_id: int):
    """Sets the message ID and stores it for role assignment."""
    global role_message_id
    role_message_id = message_id
    save_role_message(message_id)  # Save to file

    message = await ctx.channel.fetch_message(message_id)

    # Add all predefined reactions
    for emoji in emoji_to_role.keys():
        await message.add_reaction(emoji)

    await ctx.send(
        f"✅ Tracking reactions on message ID {message_id} with default emojis."
    )


@bot.event
async def on_raw_reaction_add(payload):
    """Assigns a role when a user reacts to the stored message."""
    if role_message_id and payload.message_id == role_message_id:
        guild = bot.get_guild(payload.guild_id)
        role_id = emoji_to_role.get(payload.emoji.name)

        if role_id:
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)

            if member and role and not member.bot:
                await member.add_roles(role)
                
                await member.send(f"You have been assigned the role of {role.name}")

                log_channel = bot.get_channel(
                    1345452618264350751
                )  # Replace with log channel ID
                if log_channel:
                    await log_channel.send(
                        f"✅ Assigned {role.name} to {member.display_name}"
                    )


@bot.event
async def on_raw_reaction_remove(payload):
    """Removes a role when a user removes their reaction."""
    if role_message_id and payload.message_id == role_message_id:
        guild = bot.get_guild(payload.guild_id)
        role_id = emoji_to_role.get(payload.emoji.name)

        if role_id:
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)

            if member and role and not member.bot:
                await member.remove_roles(role)

                log_channel = bot.get_channel(
                    1345452618264350751
                )  # Replace with log channel ID
                if log_channel:
                    await log_channel.send(
                        f"❌ Removed {role.name} from {member.display_name}"
                    )


@bot.command()
async def khalas(ctx):
    """User submits recitation completion."""
    user = str(ctx.author.display_name)
    date = local_time.strftime("%d-%m-%Y")

    # Confirmation message
    message = await ctx.send(
        f"{ctx.author.mention}, have you completed Qur'an recitation?"
    )
    await message.add_reaction("✅")
    await message.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

    reaction, _ = await bot.wait_for("reaction_add", check=check)
    if str(reaction.emoji) == "✅":
        # Find column index for today's date
        row_headers = daily_sheet.row_values(1)  # Get the first row (headers)
        if date in row_headers:
            col_index = row_headers.index(date) + 1  # Find existing column
        else:
            col_index = len(row_headers) + 1  # Add a new column if not found
            daily_sheet.update_cell(1, col_index, date)  # Update header

        # Find user's row
        user_cells = daily_sheet.col_values(1)
        if user in user_cells:
            user_row = user_cells.index(user) + 1  # Find user's row
        else:
            user_row = len(user_cells) + 1  # Add a new row if not found
            daily_sheet.update_cell(user_row, 1, user)  # Add user to first column

        # Update recitation status and id
        daily_sheet.update_cell(user_row, col_index, "TRUE")
        daily_sheet.update_cell(user_row, 2, str(ctx.author.id))
        await ctx.send(f"✅ {ctx.author.mention}, your recitation has been recorded!")
        await ctx.send(
            "**Alhamdulillah dikit-dikit, jadi bukit! Terima kasih telah tilawah hari ini, tetap semangat dan istiqomah ya!**"
        )
    else:
        await ctx.send(f"❌ {ctx.author.mention}, submission cancelled.")


@bot.command()
async def khatam(ctx):
    """Logs the overall completion progress for a user."""
    member = ctx.author

    # Get current date
    completion_date = local_time.strftime("%d-%m-%Y")

    # Confirmation message
    message = await ctx.send(
        f"{ctx.author.mention}, have you completed Qur'an recitation?"
    )
    await message.add_reaction("✅")
    await message.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

    reaction, _ = await bot.wait_for("reaction_add", check=check)
    if str(reaction.emoji) == "✅":
        # Append new row in Google Sheets (username, user_id, date)
        khatam_sheet.append_row([member.display_name, str(member.id), completion_date])
        await ctx.send(
            f"✅ {ctx.author.mention}, your completion has been recorded on {completion_date}!"
        )
        await ctx.send(
            "**Maasya Allah tabarakallah, selamat sudah berhasil khatam Al-Qur'an semoga Allah ridhoi dan berkahi selalu! JANGAN LUPA KASIH APA? KASIH W, KASIH O, KASIH W, WOW KEREN, WOW WOW KEREN! 👏🏻**"
        )

    else:
        await ctx.send(f"❌ {ctx.author.mention}, submission cancelled.")


@tasks.loop(hours=24)
async def daily_reminder():
    guild = bot.get_guild(1271467172258119763)  # Replace with your server ID
    role_names = ["Ikhwan", "Akhwat"]  # Add multiple role names here
    members_to_notify = set()  # Use a set to avoid duplicate members

    for role_name in role_names:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            members_to_notify.update(role.members)

        count = 0
    for member in members_to_notify:
        try:
            await member.send(
                "📖 Reminder: Don't forget to complete your daily recitation!"
            )
            await member.send(
                "Report your recitation at <#1345388935186087956>! or <#1345388978635014164>"
            )
            count += 1
        except discord.Forbidden:
            await send_log_to_discord(f"❌ Couldn't send DM to {member.name}.")

    await send_log_to_discord(
        f"✅ Sent reminders to a total of {count} Ikhwan and Akhwat!"
    )


@bot.command()
async def progress(ctx):
    """Sends user their recitation progress via DM."""
    user_id = str(ctx.author.id)

    # Try to find user data
    user_data = daily_sheet.find(user_id)
    user_completion = khatam_sheet.find(user_id)

    if user_data or user_completion:
        completed_days = 0
        if user_data:  # Ensure the user exists before accessing row values
            row_values = daily_sheet.row_values(user_data.row)
            completed_days = row_values.count("TRUE")

        # Fetch all user IDs from the sheet
        user_ids = khatam_sheet.col_values(2)  # Column 2 contains user IDs
        completion_count = user_ids.count(user_id)

        # DM the user with their progress
        await ctx.author.send(
            f"📊 Your progress:\n"
            f"✅ Daily Recitation: {completed_days} days completed.\n"
            f"📖 Overall Completion: {completion_count} times."
        )
    else:
        await ctx.author.send("No records found.")


@bot.command()
@commands.has_role("admin")
async def start_reminders(ctx):
    """Start daily reminders (admin only)."""
    daily_reminder.start()
    await ctx.send("Daily reminders started!")


@bot.command()
@commands.has_role("admin")
async def stop_reminders(ctx):
    """Stop daily reminders (admin only)."""
    daily_reminder.cancel()
    await ctx.send("Daily reminders stopped!")


@bot.command()
@commands.has_role("admin")
async def reset_reminders(ctx):
    """Reset daily reminders (admin only)."""
    if daily_reminder.is_running():
        daily_reminder.cancel()
        await sleep(1)
        daily_reminder.start()
        await ctx.send("Daily reminders have been reseted!")


@bot.command()
@commands.has_role("admin")
async def reminder_status(ctx):
    """Checks if the reminder loop is running."""
    status = "✅ Running" if daily_reminder.is_running() else "⏹️ Stopped"
    await ctx.send(f"Reminder loop status: {status}")


# Run the bot
keep_alive()
bot.run(TOKEN)
