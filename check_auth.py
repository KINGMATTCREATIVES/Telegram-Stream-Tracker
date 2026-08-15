from telethon.sync import TelegramClient
import config

client = TelegramClient('tracker_session', config.API_ID, config.API_HASH)
client.connect()
print("IS_AUTHORIZED:", client.is_user_authorized())
client.disconnect()
