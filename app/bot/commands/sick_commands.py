import discord
from discord import app_commands
from app.db.schedule import update_sick
from datetime import datetime, timedelta

async def register_sick_commands(tree, GUILD_ID):
    guild = discord.Object(id=GUILD_ID)

    @tree.command(name="sick", description="Mark yourself sick", guild=guild)
    async def sick(interaction, hours: int):
        until = datetime.utcnow() + timedelta(hours=hours)
        update_sick(interaction.user.id, until.isoformat())
        await interaction.response.send_message(f"Sick for {hours} hours")

    @tree.command(name="back", description="Return from sick", guild=guild)
    async def back(interaction):
        update_sick(interaction.user.id, None)
        await interaction.response.send_message("You are back from sick")