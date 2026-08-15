import re
import sys
import datetime
import csv
from tabulate import tabulate

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

raw_text = """
[LIVE STREAM STARTED] Call ID: -5734923756965228090 at: 2026-08-14 20:12:00 UTC
Monitoring participant join/leave events...

 [+] JOIN : Matthew Ọbańlá (@KingmattMO) [ID: 1067204907] at 20:12:00 UTC (Total: 1)
 [+] JOIN : Esther Olajide (@toluwa_nisola) [ID: 1187478939] at 20:12:00 UTC (Total: 2)
 [+] JOIN : Sis Damilola Oladipupo [ID: 1633978817] at 20:12:01 UTC (Total: 3)
 [+] JOIN : Bro Arthur Ogodo [ID: 1568346316] at 20:12:01 UTC (Total: 4)
 [+] JOIN : Adekunle Philip KH (@philipecclesia) [ID: 5021886681] at 20:12:01 UTC (Total: 5)
 [+] JOIN : Bro dare (@Daiveedladray) [ID: 6154808428] at 20:12:01 UTC (Total: 6)
 [+] JOIN : Titilayo Rosiji (@titilee82) [ID: 1623337363] at 20:12:01 UTC (Total: 7)
 [+] JOIN : Bro Isaac Oladipupo (@Olaking1) [ID: 1055188344] at 20:12:01 UTC (Total: 8)
 [+] JOIN : Sis Esther Olusola [ID: 1198580304] at 20:12:01 UTC (Total: 9)
 [+] JOIN : Sis Chinwendu KH [ID: 5736853479] at 20:12:01 UTC (Total: 10)
 [+] JOIN : Sis Adejoke Kings Hub [ID: 1768740489] at 20:12:02 UTC (Total: 11)
 [+] JOIN : Bro Daniel Emblem [ID: 8452374462] at 20:12:02 UTC (Total: 12)
 [+] JOIN : Sis Joy Igele [ID: 5842104960] at 20:12:02 UTC (Total: 13)
 [+] JOIN : Sis BEKKY KINGS HUB (@beckyz_Artistry) [ID: 6169690410] at 20:12:02 UTC (Total: 14)
 [+] JOIN : Modupe Lawal (@Oluwaseun_modupe) [ID: 1902811470] at 20:12:02 UTC (Total: 15)
 [+] JOIN : Sis Bright KH (@Bright633) [ID: 2050735724] at 20:12:02 UTC (Total: 16)
 [+] JOIN : Favour [ID: 8579726991] at 20:12:02 UTC (Total: 17)
 [+] JOIN : Sister Titilayo Oladipupo (@Teelahyor5) [ID: 5450495252] at 20:12:02 UTC (Total: 18)
 [+] JOIN : Sis Adeola Adeoye [ID: 1733858222] at 20:12:03 UTC (Total: 19)
 [+] JOIN : Sis Blessing Kings Hub (@Blessingore) [ID: 6374190576] at 20:12:03 UTC (Total: 20)
 [+] JOIN : Oshilaja Titilayo KH [ID: 5330295657] at 20:12:08 UTC (Total: 21)
 [-] LEAVE: Oshilaja Titilayo KH at 20:12:11 UTC (Session: 0.0 min)
 [+] REJOIN: Oshilaja Titilayo KH [ID: 5330295657] at 20:12:12 UTC
 [-] LEAVE: Oshilaja Titilayo KH at 20:12:20 UTC (Session: 0.1 min)
 [+] JOIN : Dotun Collins [ID: 1192562832] at 20:12:23 UTC (Total: 22)
 [-] LEAVE: Sis Blessing Kings Hub (@Blessingore) at 20:12:28 UTC (Session: 0.4 min)
 [-] LEAVE: Sis Joy Igele at 20:12:29 UTC (Session: 0.5 min)
 [+] REJOIN: Sis Blessing Kings Hub (@Blessingore) [ID: 6374190576] at 20:12:37 UTC
 [+] REJOIN: Sis Joy Igele [ID: 5842104960] at 20:12:57 UTC
 [+] JOIN : Akanbi Folakemi [ID: 7373745365] at 20:13:00 UTC (Total: 23)
 [+] JOIN : Leye Rosiji (@OlaleyeR) [ID: 549053856] at 20:13:01 UTC (Total: 24)
 [-] LEAVE: Sis Joy Igele at 20:13:02 UTC (Session: 0.1 min)
 [-] LEAVE: Sis Blessing Kings Hub (@Blessingore) at 20:13:02 UTC (Session: 0.4 min)
 [-] LEAVE: Akanbi Folakemi at 20:13:02 UTC (Session: 0.0 min)
 [+] REJOIN: Sis Joy Igele [ID: 5842104960] at 20:13:05 UTC
 [-] LEAVE: Sis Joy Igele at 20:13:10 UTC (Session: 0.1 min)
 [+] JOIN : Damilola Kingshub (@Mo_rireoluwa) [ID: 5198092341] at 20:13:19 UTC (Total: 25)
 [+] JOIN : TALKINGWILLY (@talkingwilly) [ID: 2020680914] at 20:13:35 UTC (Total: 26)
 [-] LEAVE: TALKINGWILLY (@talkingwilly) at 20:13:40 UTC (Session: 0.1 min)
 [+] JOIN : Sia Funke KH (@Beezalel) [ID: 1070491258] at 20:13:57 UTC (Total: 27)
 [+] JOIN : Bro Bukunmi KH (@adebarigold) [ID: 1074618195] at 20:13:57 UTC (Total: 28)
 [-] LEAVE: Sia Funke KH (@Beezalel) at 20:14:05 UTC (Session: 0.1 min)
 [-] LEAVE: Bro Bukunmi KH (@adebarigold) at 20:14:05 UTC (Session: 0.1 min)
 [-] LEAVE: Sis BEKKY KINGS HUB (@beckyz_Artistry) at 20:14:21 UTC (Session: 0.8 min)
 [+] REJOIN: Sis BEKKY KINGS HUB (@beckyz_Artistry) [ID: 6169690410] at 20:14:24 UTC
 [-] LEAVE: Sis BEKKY KINGS HUB (@beckyz_Artistry) at 20:14:24 UTC (Session: 0.0 min)
 [+] REJOIN: Sis BEKKY KINGS HUB (@beckyz_Artistry) [ID: 6169690410] at 20:14:24 UTC
 [+] JOIN : Emmanuel [ID: 655988041] at 20:14:28 UTC (Total: 29)
 [+] JOIN : Sis Blessing Kings Hub (@Blessingore) [ID: 6374190576] at 20:14:30 UTC (Total: 30)
 [-] LEAVE: Sis BEKKY KINGS HUB (@beckyz_Artistry) at 20:14:30 UTC (Session: 0.1 min)
 [-] LEAVE: Emmanuel at 20:14:30 UTC (Session: 0.0 min)
 [+] REJOIN: Oshilaja Titilayo KH [ID: 5330295657] at 20:14:42 UTC
"""

