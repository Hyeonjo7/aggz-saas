# Schedule bot

- **Run from project root:** `python3 -m app.main`  
  (Do not run from inside `app/` or `python3 app/main.py` — the `app` package must be on the path.)
- Dependencies: `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and set `DISCORD_TOKEN`, `GUILD_ID`, and optionally `ROLE_NAME`.
- **Role not attaching?** Create a role with the exact name in `ROLE_NAME` (e.g. "At Work"). In Server Settings → Roles, drag that role **below** the bot’s role (the bot can only assign roles beneath its own).