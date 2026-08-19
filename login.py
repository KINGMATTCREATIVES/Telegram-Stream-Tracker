import asyncio
from telethon import TelegramClient
import config

async def main():
    print("=" * 60)
    print("Telegram User Account Authentication (One-Time Setup)")
    print("=" * 60)
    print("This links your Telegram account so the tracker can monitor")
    print("group voice/video streams and fetch all participants.\n")

    client = TelegramClient("tracker_session", config.API_ID, config.API_HASH)
    await client.start()

    me = await client.get_me()
    print(f"\n[SUCCESS] Logged in as: {me.first_name} (@{me.username or 'NoUsername'})")
    print("Session saved to 'tracker_session.session'.")
    print("You can now run tracker.py and it will run autonomously!\n")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
