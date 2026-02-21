from discord.ext import tasks
from app.services.schedule_service import get_active_users
from app.services.role_service import update_roles

def start_scheduler(bot):
    @tasks.loop(minutes=1)
    async def loop():
        active = get_active_users()
        await update_roles(bot, active)

    @loop.before_loop
    async def before_loop():
        await bot.wait_until_ready()
        # Run once immediately so roles apply without waiting 1 minute
        active = get_active_users()
        await update_roles(bot, active)

    loop.start()