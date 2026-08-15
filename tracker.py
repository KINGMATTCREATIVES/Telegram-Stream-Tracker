import os
import sys
import csv
import asyncio
import datetime
import warnings
from tabulate import tabulate
from telethon import TelegramClient, events, errors
from telethon.tl import types, functions

warnings.filterwarnings("ignore", category=DeprecationWarning)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import config
import db

API_ID = int(os.getenv("API_ID", config.API_ID))
API_HASH = os.getenv("API_HASH", config.API_HASH)
BOT_TOKEN = os.getenv("BOT_TOKEN", getattr(config, "BOT_TOKEN", ""))
TARGET_CHAT = os.getenv("TARGET_CHAT", config.TARGET_CHAT)
AUTO_POST_REPORT_TO_CHAT = bool(os.getenv("AUTO_POST_REPORT_TO_CHAT", config.AUTO_POST_REPORT_TO_CHAT))
CSV_OUTPUT_DIR = os.getenv("CSV_OUTPUT_DIR", config.CSV_OUTPUT_DIR)

os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)
db.init_db()

class CallSessionTracker:
    def __init__(self):
        self.active_stream_id = None
        self.active_call_id = None
        self.active_call_input = None
        self.chat_title = ""
        self.call_start_time = None
        self.call_end_time = None
        self.participants = {}
        self.last_csv_path = None

    def is_call_active(self):
        return self.active_call_id is not None

    def start_call(self, call_input, chat_title=""):
        call_id = getattr(call_input, "id", None)
        if self.active_call_id == call_id and self.active_call_id is not None:
            return

        now = datetime.datetime.now(datetime.timezone.utc)
        self.active_call_id = call_id
        self.active_call_input = call_input
        self.chat_title = chat_title
        self.call_start_time = now
        self.call_end_time = None
        self.active_stream_id = f"stream_{now.strftime('%Y%m%d_%H%M%S')}_{call_id}"
        self.participants = {}
        self.last_csv_path = None

        db.save_stream_start(self.active_stream_id, call_id, chat_title, now)
        print(f"\n[LIVE STREAM STARTED] Stream ID: {self.active_stream_id} at: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("Monitoring participant join/leave events...\n")

    def register_join(self, user_id: int, name: str, username: str = ""):
        if not self.is_call_active():
            return
        now = datetime.datetime.now(datetime.timezone.utc)
        if user_id not in self.participants:
            self.participants[user_id] = {
                "name": name,
                "username": username,
                "sessions": [],
                "current_join": now
            }
            uname_str = f" (@{username})" if username else ""
            print(f" [+] JOIN : {name}{uname_str} [ID: {user_id}] at {now.strftime('%H:%M:%S UTC')} (Total: {len(self.participants)})")
        else:
            if name and not name.startswith("Participant ") and not name.startswith("User "):
                self.participants[user_id]["name"] = name
            if username:
                self.participants[user_id]["username"] = username

            if self.participants[user_id]["current_join"] is None:
                self.participants[user_id]["current_join"] = now
                uname_str = f" (@{self.participants[user_id]['username']})" if self.participants[user_id]['username'] else ""
                print(f" [+] REJOIN: {self.participants[user_id]['name']}{uname_str} [ID: {user_id}] at {now.strftime('%H:%M:%S UTC')}")

        db.save_participant_join(self.active_stream_id, user_id, name, username, now)

    def register_leave(self, user_id: int):
        if not self.is_call_active():
            return
        now = datetime.datetime.now(datetime.timezone.utc)
        if user_id in self.participants and self.participants[user_id]["current_join"] is not None:
            join_time = self.participants[user_id]["current_join"]
            self.participants[user_id]["sessions"].append((join_time, now))
            self.participants[user_id]["current_join"] = None
            session_duration_sec = (now - join_time).total_seconds()
            uname_str = f" (@{self.participants[user_id]['username']})" if self.participants[user_id]['username'] else ""
            print(f" [-] LEAVE: {self.participants[user_id]['name']}{uname_str} at {now.strftime('%H:%M:%S UTC')} (Session: {session_duration_sec/60:.1f} min)")
            db.save_participant_leave(self.active_stream_id, user_id, now)

    def end_call(self):
        if not self.is_call_active():
            return
        now = datetime.datetime.now(datetime.timezone.utc)
        self.call_end_time = now

        for uid, pdata in self.participants.items():
            if pdata["current_join"] is not None:
                pdata["sessions"].append((pdata["current_join"], now))
                pdata["current_join"] = None

        print(f"\n[LIVE STREAM ENDED] Ended at: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        csv_file = self.generate_csv()
        db.save_stream_end(self.active_stream_id, now, csv_file)
        self.last_csv_path = csv_file
        self.generate_console_report()

        ended_stream_id = self.active_stream_id
        self.active_call_id = None
        self.active_call_input = None
        return ended_stream_id, csv_file

    def generate_csv(self):
        stats = self.get_current_stats()
        if not stats or not stats["participants"]:
            return ""

        filename = f"report_{stats['start_time'].strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(CSV_OUTPUT_DIR, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "User ID", "Name", "Username", "First Join (UTC)", "Last Leave (UTC)", "Session Count", "Total Duration (Minutes)", "Participation (%)"])
            for rank, p in enumerate(stats["participants"], 1):
                writer.writerow([rank, p["uid"], p["name"], p["username"], p["first_join"], p["last_leave"], p["session_count"], f"{p['total_min']:.2f}", f"{p['pct']:.2f}"])
        self.last_csv_path = filepath
        print(f"\n[CSV Exported] Successfully saved to: {os.path.abspath(filepath)}")
        return filepath

    def get_current_stats(self):
        if not self.call_start_time:
            return None

        start_time = self.call_start_time
        end_time = self.call_end_time or datetime.datetime.now(datetime.timezone.utc)
        total_call_sec = max(1.0, (end_time - start_time).total_seconds())
        total_call_min = total_call_sec / 60.0

        participant_stats = []
        for uid, pdata in self.participants.items():
            user_total_sec = sum((leave - join).total_seconds() for join, leave in pdata["sessions"])
            if pdata["current_join"] is not None:
                user_total_sec += (end_time - pdata["current_join"]).total_seconds()

            user_total_min = user_total_sec / 60.0
            pct = min(100.0, (user_total_sec / total_call_sec) * 100.0)

            first_join = pdata["sessions"][0][0].strftime("%H:%M:%S") if pdata["sessions"] else (pdata["current_join"].strftime("%H:%M:%S") if pdata["current_join"] else "N/A")
            last_leave = pdata["sessions"][-1][1].strftime("%H:%M:%S") if (pdata["sessions"] and pdata["current_join"] is None) else ("Online" if pdata["current_join"] else "N/A")

            participant_stats.append({
                "uid": uid,
                "name": pdata["name"],
                "username": pdata["username"],
                "first_join": first_join,
                "last_leave": last_leave,
                "session_count": len(pdata["sessions"]) + (1 if pdata["current_join"] else 0),
                "total_sec": user_total_sec,
                "total_min": user_total_min,
                "pct": pct,
                "is_online": pdata["current_join"] is not None
            })

        participant_stats.sort(key=lambda x: x["total_sec"], reverse=True)
        return {
            "start_time": start_time,
            "end_time": end_time,
            "is_active": self.is_call_active(),
            "total_min": total_call_min,
            "total_sec": total_call_sec,
            "participants": participant_stats
        }

    def generate_console_report(self):
        stats = self.get_current_stats()
        if not stats or not stats["participants"]:
            return

        headers = ["Rank", "Name", "Username", "First Join", "Last Leave", "Sessions", "Total Time", "Participation"]
        table_rows = []
        for rank, p in enumerate(stats["participants"], 1):
            table_rows.append([
                rank,
                p["name"][:25],
                f"@{p['username']}" if p["username"] else "-",
                p["first_join"],
                p["last_leave"],
                p["session_count"],
                f"{p['total_min']:.1f} min",
                f"{p['pct']:.1f}%"
            ])

        print("\n" + "=" * 80)
        print("  LIVE STREAM PARTICIPATION REPORT")
        print(f"  Start Time : {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  End Time   : {stats['end_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  Duration   : {stats['total_min']:.2f} minutes ({int(stats['total_sec'])} seconds)")
        print(f"  Total Users: {len(stats['participants'])}")
        print("=" * 80)
        print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))
        print("=" * 80 + "\n")

