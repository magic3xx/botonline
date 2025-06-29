from telethon.sync import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import os
import requests
import time
import re

# Configuration from environment variables
api_id = int(os.getenv("API_ID", "27758818"))
api_hash = os.getenv("API_HASH", "f618d737aeaa7578fa0fa30c8c5572de")
string_session = os.getenv("STRING_SESSION", "1BJWap1wBuxELxawBlhv3tqEtQio83ucviYi9zscfhUotrp_kkusqOWcb6M8zS3RA0zeCN4V16vGZhR9fYcv6S774LvMOeEGAPjH2p0q6xPRWL90yPXmF07Y2WiGrK1bd4qb4dDK_4VW9XxH9RNtLmNUlgv_GPfo2GKOY1w8uq1Z4eVgZ-HqmckTVWy5BmcoIeqehehPvnIC61lOAhLdrFyIb-yrUiTk4HbQcsipveve4cUQyJW-yvtIlnBNVHrZj6mNCGi8DnhA1SewPifJ-AmOakjtmos-zEuwTzOtrosGI2U-HznreYtj3jxaylHdYJI7KvY7fGx_iIhtU_XzvOInCoAgioCg=")
channel_username = os.getenv("CHANNEL_USERNAME", "@PocketSignalsM1")
webhook_url = os.getenv("WEBHOOK_URL", "https://marisbriedis.app.n8n.cloud/webhook/fd2ddf25-4b6c-4d7b-9ee1-0d927fda2a41")

# Telegram bot and channel details
BOT_TOKEN = os.getenv("BOT_TOKEN", "7711621476:AAHPgGsxmviRFIRSHtZ8FlQdPdH7lbhrzuM")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002383089858"))

# Global variables
sequence = []
last_signal = None

def reformat_signal_message(original_message, is_result=False, win_type=None):
    """Reformat the message to the desired format"""
    if is_result:
        if win_type == "regular":
            return "🚨 AMO QUOTEX BOT 🚨\n✅ WIN"
        elif win_type == "win1":
            return "🚨 AMO QUOTEX BOT 🚨\n✅¹ WIN"
        elif win_type == "win2":
            return "🚨 AMO QUOTEX BOT 🚨\n✅² WIN"
        elif win_type == "loss":
            return "🚨 AMO QUOTEX BOT 🚨\n💔 LOSS"
        return None

    # Split the original message into lines
    lines = original_message.split('\n')

    # Extract the relevant lines
    keep_lines = []
    for line in lines:
        if any(prefix in line for prefix in ['💳', '🔥', '⌛', '🔽', '🔼']):
            keep_lines.append(line)

    # Construct the new message
    new_message = "🚨 AMO QUOTEX BOT 🚨\n\n"
    new_message += "@amotradingteam - join channel now! 👈\n\n"
    new_message += "\n".join(keep_lines)

    return new_message


async def send_to_telegram_channel(message):
    """Send message to Telegram channel using bot"""
    if not message or message.strip() == "":
        print("⚠️ Empty message - not sending")
        return None

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Telegram API response: {response.text}")
        return response.json()
    except Exception as e:
        print(f"❌ Error sending to Telegram channel: {str(e)}")
        return None


async def main():
    print("📡 Starting Telegram Bot...")
    print(f"📡 Listening for messages on {channel_username}...")
    
    # Initialize client
    client = TelegramClient(StringSession(string_session), api_id, api_hash)

    @client.on(events.NewMessage(chats=channel_username))
    async def handler(event):
        global sequence, last_signal

        message_text = event.message.message.strip()
        print(f"📨 Original message: {message_text}")

        # Handle WIN messages
        win_match = re.search(r"WIN\s*(✅\d*)", message_text)
        if win_match:
            sequence.append("win")
            win_type = "regular"
            if "✅¹" in message_text:
                win_type = "win1"
                print("✅¹ Detected: WIN 1")
            elif "✅²" in message_text:
                win_type = "win2"
                print("✅² Detected: WIN 2")
            else:
                print("✅ Detected: WIN")
            
            result_message = reformat_signal_message(None, True, win_type)
            await send_to_telegram_channel(result_message)
            return
            
        # Handle Loss messages
        if "✖️ Loss" in message_text:
            sequence.append("loss")
            print("✖️ Detected: Loss")
            result_message = reformat_signal_message(None, True, "loss")
            await send_to_telegram_channel(result_message)
            return
            
        # Handle DOJI messages
        if "DOJI ⚖" in message_text:
            print("⚖️ Detected: DOJI - ignoring")
            return

        # Process trading signals
        formatted_message = reformat_signal_message(message_text)
        
        if formatted_message:
            print(f"🔄 Reformatted message: {formatted_message}")
            await send_to_telegram_channel(formatted_message)
            sequence.append("call")
            last_signal = formatted_message  # Store the last signal
            print("📈 Detected: SIGNAL CALL")
        else:
            print("⚠️ Not a valid signal format - ignoring")

        # Sequence management
        if len(sequence) > 12:
            sequence.pop(0)

        if sequence == ["call", "win"] * 6:
            print("🔥 Detected 6 consecutive SIGNAL → WIN pairs. Sending webhook...")
            try:
                requests.post(webhook_url, json={"message": "6 consecutive trading wins detected on M5!"})
                print("✅ Webhook sent.")
            except Exception as e:
                print("❌ Webhook failed:", str(e))
            sequence = []

    try:
        await client.start()
        print("✅ Bot started successfully!")
        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Error starting bot: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
