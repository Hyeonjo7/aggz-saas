import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from app.core.config import DISCORD_TOKEN, GUILD_ID, ROLE_NAME
from app.bot.commands import schedule_commands, sick_commands
from app.scheduler.scheduler import start_scheduler
from app.services.schedule_service import get_active_users
from app.db.schedule import get_schedule
from app.utils.time_utils import format_days_display, get_next_role_change_utc, format_timedelta

intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # required for prefix commands like !help
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")  # use our custom !help below

help_guild = discord.Object(id=GUILD_ID)


def make_help_embed():
    embed = discord.Embed(
        title="Schedule bot – commands",
        description="Slash commands (type `/` to see them). You can also use `!help`.",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="`/setwork`",
        value="Set your work schedule.\n**Usage:** `/setwork start end days`\n**Example:** `/setwork 09:00 17:00 mon,tue,wed,thu,fri` or `0,1,2,3,4` (0=Mon, 6=Sun)",
        inline=False,
    )
    embed.add_field(
        name="`/setdays`",
        value="Change which days you work (keeps start/end times).\n**Usage:** `/setdays days`\n**Example:** `/setdays mon,wed,fri`",
        inline=False,
    )
    embed.add_field(
        name="`/myschedule`",
        value="View your current schedule and status.\n**Usage:** `/myschedule`",
        inline=False,
    )
    embed.add_field(
        name="`/sick`",
        value="Mark yourself sick for a number of hours.\n**Usage:** `/sick hours`\n**Example:** `/sick 24`",
        inline=False,
    )
    embed.add_field(
        name="`/back`",
        value="Clear your sick status and return from sick.\n**Usage:** `/back`",
        inline=False,
    )
    embed.add_field(
        name="`/time`",
        value="Show current time (UTC + Sydney). For testing.",
        inline=False,
    )
    embed.add_field(
        name="`/rolestatus`",
        value="Debug: see why the At Work role might not be attached.",
        inline=False,
    )
    embed.set_footer(text="/help or !help – show this message")
    return embed


@bot.command(name="help")
async def help_prefix(ctx):
    """List all commands and usage examples (prefix: !help)."""
    await ctx.send(embed=make_help_embed())


@bot.tree.command(name="help", description="List all commands and usage examples", guild=help_guild)
async def help_slash(interaction: discord.Interaction):
    """List all commands and usage examples (slash: /help)."""
    await interaction.response.send_message(embed=make_help_embed())


@bot.tree.command(name="time", description="Show current time (for testing)", guild=help_guild)
async def time_slash(interaction: discord.Interaction):
    """Show current time in UTC and Australia/Sydney."""
    now_utc = datetime.now(timezone.utc)
    tz_sydney = ZoneInfo("Australia/Sydney")
    now_sydney = now_utc.astimezone(tz_sydney)
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][now_utc.weekday()]
    msg = (
        f"**UTC:** {now_utc.strftime('%Y-%m-%d %H:%M:%S')} ({weekday})\n"
        f"**Australia/Sydney:** {now_sydney.strftime('%Y-%m-%d %H:%M:%S')} ({weekday})"
    )
    await interaction.response.send_message(msg)


@bot.tree.command(name="rolestatus", description="Debug: why the At Work role might not be attached", guild=help_guild)
async def rolestatus_slash(interaction: discord.Interaction):
    """Show role/guild status and who should have the role right now."""
    now_utc = datetime.now(timezone.utc)
    tz_sydney = ZoneInfo("Australia/Sydney")
    now_sydney = now_utc.astimezone(tz_sydney)
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][now_utc.weekday()]

    lines = [
        f"**Time (UTC):** {now_utc.strftime('%H:%M:%S')} · **Sydney:** {now_sydney.strftime('%H:%M:%S')} · **Day:** {weekday}",
        "",
    ]

    guild = interaction.client.get_guild(GUILD_ID)
    if guild is None:
        lines.append(f"Guild `{GUILD_ID}` not found. Check GUILD_ID in .env and that the bot is in the server.")
        await interaction.response.send_message("\n".join(lines), ephemeral=True)
        return

    lines.append(f"Guild: **{guild.name}**")

    role = next((r for r in guild.roles if r.name == ROLE_NAME), None)
    if role is None:
        lines.append(f"Role **{ROLE_NAME}** not found. Create a role with that exact name (case-sensitive).")
        await interaction.response.send_message("\n".join(lines), ephemeral=True)
        return

    lines.append(f"Role: **{ROLE_NAME}** (position {role.position})")

    bot_member = guild.get_member(interaction.client.user.id)
    if bot_member:
        lines.append(f"   Bot's highest role position: **{bot_member.top_role.position}**")
        if bot_member.top_role <= role:
            lines.append(f"   **At Work** must be *below* the bot's role. Drag it down in Server Settings -> Roles.")
        else:
            lines.append(f"   Hierarchy OK (bot can assign this role).")

    active_ids = get_active_users()
    lines.append("")
    lines.append(f"**Should have role right now:** {len(active_ids)} user(s)")
    if active_ids:
        for uid in active_ids[:10]:
            m = guild.get_member(uid)
            name = m.display_name if m else str(uid)
            has_role = role in m.roles if m else False
            lines.append(f"   - {name} (ID {uid}) — {'has role' if has_role else 'missing role'}")
        if len(active_ids) > 10:
            lines.append(f"   ... and {len(active_ids) - 10} more")

    you_in = interaction.user.id in active_ids
    lines.append("")
    lines.append(f"You: **{'On work' if you_in else 'Not on work'}**")

    row = get_schedule(interaction.user.id)
    if row:
        lines.append("")
        lines.append("**Your schedule (Sydney):**")
        lines.append(f"   {row['start_time']} – {row['end_time']} on {format_days_display(row['days'])}")
        on_work, next_utc = get_next_role_change_utc(row, now_utc)
        if next_utc:
            delta = next_utc - now_utc
            sick_until_str = row["sick_until"]
            if sick_until_str and next_utc == datetime.fromisoformat(sick_until_str):
                lines.append(f"   Sick ends in **{format_timedelta(delta)}** (at {next_utc.astimezone(tz_sydney).strftime('%H:%M')} Sydney).")
            elif on_work:
                lines.append(f"   Role will be **removed** in **{format_timedelta(delta)}** (at {next_utc.astimezone(tz_sydney).strftime('%H:%M')} Sydney).")
            else:
                lines.append(f"   Role will be **added** in **{format_timedelta(delta)}** (at {next_utc.astimezone(tz_sydney).strftime('%H:%M')} Sydney).")
        elif row["sick_until"]:
            sick_until = datetime.fromisoformat(row["sick_until"])
            lines.append(f"   Sick until {sick_until.astimezone(tz_sydney).strftime('%Y-%m-%d %H:%M')} Sydney.")
    else:
        lines.append("")
        lines.append("No schedule set. Use `/setwork` to set your work times.")

    await interaction.response.send_message("\n".join(lines), ephemeral=True)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    guild = discord.Object(id=GUILD_ID)
    await schedule_commands.register_schedule_commands(bot.tree, GUILD_ID)
    await sick_commands.register_sick_commands(bot.tree, GUILD_ID)
    await bot.tree.sync(guild=guild)  # sync to your server so slash commands show up
    start_scheduler(bot)  # start scheduler