tracker = CallSessionTracker()

user_client = TelegramClient("tracker_session", API_ID, API_HASH, connection_retries=None, auto_reconnect=True)
bot_client = TelegramClient("bot_service_session", API_ID, API_HASH, connection_retries=None, auto_reconnect=True)
bot_active = False

entity_cache = {}

async def resolve_peer_info(client_instance, peer):
    pid = getattr(peer, "user_id", None) or getattr(peer, "channel_id", None) or getattr(peer, "chat_id", None)
    if not pid:
        return None, "Unknown", ""

    if pid in entity_cache:
        return pid, entity_cache[pid]["name"], entity_cache[pid]["username"]

    try:
        entity = await client_instance.get_entity(peer)
        if isinstance(entity, types.User):
            first = getattr(entity, "first_name", "") or ""
            last = getattr(entity, "last_name", "") or ""
            name = f"{first} {last}".strip() or f"User {pid}"
            username = getattr(entity, "username", "") or ""
        else:
            name = getattr(entity, "title", "") or f"Channel {pid}"
            username = getattr(entity, "username", "") or ""

        entity_cache[pid] = {"name": name, "username": username}
        return pid, name, username
    except Exception:
        return pid, f"Participant {pid}", ""

def format_report_message(stream_meta, participants, is_active=False):
    status_tag = "🔴 LIVE NOW" if is_active else "🏁 CALL FINISHED"
    start_dt = datetime.datetime.fromisoformat(stream_meta["start_time"]) if isinstance(stream_meta["start_time"], str) else stream_meta["start_time"]
    dur_min = stream_meta.get("duration_sec", 0) / 60.0 if not is_active else stream_meta.get("total_min", 0)

    msg = f"📊 **Live Stream Participation Report** ({status_tag})\n\n"
    msg += f"⏱ **Duration**: `{dur_min:.1f} mins`\n"
    msg += f"👥 **Total Participants**: `{len(participants)}`\n"
    msg += f"📅 **Started**: `{start_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n\n"
    msg += "🏆 **Participant Leaderboard**:\n"

    if not participants:
        msg += "_No participants recorded for this session._\n"
        return msg

    for rank, p in enumerate(participants[:20], 1):
        uname = f" (@{p['username']})" if p.get('username') else ""
        dot = "🟢" if p.get("is_online") else "⚪️"
        total_m = p.get("total_min", 0)
        pct_val = p.get("pct", 0)
        sess_c = p.get("session_count", 1)
        msg += f"`#{rank:02d}` {dot} **{p['name']}**{uname}\n"
        msg += f"      └ ⏳ `{total_m:.1f}m` ({pct_val:.1f}%) | 🚪 `{sess_c}` joins\n"

    if len(participants) > 20:
        msg += f"\n_...and {len(participants) - 20} more participants in CSV export._"

    return msg

