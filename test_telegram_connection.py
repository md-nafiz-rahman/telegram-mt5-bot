import asyncio
from telethon import TelegramClient
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE_NUMBER

async def test_telegram():
    client = TelegramClient('session_test', TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    async with client:
        print("✅ Connecting to Telegram...")
        await client.start(phone=TELEGRAM_PHONE_NUMBER)
        me = await client.get_me()
        print(f"✅ Connected as: {me.first_name}")
        print(f"✅ Phone: {me.phone}")

asyncio.run(test_telegram())
