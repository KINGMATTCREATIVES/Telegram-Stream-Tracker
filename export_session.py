import base64
import os

SESSION_FILE = "tracker_session.session"

if not os.path.exists(SESSION_FILE):
    print(f"[ERROR] '{SESSION_FILE}' not found! Please run 'python login.py' first to authenticate.")
    exit(1)

with open(SESSION_FILE, "rb") as f:
    b64_str = base64.b64encode(f.read()).decode("utf-8")

print("=" * 60)
print("YOUR BASE64 SESSION ENCODING (Copy the line below):")
print("=" * 60)
print(b64_str)
print("=" * 60)
print("Paste this value into your Koyeb / Cloud 'SESSION_B64' environment variable.")