async def send_auto_report(target_chat_str, csv_path):
    """Sends the post-stream report and CSV directly into Telegram."""
    try:
        stream_meta, participants = db.get_latest_stream()
        if not stream_meta or not participants:
            return

        report_text = format_report_message(stream_meta, participants, is_active=False)
        bot_target = await bot_client.get_entity(target_chat_str)
        await bot_client.send_message(bot_target, report_text, parse_mode="markdown")

        if csv_path and os.path.exists(csv_path):
            await bot_client.send_file(
                bot_target,
                csv_path,
                caption=f"📊 **Final Participation Spreadsheet**\nDuration: {stream_meta.get('duration_sec', 0)/60.0:.1f} mins | Total: {len(participants)} callers"
            )
            print(f"[Auto-Post] Successfully sent report and CSV to {target_chat_str}")
    except Exception as e:
        print(f"[Auto-Post Warning] Could not send auto-report: {e}")

# --- IN-TELEGRAM COMMAND HANDLERS ---
@bot_client.on(events.NewMessage)
async def bot_command_handler(event):
    text = event.raw_text.strip()
    if not (text.startswith("/") or text.startswith(".")):
        return

    cmd = text.split()[0].lower().replace(".", "/")
    if "@" in cmd:
        cmd = cmd.split("@")[0]

    if cmd in ["/stats", "/report", "/leaderboard"]:
        if tracker.is_call_active():
            stats = tracker.get_current_stats()
            msg = format_report_message(stats, stats["participants"], is_active=True)
            await event.reply(msg, parse_mode="markdown")
        else:
            stream_meta, participants = db.get_latest_stream()
            if stream_meta and participants:
                msg = format_report_message(stream_meta, participants, is_active=False)
                await event.reply(msg, parse_mode="markdown")
            else:
                await event.reply("⚠️ No live stream records found in database yet.", parse_mode="markdown")

    elif cmd in ["/livestatus", "/status"]:
        if tracker.is_call_active():
            stats = tracker.get_current_stats()
            online_count = sum(1 for p in stats["participants"] if p["is_online"])
            await event.reply(
                f"🔴 **Live Stream is ACTIVE**\n\n"
                f"⏱ Elapsed: `{stats['total_min']:.1f} mins`\n"
                f"👥 Currently online: `{online_count}` participants\n"
                f"📈 Total unique participants: `{len(stats['participants'])}`\n\n"
                f"Type `/stats` for the live leaderboard.",
                parse_mode="markdown"
            )
        else:
            stream_meta, participants = db.get_latest_stream()
            prev_info = f" (Last stream had {len(participants)} participants)" if participants else ""
            await event.reply(f"⚪️ No live stream is currently active{prev_info}.\nType `/stats` or `/export` to view the last report.", parse_mode="markdown")

    elif cmd in ["/export", "/csv"]:
        if tracker.is_call_active():
            csv_path = tracker.generate_csv()
            if csv_path and os.path.exists(csv_path):
                await event.reply(file=csv_path, message="📄 Here is the live in-progress participation CSV export.")
            else:
                await event.reply("⚠️ No participant data to export yet.")
        else:
            stream_meta, participants = db.get_latest_stream()
            if stream_meta and stream_meta.get("csv_path") and os.path.exists(stream_meta["csv_path"]):
                await event.reply(file=stream_meta["csv_path"], message="📄 Here is the latest completed stream CSV report.")
            elif participants:
                filename = f"report_latest.csv"
                filepath = os.path.join(CSV_OUTPUT_DIR, filename)
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Rank", "User ID", "Name", "Username", "First Join (UTC)", "Last Leave (UTC)", "Session Count", "Total Duration (Minutes)", "Participation (%)"])
                    for rank, p in enumerate(participants, 1):
                        writer.writerow([rank, p["user_id"], p["name"], p["username"], p["first_join"], p["last_leave"], p["session_count"], f"{p['total_min']:.2f}", f"{p['pct']:.2f}"])
                await event.reply(file=filepath, message="📄 Here is the latest stream CSV report.")
            else:
                await event.reply("⚠️ No stream reports found in history.", parse_mode="markdown")

    elif cmd in ["/help", "/start"]:
        help_text = (
            "🤖 **Telegram Live Stream Tracker Bot**\n\n"
            "• `/stats` or `/report` - Show latest participant leaderboard & participation %\n"
            "• `/livestatus` - Check if a live stream is active and who's online\n"
            "• `/export` or `/csv` - Download the CSV participation spreadsheet\n"
            "• `/help` - Show this menu\n\n"
            "_All stats and CSV files are permanently saved even after calls end._"
        )
        await event.reply(help_text, parse_mode="markdown")

