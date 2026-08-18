import os
import sys
import csv
from telethon.sync import TelegramClient
import config

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=" * 70)
print("DOWNLOADING & ANALYZING TODAY'S (2026-08-18) SPREADSHEET")
print("=" * 70)

client = TelegramClient("tracker_session", config.API_ID, config.API_HASH)
client.connect()

group = client.get_entity(config.TARGET_CHAT)

# Find the CSV message from this morning
msgs = client.get_messages(group, limit=20)
today_csv_file = None

for m in msgs:
    if m.file and hasattr(m.file, "name") and m.file.name and m.file.name.endswith(".csv"):
        print(f"Found CSV message from {m.date}: {m.file.name}")
        local_path = os.path.join("reports", f"today_{m.file.name}")
        client.download_media(m, local_path)
        today_csv_file = local_path
        print(f"Downloaded to: {local_path}")
        break

client.disconnect()

if today_csv_file and os.path.exists(today_csv_file):
    print("\n--- PARSING ALL PARTICIPANTS IN TODAY'S SPREADSHEET ---")
    with open(today_csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = list(csv.DictReader(f))
        print(f"Total Rows in Spreadsheet: {len(reader)}\n")
        
        # Search for danigo / 6765772652 / daniel / aina
        target_uid = "6765772652"
        found = False
        
        for row in reader:
            uid = str(row.get("User ID", ""))
            uname = str(row.get("Username", "")).lower()
            name = str(row.get("Name", "")).lower()
            
            if uid == target_uid or "danigo" in uname or "daniel" in name or "aina" in name:
                found = True
                print("*" * 60)
                print("🎯 MATCH FOUND FOR TARGET USER:")
                for k, v in row.items():
                    print(f"   {k:25}: {v}")
                print("*" * 60)

        if not found:
            print(f"❌ User ID {target_uid} (@danigodhfo / Daniel Aina) is NOT in today's 46 participants.\n")

        print("\n--- ALL 46 PARTICIPANTS FROM TODAY'S CALL ---")
        for r in reader:
            print(f"#{r.get('Rank', '?'):>2} | ID: {r.get('User ID', ''):<10} | {r.get('Name', ''):<25} | @{r.get('Username', ''):<18} | {r.get('Total Duration (Minutes)', ''):>5}m ({r.get('Participation (%)', ''):>5}%) | Joins: {r.get('Session Count', '')}")

print("=" * 70)
