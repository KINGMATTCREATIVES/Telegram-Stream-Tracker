import sqlite3
import datetime
import os

DB_PATH = "tracker.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS streams (
        stream_id TEXT PRIMARY KEY,
        call_id TEXT,
        chat_title TEXT,
        start_time TEXT,
        end_time TEXT,
        duration_sec REAL DEFAULT 0,
        total_participants INTEGER DEFAULT 0,
        csv_path TEXT,
        is_active INTEGER DEFAULT 1
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS participants (
        stream_id TEXT,
        user_id INTEGER,
        name TEXT,
        username TEXT,
        first_join TEXT,
        last_leave TEXT,
        session_count INTEGER DEFAULT 1,
        total_sec REAL DEFAULT 0,
        total_min REAL DEFAULT 0,
        pct REAL DEFAULT 0,
        is_online INTEGER DEFAULT 1,
        PRIMARY KEY (stream_id, user_id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stream_id TEXT,
        user_id INTEGER,
        join_time TEXT,
        leave_time TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_stream_start(stream_id, call_id, chat_title, start_time_dt):
    conn = get_connection()
    c = conn.cursor()
    # Mark any previously active stream as closed
    c.execute("UPDATE streams SET is_active = 0 WHERE is_active = 1")
    c.execute("""
    INSERT OR REPLACE INTO streams (stream_id, call_id, chat_title, start_time, is_active)
    VALUES (?, ?, ?, ?, 1)
    """, (stream_id, str(call_id), chat_title, start_time_dt.isoformat()))
    conn.commit()
    conn.close()

def save_participant_join(stream_id, user_id, name, username, join_time_dt):
    conn = get_connection()
    c = conn.cursor()
    # Check if participant already exists in this stream
    c.execute("SELECT * FROM participants WHERE stream_id = ? AND user_id = ?", (stream_id, user_id))
    row = c.fetchone()
    join_str = join_time_dt.isoformat()

    if not row:
        c.execute("""
        INSERT INTO participants (stream_id, user_id, name, username, first_join, is_online, session_count)
        VALUES (?, ?, ?, ?, ?, 1, 1)
        """, (stream_id, user_id, name, username, join_str))
    else:
        # Update name/username if better info available
        curr_name = name if (name and not name.startswith("User ") and not name.startswith("Participant ")) else row["name"]
        curr_uname = username or row["username"]
        sess_count = row["session_count"] + (1 if row["is_online"] == 0 else 0)
        c.execute("""
        UPDATE participants
        SET name = ?, username = ?, is_online = 1, session_count = ?
        WHERE stream_id = ? AND user_id = ?
        """, (curr_name, curr_uname, sess_count, stream_id, user_id))

    # Insert a new session interval
    c.execute("""
    INSERT INTO sessions (stream_id, user_id, join_time)
    VALUES (?, ?, ?)
    """, (stream_id, user_id, join_str))

    conn.commit()
    conn.close()

def save_participant_leave(stream_id, user_id, leave_time_dt):
    conn = get_connection()
    c = conn.cursor()
    leave_str = leave_time_dt.isoformat()

    # Find the open session for this user
    c.execute("""
    SELECT id, join_time FROM sessions
    WHERE stream_id = ? AND user_id = ? AND leave_time IS NULL
    ORDER BY id DESC LIMIT 1
    """, (stream_id, user_id))
    sess = c.fetchone()

    added_sec = 0.0
    if sess:
        join_dt = datetime.datetime.fromisoformat(sess["join_time"])
        added_sec = max(0.0, (leave_time_dt - join_dt).total_seconds())
        c.execute("UPDATE sessions SET leave_time = ? WHERE id = ?", (leave_str, sess["id"]))

    # Update participant totals
    c.execute("SELECT total_sec FROM participants WHERE stream_id = ? AND user_id = ?", (stream_id, user_id))
    p = c.fetchone()
    if p:
        new_total_sec = p["total_sec"] + added_sec
        new_total_min = new_total_sec / 60.0
        c.execute("""
        UPDATE participants
        SET is_online = 0, last_leave = ?, total_sec = ?, total_min = ?
        WHERE stream_id = ? AND user_id = ?
        """, (leave_str, new_total_sec, new_total_min, stream_id, user_id))

    conn.commit()
    conn.close()

def save_stream_end(stream_id, end_time_dt, csv_path=""):
    conn = get_connection()
    c = conn.cursor()
    end_str = end_time_dt.isoformat()

    # Close any open sessions
    c.execute("""
    SELECT id, user_id, join_time FROM sessions
    WHERE stream_id = ? AND leave_time IS NULL
    """, (stream_id,))
    open_sessions = c.fetchall()

    for s in open_sessions:
        join_dt = datetime.datetime.fromisoformat(s["join_time"])
        added_sec = max(0.0, (end_time_dt - join_dt).total_seconds())
        c.execute("UPDATE sessions SET leave_time = ? WHERE id = ?", (end_str, s["id"]))
        
        c.execute("SELECT total_sec FROM participants WHERE stream_id = ? AND user_id = ?", (stream_id, s["user_id"]))
        p = c.fetchone()
        if p:
            new_sec = p["total_sec"] + added_sec
            c.execute("""
            UPDATE participants
            SET is_online = 0, last_leave = ?, total_sec = ?, total_min = ?
            WHERE stream_id = ? AND user_id = ?
            """, (end_str, new_sec, new_sec / 60.0, stream_id, s["user_id"]))

    # Calculate total stream duration
    c.execute("SELECT start_time FROM streams WHERE stream_id = ?", (stream_id,))
    st = c.fetchone()
    total_stream_sec = 1.0
    if st and st["start_time"]:
        start_dt = datetime.datetime.fromisoformat(st["start_time"])
        total_stream_sec = max(1.0, (end_time_dt - start_dt).total_seconds())

    # Update participation percentage for all participants
    c.execute("SELECT user_id, total_sec FROM participants WHERE stream_id = ?", (stream_id,))
    all_p = c.fetchall()
    for p in all_p:
        pct = min(100.0, (p["total_sec"] / total_stream_sec) * 100.0)
        c.execute("UPDATE participants SET pct = ? WHERE stream_id = ? AND user_id = ?", (pct, stream_id, p["user_id"]))

    total_count = len(all_p)
    c.execute("""
    UPDATE streams
    SET end_time = ?, duration_sec = ?, total_participants = ?, csv_path = ?, is_active = 0
    WHERE stream_id = ?
    """, (end_str, total_stream_sec, total_count, csv_path, stream_id))

    conn.commit()
    conn.close()

def get_latest_stream():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM streams ORDER BY rowid DESC LIMIT 1")
    stream = c.fetchone()
    if not stream:
        conn.close()
        return None, []

    c.execute("""
    SELECT * FROM participants
    WHERE stream_id = ?
    ORDER BY total_sec DESC
    """, (stream["stream_id"],))
    participants = c.fetchall()
    conn.close()
    return dict(stream), [dict(p) for p in participants]

def get_stream_history(limit=5):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM streams WHERE is_active = 0 ORDER BY rowid DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