# --- USER CLIENT LIVE CALL POLLING & EVENTS ---
@user_client.on(events.Raw)
async def raw_event_handler(event):
    if isinstance(event, types.UpdateGroupCallParticipants):
        for p in event.participants:
            peer = p.peer
            pid, name, username = await resolve_peer_info(user_client, peer)
            if not pid:
                continue

            if getattr(p, "left", False):
                tracker.register_leave(pid)
            else:
                tracker.register_join(pid, name, username)

    elif isinstance(event, types.UpdateGroupCall):
        if getattr(event.call, "duration", None) is not None:
            ended_stream_id, csv_file = tracker.end_call()
            if AUTO_POST_REPORT_TO_CHAT:
                asyncio.create_task(send_auto_report(TARGET_CHAT, csv_file))

async def background_poll_loop(target_entity):
    while True:
        try:
            full_chat = await user_client(functions.channels.GetFullChannelRequest(channel=target_entity))
            group_call = full_chat.full_chat.call

            if group_call:
                call_id = getattr(group_call, "id", None)
                if not tracker.is_call_active() or tracker.active_call_id != call_id:
                    chat_title = getattr(target_entity, "title", str(TARGET_CHAT))
                    tracker.start_call(group_call, chat_title)

                participants_res = await user_client(functions.phone.GetGroupParticipantsRequest(
                    call=group_call,
                    ids=[],
                    sources=[],
                    offset="",
                    limit=200
                ))

                active_uids = set()
                user_dict = {u.id: u for u in getattr(participants_res, "users", [])}
                chat_dict = {c.id: c for c in getattr(participants_res, "chats", [])}

                for p in participants_res.participants:
                    peer = p.peer
                    pid, name, username = await resolve_peer_info(user_client, peer)
                    if pid:
                        active_uids.add(pid)
                        if pid in user_dict:
                            u = user_dict[pid]
                            first = getattr(u, "first_name", "") or ""
                            last = getattr(u, "last_name", "") or ""
                            fname = f"{first} {last}".strip()
                            if fname:
                                name = fname
                            if getattr(u, "username", ""):
                                username = u.username
                        elif pid in chat_dict:
                            c = chat_dict[pid]
                            if getattr(c, "title", ""):
                                name = c.title
                            if getattr(c, "username", ""):
                                username = c.username

                        tracker.register_join(pid, name, username)

                for uid in list(tracker.participants.keys()):
                    if uid not in active_uids and tracker.participants[uid]["current_join"] is not None:
                        tracker.register_leave(uid)
            else:
                if tracker.is_call_active():
                    ended_stream_id, csv_file = tracker.end_call()
                    if AUTO_POST_REPORT_TO_CHAT:
                        asyncio.create_task(send_auto_report(TARGET_CHAT, csv_file))

        except Exception as e:
            print(f"[Polling Notice] {type(e).__name__}: {e}")

        await asyncio.sleep(8)

