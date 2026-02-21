from app.db.database import init_db
from app.bot.client import bot
from app.core.config import DISCORD_TOKEN

if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN.strip() in ("", "YOUR_BOT_TOKEN", "YOUR_TOKEN"):
        print("Error: Set a valid DISCORD_TOKEN in .env")
        print("  1. Go to https://discord.com/developers/applications")
        print("  2. Select your app → Bot → Reset/Copy token")
        print("  3. Put it in .env as DISCORD_TOKEN=your_token")
        raise SystemExit(1)
    init_db()  # create SQLite tables
    bot.run(DISCORD_TOKEN)