stream_start = datetime.datetime.strptime("2026-08-14 20:12:00", "%Y-%m-%d %H:%M:%S")
stream_end = datetime.datetime.strptime("2026-08-14 20:20:00", "%Y-%m-%d %H:%M:%S")

users = {}

for line in raw_text.splitlines():
    line = line.strip()
    if not line:
        continue

    # JOIN or REJOIN
    if "[+] JOIN" in line or "[+] REJOIN" in line:
        # Match: [+] JOIN : Name (@Username) [ID: 123] at 20:12:00 UTC
        # or: [+] JOIN : Name [ID: 123] at 20:12:00 UTC
        m_uid = re.search(r'\[ID:\s*(\d+)\]', line)
        m_time = re.search(r'at\s*(\d{2}:\d{2}:\d{2})\s*UTC', line)
        m_uname = re.search(r'\(@([^\)]+)\)', line)
        m_name = re.search(r':\s*(.*?)(?:\s*\(@|\s*\[ID)', line)

        if m_uid and m_time:
            uid = int(m_uid.group(1))
            t_str = m_time.group(1)
            t_dt = datetime.datetime.strptime(f"2026-08-14 {t_str}", "%Y-%m-%d %H:%M:%S")
            uname = m_uname.group(1) if m_uname else ""
            name = m_name.group(1).strip() if m_name else f"User {uid}"

            if uid not in users:
                users[uid] = {
                    "name": name,
                    "username": uname,
                    "sessions": [],
                    "current_join": t_dt,
                    "first_join": t_dt
                }
            else:
                if uname:
                    users[uid]["username"] = uname
                if name and not name.startswith("User "):
                    users[uid]["name"] = name
                if users[uid]["current_join"] is None:
                    users[uid]["current_join"] = t_dt

    elif "[-] LEAVE" in line:
        # Match: [-] LEAVE: Name (@Username) at 20:12:11 UTC
        # or: [-] LEAVE: Name at 20:12:11 UTC
        m_time = re.search(r'at\s*(\d{2}:\d{2}:\d{2})\s*UTC', line)
        m_uname = re.search(r'\(@([^\)]+)\)', line)
        m_name = re.search(r'LEAVE:\s*(.*?)(?:\s*\(@|\s*at\s*\d{2}:)', line)

        if m_time:
            t_str = m_time.group(1)
            t_dt = datetime.datetime.strptime(f"2026-08-14 {t_str}", "%Y-%m-%d %H:%M:%S")
            uname = m_uname.group(1) if m_uname else ""
            name = m_name.group(1).strip() if m_name else ""

            matched_uid = None
            for u_id, u_data in users.items():
                if (uname and u_data["username"] == uname) or (name and u_data["name"] == name):
                    matched_uid = u_id
                    break

            if matched_uid and users[matched_uid]["current_join"] is not None:
                join_t = users[matched_uid]["current_join"]
                users[matched_uid]["sessions"].append((join_t, t_dt))
                users[matched_uid]["current_join"] = None

