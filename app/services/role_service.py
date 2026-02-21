import discord
from app.core.config import ROLE_NAME, GUILD_ID

async def update_roles(bot, active_user_ids):
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print(f"[Role] Guild {GUILD_ID} not found. Is the bot in that server? Is GUILD_ID in .env correct?")
        return

    role = next((r for r in guild.roles if r.name == ROLE_NAME), None)
    if role is None:
        print(f"[Role] Role '{ROLE_NAME}' not found on the server. Create a role with that exact name (case-sensitive).")
        return

    # Bot can only assign roles that are BELOW its highest role in Server Settings → Roles
    bot_member = guild.get_member(bot.user.id)
    if bot_member and bot_member.top_role <= role:
        print(f"[Role] Cannot assign '{ROLE_NAME}': it must be below the bot's role in Server Settings → Roles (drag it down).")
        return

    for member in guild.members:
        try:
            if member.id in active_user_ids:
                if role not in member.roles:
                    await member.add_roles(role)
            else:
                if role in member.roles:
                    await member.remove_roles(role)
        except discord.Forbidden:
            print(f"[Role] Missing permission to manage roles for {member}. Bot needs 'Manage Roles' and the role must be below the bot's role.")