async def try_start_bot():
    global bot_active
    try:
        if not bot_client.is_connected():
            await bot_client.start(bot_token=BOT_TOKEN)
        bot_me = await bot_client.get_me()
        bot_active = True
        print(f"[UI Bot Online]  : @{bot_me.username} ({bot_me.first_name})")
    except errors.FloodWaitError as e:
        print(f"[Bot Cooldown]   : Telegram rate-limit for new bot login ({e.seconds}s). Running stream monitor via User Account in the meantime...")
        bot_active = False
        asyncio.create_task(bot_retry_after(e.seconds))
    except Exception as e:
        print(f"[Bot Notice]     : {e}. Running stream monitor via User Account...")
        bot_active = False

async def bot_retry_after(seconds):
    global bot_active
    await asyncio.sleep(seconds + 5)
    try:
        if not bot_client.is_connected():
            await bot_client.start(bot_token=BOT_TOKEN)
        bot_me = await bot_client.get_me()
        bot_active = True
        print(f"\n[UI Bot Activated] : @{bot_me.username} is now online in Telegram!")
    except Exception as e:
        print(f"[Bot Retry Notice] {e}")

async def main():
    print("=" * 60)
    print("Starting Telegram Live Stream Participant Tracker (Dual Engine)...")
    print("=" * 60)

    print("[Stream Monitor] : Connecting User Account to monitor voice/video streams...")
    if not user_client.is_connected():
        await user_client.connect()
        if not await user_client.is_user_authorized():
            await user_client.start()
    user_me = await user_client.get_me()
    print(f"[Stream Monitor] : Connected as {user_me.first_name} (@{user_me.username or 'NoUsername'})")

    await try_start_bot()

    print(f"\nResolving target chat '{TARGET_CHAT}'...")
    target_entity = await user_client.get_entity(TARGET_CHAT)
    title = getattr(target_entity, "title", str(TARGET_CHAT))
    print(f"[OK] Successfully linked to: {title}")

    print("\n[READY] Participant tracking active for live calls & streams!")
    print("  Auto-generates attendance CSV reports on stream end.")
    print("  Permanently persists all sessions to SQLite database.\n")

    tasks = [
        user_client.run_until_disconnected(),
        background_poll_loop(target_entity)
    ]
    if bot_active:
        tasks.append(bot_client.run_until_disconnected())

    try:
        await asyncio.gather(*tasks)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        print(f"[Notice] Client connection dropped: {e}")
    finally:
        try:
            if user_client.is_connected():
                await user_client.disconnect()
        except Exception:
            pass
        try:
            if bot_client.is_connected():
                await bot_client.disconnect()
        except Exception:
            pass

async def supervisor():
    while True:
        try:
            await main()
        except (KeyboardInterrupt, SystemExit):
            print("\nTracker stopped by user.")
            if tracker.is_call_active():
                tracker.end_call()
            break
        except Exception as e:
            print(f"[Auto-Recover] Connection interrupted: {e}. Reconnecting in 10s...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(supervisor())
    except (KeyboardInterrupt, SystemExit):
        pass
