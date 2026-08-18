import os
import sys
import datetime
from telethon.sync import TelegramClient
import config

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=" * 70)
print("FETCHING TODAY'S (2026-08-18) LIVE STREAM REPORTS FROM TELEGRAM")
print("=" * 70)

client = TelegramClient("tracker_session", config.API_ID, config.API_HASH)
client.connect()

group = client.get_entity(config.TARGET_CHAT)
print(f"Target Chat: {getattr(group, 'title', str(group))}\n")

# Fetch recent messages from today
messages = client.get_messages(group, limit=60)
today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
print(f"Today's date (UTC): {today_str}\n")

found_reports = []
csv_files_downloaded = []

for m in messages:
    m_date_str = m.date.strftime("%Y-%m-%d %H:%M:%S UTC")
    sender_name = getattr(m.sender, "first_name", "Unknown") if m.sender else "System"
    
    # Check if message is a report or CSV from today
    is_report = False
    if m.text and ("Participation Report" in m.text or "Leaderboard" in m.text or "Live Stream" in m.text or "CALL FINISHED" in m.text):
        is_report = True
        print(f"[{m_date_str}] Report Message from {sender_name}:")
        print(m.text)
        print("-" * 50)
        found_reports.append(m)

    # Check if message has a CSV file
    if m.file and hasattr(m.file, "name") and m.file.name and m.file.name.endswith(".csv"):
        print(f"[{m_date_str}] CSV File found: {m.file.name} (Size: {m.file.size} bytes)")
        dest = os.path.join("reports", m.file.name)
        client.download_media(m, dest)
        csv_files_downloaded.append(dest)
        print(f"-> Downloaded to: {dest}")

# Also check private messages from the bot (@KHkronosbot)
try:
    bot_entity = client.get_entity("KHkronosbot")
    print(f"\nChecking direct messages from @KHkronosbot...")
    bot_msgs = client.get_messages(bot_entity, limit=20)
    for bm in bot_msgs:
        if bm.file and hasattr(bm.file, "name") and bm.file.name and bm.file.name.endswith(".csv"):
            dest = os.path.join("reports", f"bot_{bm.file.name}")
            client.download_media(bm, dest)
            csv_files_downloaded.append(dest)
            print(f"-> Downloaded CSV from Bot DM: {dest}")
        elif bm.text and ("Participation Report" in bm.text or "Leaderboard" in bm.text):
            print(f"[{bm.date}] Bot DM Report:\n{bm.text}\n{'-'*50}")
except Exception as e:
    print(f"Notice checking bot DMs: {e}")

client.disconnect()
print("=" * 70)
