import os
import base64
from telethon.sessions import StringSession, SQLiteSession

SESSION_FILE = "tracker_session.session"

if not os.path.exists(SESSION_FILE):
    print(f"[ERROR] '{SESSION_FILE}' not found! Please run 'python login.py' first to authenticate.")
    exit(1)

try:
    with open(SESSION_FILE, "rb") as f:
        b64_val = base64.b64encode(f.read()).decode("utf-8")
    
    with open("session_b64.txt", "w", encoding="utf-8") as f:
        f.write(b64_val)

    try:
        sqlite_sess = SQLiteSession("tracker_session")
        string_val = StringSession.save(sqlite_sess)
        sqlite_sess.close()
        with open("session_string.txt", "w", encoding="utf-8") as f:
            f.write(string_val)
    except Exception:
        string_val = ""

    print("=" * 60)
    print("SESSION EXPORT SUCCESSFUL")
    print("=" * 60)
    print("1. SESSION_B64 (Saved to session_b64.txt)")
    print("2. SESSION_STRING (Saved to session_string.txt)")
    print("=" * 60)
    print("Paste SESSION_B64 or SESSION_STRING into your Railway Environment Variables.")
except Exception as e:
    print(f"[ERROR] Could not export session: {e}")
