import sys
import datetime
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
import config

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=" * 70)
print("FETCHING TODAY'S (2026-08-18) CALL & CHAT HISTORY IN @kingshubBC")
print("=" * 70)

client = TelegramClient("tracker_session", config.API_ID, config.API_HASH)
client.connect()

group = client.get_entity(config.TARGET_CHAT)
print(f"Target: {getattr(group, 'title', str(group))}\n")

# Get messages from today
msgs = client.get_messages(group, limit=100)
today_utc = datetime.datetime.now(datetime.timezone.utc).date()

today_msgs = [m for m in msgs if m.date.date() == today_utc]
print(f"Total messages from today ({today_utc}): {len(today_msgs)}")

for m in today_msgs:
    sender = getattr(m.sender, "first_name", "Unknown") if m.sender else "System"
    uname = f" (@{m.sender.username})" if (m.sender and getattr(m.sender, 'username', '')) else ""
    print(f"[{m.date.strftime('%H:%M:%S UTC')}] {sender}{uname}: {m.text if m.text else '[Media/Action]'}")
    if hasattr(m, "action") and m.action:
        print(f"   -> Action: {m.action}")

print("\n--- CHECKING DIRECT BOT MESSAGES TODAY ---")
try:
    bot = client.get_entity("KHkronosbot")
    bot_msgs = client.get_messages(bot, limit=50)
    for bm in bot_msgs:
        if bm.date.date() == today_utc:
            print(f"[{bm.date.strftime('%H:%M:%S UTC')}] Bot: {bm.text if bm.text else '[File/Media]'}")
except Exception as e:
    print(f"Bot DM error: {e}")

client.disconnect()
print("=" * 70)
