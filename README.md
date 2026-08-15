# Telegram Live Stream Participant Tracker

Track participant join/leave events, total durations, and participation percentages during Telegram group voice and video streams.

---

## 🚀 Quick Setup Guide

### 1. Set Your Telegram API Credentials
1. Log into [**my.telegram.org**](https://my.telegram.org) with your Telegram phone number.
2. Go to **API development tools** and create a new application.
3. Open `config.py` in this folder:
   - Paste your **`API_ID`**
   - Paste your **`API_HASH`**
   - Set **`TARGET_CHAT`** to your channel or group's `@username` (or private chat ID).

---

### 2. Run the Tracker
From this folder, run:

```bash
uv run python tracker.py
```
*(Or use `.venv\Scripts\python.exe tracker.py`)*

- On the first run, Telethon will ask for your phone number and the Telegram login code to create a session.
- Once connected, it will wait for any live voice/video stream to start.

---

### 3. What Happens During a Live Stream
- **Join / Rejoin**: Whenever a user joins or rejoins, their timestamp is recorded.
- **Drop-off / Leave**: When a user leaves, their session duration is logged.
- **Call Ended**: When the stream finishes, the script automatically:
  1. Computes each user's total time on the call.
  2. Calculates their participation percentage: `(Total User Time / Call Duration) * 100%`.
  3. Displays a formatted leaderboard in the terminal.
  4. Exports a detailed CSV report to the `reports/` folder.
