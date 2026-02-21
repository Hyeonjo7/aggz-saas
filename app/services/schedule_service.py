from app.db.schedule import get_all_schedules
from app.utils.time_utils import should_be_on_shift, to_time_obj, parse_days
from datetime import datetime
from zoneinfo import ZoneInfo

def get_active_users():
    now_utc = datetime.utcnow()
    active = []

    for row in get_all_schedules():
        tz = ZoneInfo(row["timezone"])
        now_local = now_utc.astimezone(tz)

        days = parse_days(row["days"])
        if now_local.weekday() not in days:
            continue

        if row["sick_until"]:
            sick_until = datetime.fromisoformat(row["sick_until"])
            if now_utc < sick_until:
                continue

        start = to_time_obj(row["start_time"])
        end = to_time_obj(row["end_time"])

        if should_be_on_shift(now_local, start, end):
            active.append(row["user_id"])
    return active