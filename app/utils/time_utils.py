from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

def should_be_on_shift(now_local: datetime, start_time: time, end_time: time):
    current = now_local.time()
    if start_time <= end_time:
        return start_time <= current <= end_time
    else:
        return current >= start_time or current <= end_time

def to_time_obj(time_str: str):
    return datetime.strptime(time_str, "%H:%M").time()

def parse_days(days_str: str):
    return [int(d) for d in days_str.split(",")]

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_ABBREV_TO_INT = {name.lower()[:3]: i for i, name in enumerate(DAY_NAMES)}

def parse_days_input(input_str: str) -> str:
    """Parse user input like 'mon,tue,wed' or '0,1,2' into stored format '0,1,2'."""
    parts = [p.strip().lower() for p in input_str.split(",") if p.strip()]
    out = []
    for p in parts:
        if p in DAY_ABBREV_TO_INT:
            out.append(DAY_ABBREV_TO_INT[p])
        elif p.isdigit() and 0 <= int(p) <= 6:
            out.append(int(p))
        else:
            raise ValueError(f"Invalid day: {p}. Use mon,tue,wed,thu,fri,sat,sun or 0-6.")
    if not out:
        raise ValueError("Specify at least one day (e.g. mon,tue,wed or 0,1,2).")
    return ",".join(str(d) for d in sorted(set(out)))

def format_days_display(days_str: str) -> str:
    """Turn stored '0,1,2' into 'Mon, Tue, Wed'."""
    try:
        nums = parse_days(days_str)
        return ", ".join(DAY_NAMES[i] for i in nums)
    except (ValueError, IndexError):
        return days_str


def get_next_role_change_utc(row, now_utc: datetime):
    """
    Given a schedule row and current UTC time, return (on_work_now, next_change_utc).
    next_change_utc is when the role would be added or removed (or None).
    """
    tz = ZoneInfo(row["timezone"])
    now_local = now_utc.astimezone(tz)
    start_t = to_time_obj(row["start_time"])
    end_t = to_time_obj(row["end_time"])
    work_days = parse_days(row["days"])

    if row["sick_until"]:
        sick_until = datetime.fromisoformat(row["sick_until"])
        if now_utc < sick_until:
            return (False, sick_until)

    if now_local.weekday() not in work_days:
        next_start = _next_shift_start_local(now_local, work_days, start_t, tz)
        return (False, next_start.astimezone(timezone.utc) if next_start else None)

    on_work_now = should_be_on_shift(now_local, start_t, end_t)
    if on_work_now:
        end_dt = _current_shift_end_local(now_local, start_t, end_t, tz)
        return (True, end_dt.astimezone(timezone.utc) if end_dt else None)
    else:
        next_start = _next_shift_start_local(now_local, work_days, start_t, tz)
        return (False, next_start.astimezone(timezone.utc) if next_start else None)


def _current_shift_end_local(now_local: datetime, start_t: time, end_t: time, tz: ZoneInfo) -> datetime | None:
    """When does the current shift end (in local time)?"""
    if start_t <= end_t:
        end_dt = now_local.replace(hour=end_t.hour, minute=end_t.minute, second=0, microsecond=0)
        if end_dt > now_local:
            return end_dt
        return None
    else:
        if now_local.time() >= start_t:
            end_dt = (now_local + timedelta(days=1)).replace(hour=end_t.hour, minute=end_t.minute, second=0, microsecond=0)
        else:
            end_dt = now_local.replace(hour=end_t.hour, minute=end_t.minute, second=0, microsecond=0)
        return end_dt if end_dt > now_local else None


def _next_shift_start_local(now_local: datetime, work_days: list[int], start_t: time, tz: ZoneInfo) -> datetime | None:
    """Next moment a shift starts (local time), strictly after now_local."""
    for d in range(8):
        candidate_date = (now_local.date() + timedelta(days=d))
        if candidate_date.weekday() not in work_days:
            continue
        start_dt = datetime(candidate_date.year, candidate_date.month, candidate_date.day,
                           start_t.hour, start_t.minute, start_t.second or 0, tzinfo=tz)
        if start_dt > now_local:
            return start_dt
    return None


def format_timedelta(td: timedelta) -> str:
    """Human-readable e.g. '2h 15m' or '45m'."""
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        return "now"
    if total_seconds < 60:
        return "under 1m"
    minutes, s = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) or "0m"