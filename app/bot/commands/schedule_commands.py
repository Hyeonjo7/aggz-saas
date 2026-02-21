import discord
from discord import app_commands
from app.db.schedule import insert_or_update_schedule, get_schedule, update_days
from app.utils.time_utils import parse_days_input, format_days_display

async def register_schedule_commands(tree, GUILD_ID):
    guild = discord.Object(id=GUILD_ID)

    @tree.command(name="setwork", description="Set your work schedule", guild=guild)
    @app_commands.describe(
        start="Start time (e.g. 09:00)",
        end="End time (e.g. 17:00)",
        days="Work days: comma-separated, e.g. mon,tue,wed,thu,fri or 0,1,2,3,4 (0=Mon, 6=Sun)",
    )
    async def setwork(interaction, start: str, end: str, days: str = "mon,tue,wed,thu,fri"):
        try:
            days_stored = parse_days_input(days)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return
        insert_or_update_schedule(interaction.user.id, "Australia/Sydney", start, end, days_stored)
        days_display = format_days_display(days_stored)
        await interaction.response.send_message(f"Schedule saved: {start}–{end} on {days_display}.")

    @tree.command(name="setdays", description="Change which days you work (keeps your start/end times)", guild=guild)
    @app_commands.describe(
        days="Work days: comma-separated, e.g. mon,tue,wed,thu,fri or 0,1,2,3,4 (0=Mon, 6=Sun)",
    )
    async def setdays(interaction, days: str):
        row = get_schedule(interaction.user.id)
        if not row:
            await interaction.response.send_message("Set your schedule first with `/setwork start end days`.", ephemeral=True)
            return
        try:
            days_stored = parse_days_input(days)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return
        update_days(interaction.user.id, days_stored)
        days_display = format_days_display(days_stored)
        await interaction.response.send_message(f"Work days updated to: {days_display}.")

    @tree.command(name="myschedule", description="View your schedule", guild=guild)
    async def myschedule(interaction):
        row = get_schedule(interaction.user.id)
        if not row:
            await interaction.response.send_message("No schedule set.")
            return
        status = "Sick until " + row["sick_until"] if row["sick_until"] else "Active"
        days_display = format_days_display(row["days"])
        await interaction.response.send_message(
            f"Times are Australia/Sydney.\nStart: {row['start_time']}\nEnd: {row['end_time']}\nDays: {days_display}\nStatus: {status}"
        )