# bot.py

from telethon.sync import TelegramClient, events
from telethon.sessions import StringSession
import os
import requests
import re

# --- Configuration from Environment Variables ---
# Make sure to set these in your hosting environment (e.g., Render)
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@PocketSignalsM1")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# --- Basic Validation ---
if not all([API_ID, API_HASH, STRING_SESSION, BOT_TOKEN, CHANNEL_ID, WEBHOOK_URL]):
    raise ValueError("One or more essential environment variables are not set. Please check your configuration.")

# Convert string values from env to the correct type
API_ID = int(API_ID)
CHANNEL_ID = int(CHANNEL_ID)


# --- Bot Logic (no changes needed here) ---

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
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
    
    lines = original_message.split('\n')
    keep_lines = []
    for line in lines:
        if any(prefix in line for prefix in ['💳', '🔥', '⌛', '🔽', '🔼']):
            keep_lines.append(line)
    
    if not keep_lines:
        return None # Not a valid signal if no relevant lines are found

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
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram API response: {response.status_code} - {response.text}")
        return response.json()
    except Exception as e:
        print(f"❌ Error sending to Telegram channel: {str(e)}")
        return None

async def main():
    print("📡 Listening for messages...")

    @client.on(events.NewMessage(chats=CHANNEL_USERNAME))
    async def handler(event):
        global sequence, last_signal
        message_text = event.message.message.strip()
        print(f"📨 Original message received: '{message_text[:50]}...'")

        if "WIN" in message_text and any(s in message_text for s in ["✅", "✅¹", "✅²"]):
            sequence.append("win")
            win_type = "regular"
            if "✅¹" in message_text: win_type = "win1"
            elif "✅²" in message_text: win_type = "win2"
            print(f"✅ Detected: {win_type.upper()}")
            result_message = reformat_signal_message(None, is_result=True, win_type=win_type)
            await send_to_telegram_channel(result_message)
            return
            
        if "✖️ Loss" in message_text:
            sequence.append("loss")
            print("✖️ Detected: Loss")
            result_message = reformat_signal_message(None, is_result=True, win_type="loss")
            await send_to_telegram_channel(result_message)
            return
            
        if "DOJI ⚖" in message_text:
            print("⚖️ Detected: DOJI - ignoring")
            return

        formatted_message = reformat_signal_message(message_text)
        
        if formatted_message:
            print(f"🔄 Reformatted message: {formatted_message}")
            await send_to_telegram_channel(formatted_message)
            sequence.append("call")
            last_signal = formatted_message
            print("📈 Detected: SIGNAL CALL")
        else:
            print("⚠️ Not a valid signal format - ignoring")

        if len(sequence) > 12:
            sequence.pop(0)

        if sequence == ["call", "win"] * 6:
            print("🔥 Detected 6 consecutive SIGNAL → WIN pairs. Sending webhook...")
            try:
                requests.post(webhook_url, json={"message": "6 consecutive trading wins detected!"}, timeout=10)
                print("✅ Webhook sent.")
            except Exception as e:
                print(f"❌ Webhook failed: {str(e)}")
            sequence = []

    await client.start()
    print("🚀 Client started. Bot is now live and listening!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