# Close any still-open sessions at stream_end
for uid, udata in users.items():
    if udata["current_join"] is not None:
        users[uid]["sessions"].append((udata["current_join"], stream_end))
        users[uid]["current_join"] = None

total_call_sec = (stream_end - stream_start).total_seconds()
total_call_min = total_call_sec / 60.0

results = []
for uid, udata in users.items():
    tot_sec = sum((l - j).total_seconds() for j, l in udata["sessions"])
    tot_min = tot_sec / 60.0
    pct = min(100.0, (tot_sec / total_call_sec) * 100.0)
    first_j = udata["first_join"].strftime("%H:%M:%S")
    last_l = udata["sessions"][-1][1].strftime("%H:%M:%S") if udata["sessions"] else "N/A"

    results.append({
        "uid": uid,
        "name": udata["name"],
        "username": udata["username"],
        "first_join": first_j,
        "last_leave": last_l,
        "sessions": len(udata["sessions"]),
        "total_min": tot_min,
        "pct": pct,
        "_sec": tot_sec
    })

results.sort(key=lambda x: x["_sec"], reverse=True)

print(f"Total Unique Participants: {len(results)}")
print(f"Call Duration: {total_call_min:.1f} minutes ({int(total_call_sec)} seconds)\n")

table = []
for rank, r in enumerate(results, 1):
    table.append([
        rank,
        r["name"][:25],
        f"@{r['username']}" if r["username"] else "-",
        r["first_join"],
        r["last_leave"],
        r["sessions"],
        f"{r['total_min']:.1f} min",
        f"{r['pct']:.1f}%"
    ])

print(tabulate(table, headers=["Rank", "Name", "Username", "First Join", "Last Leave", "Sessions", "Total Time", "Participation %"], tablefmt="fancy_grid"))

with open("reports/livestream_attendance_report.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Rank", "User ID", "Name", "Username", "First Join (UTC)", "Last Leave (UTC)", "Session Count", "Total Duration (Minutes)", "Participation (%)"])
    for rank, r in enumerate(results, 1):
        writer.writerow([rank, r["uid"], r["name"], r["username"], r["first_join"], r["last_leave"], r["sessions"], f"{r['total_min']:.2f}", f"{r['pct']:.2f}"])

print("\n[OK] Generated reports/livestream_attendance_report.csv successfully!")
