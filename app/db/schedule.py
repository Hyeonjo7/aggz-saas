from app.db.database import get_connection

def insert_or_update_schedule(user_id, timezone, start, end, days):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO schedules
        (user_id, timezone, start_time, end_time, days, sick_until)
        VALUES (?, ?, ?, ?, ?, NULL)
    """, (user_id, timezone, start, end, days))
    conn.commit()
    conn.close()

def get_schedule(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_sick(user_id, sick_until):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE schedules
        SET sick_until=?
        WHERE user_id=?
    """, (sick_until, user_id))
    conn.commit()
    conn.close()

def update_days(user_id, days):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE schedules
        SET days=?
        WHERE user_id=?
    """, (days, user_id))
    conn.commit()
    conn.close()

def get_all_schedules():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules")
    rows = cursor.fetchall()
    conn.close()
    return rows