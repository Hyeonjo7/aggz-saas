import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
ROLE_NAME = os.getenv("ROLE_NAME", "At Work")
DATABASE_PATH = "schedules.db"