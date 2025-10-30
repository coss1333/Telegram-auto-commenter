from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os

api_id = int(os.getenv("API_ID") or input("Enter API_ID: ").strip())
api_hash = os.getenv("API_HASH") or input("Enter API_HASH: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("Your SESSION_STRING:\n")
    print(client.session.save())
    print("\nSave this in your .env as SESSION_STRING. Keep it secret!")
