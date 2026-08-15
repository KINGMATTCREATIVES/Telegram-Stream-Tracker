import os
from telethon.sessions import StringSession, SQLiteSession

SESSION_FILE = "tracker_session.session"

if not os.path.exists(SESSION_FILE):
    print(f"[ERROR] '{SESSION_FILE}' not found! Please run 'python login.py' first to authenticate.")
    exit(1)

try:
    sqlite_sess = SQLiteSession("tracker_session")
    string_val = StringSession.save(sqlite_sess)
    sqlite_sess.close()
    
    with open("session_string.txt", "w", encoding="utf-8") as f:
        f.write(string_val)

    print("=" * 60)
    print("YOUR COMPACT SESSION STRING (Only ~350 characters):")
    print("=" * 60)
    print(string_val)
    print("=" * 60)
    print("Saved to: session_string.txt")
    print("Paste this value into your Koyeb / Railway 'SESSION_STRING' environment variable.")
except Exception as e:
    print(f"[ERROR] Could not extract session string: {e}")
