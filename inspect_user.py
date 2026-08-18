import sqlite3
import glob
import csv
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=" * 70)
print("COMPREHENSIVE INVESTIGATION FOR: @danigodhfo / Daniel Aina")
print("=" * 70)

# 1. Search in Telegram Session Entity Cache
print("\n--- 1. TELEGRAM SESSION ENTITY DATABASE (tracker_session.session) ---")
try:
    conn_sess = sqlite3.connect("tracker_session.session")
    c_sess = conn_sess.cursor()
    entities = c_sess.execute("""
    SELECT id, username, name, phone FROM entities 
    WHERE LOWER(username) LIKE '%danigodhfo%' 
       OR LOWER(username) LIKE '%danigo%' 
       OR LOWER(name) LIKE '%daniel%' 
       OR LOWER(name) LIKE '%aina%'
    """).fetchall()
    if entities:
        for e in entities:
            print(f"-> FOUND TELEGRAM USER IN SESSION CACHE:")
            print(f"   Telegram User ID : {e[0]}")
            print(f"   Username         : @{e[1]}")
            print(f"   Full Name        : {e[2]}")
            print(f"   Phone            : {e[3]}")
    else:
        print("No matching entity found in session cache.")
    conn_sess.close()
except Exception as err:
    print(f"Session DB error: {err}")

# 2. Search in tracker.db
print("\n--- 2. STREAM TRACKER DATABASE (tracker.db) ---")
try:
    conn_trk = sqlite3.connect("tracker.db")
    c_trk = conn_trk.cursor()
    
    # Check all participants
    p_rows = c_trk.execute("""
    SELECT stream_id, user_id, name, username, first_join, last_leave, session_count, total_min, pct, is_online 
    FROM participants 
    WHERE LOWER(username) LIKE '%danigodhfo%' 
       OR LOWER(username) LIKE '%danigo%' 
       OR LOWER(name) LIKE '%daniel%' 
       OR LOWER(name) LIKE '%aina%'
    """).fetchall()
    
    if p_rows:
        for p in p_rows:
            print(f"-> STREAM ATTENDANCE RECORD:")
            print(f"   Stream ID       : {p[0]}")
            print(f"   User ID         : {p[1]}")
            print(f"   Name            : {p[2]}")
            print(f"   Username        : @{p[3]}")
            print(f"   First Join      : {p[4]}")
            print(f"   Last Leave      : {p[5]}")
            print(f"   Session Count   : {p[6]}")
            print(f"   Duration        : {p[7]:.2f} mins")
            print(f"   Participation % : {p[8]:.2f}%")
    else:
        print("No participation record found in local tracker.db for @danigodhfo.")

    conn_trk.close()
except Exception as err:
    print(f"Tracker DB error: {err}")

# 3. Search in CSV Reports
print("\n--- 3. CSV ATTENDANCE REPORTS (reports/*.csv) ---")
csv_files = glob.glob("reports/*.csv")
for fpath in csv_files:
    print(f"Searching {fpath}...")
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        found = False
        for row in reader:
            u = (row.get("Username") or "").lower()
            n = (row.get("Name") or "").lower()
            if "danigodhfo" in u or "danigo" in u or "daniel" in n or "aina" in n:
                print(f"-> MATCH IN CSV:")
                for k, v in row.items():
                    print(f"   {k}: {v}")
                found = True
        if not found:
            print("   No match in this CSV.")

print("\n" + "=" * 70)
