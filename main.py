from telethon.sync import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import os
import requests
import time
import re

# Debug environment variables
print("🔍 Debugging environment variables...")
print(f"API_ID: {'SET' if os.getenv('API_ID') else 'NOT SET'}")
print(f"API_HASH: {'SET' if os.getenv('API_HASH') else 'NOT SET'}")
print(f"STRING_SESSION: {'SET' if os.getenv('STRING_SESSION') else 'NOT SET'}")
print(f"BOT_TOKEN: {'SET' if os.getenv('BOT_TOKEN') else 'NOT SET'}")
print(f"CHANNEL_ID: {'SET' if os.getenv('CHANNEL_ID') else 'NOT SET'}")

# Configuration from environment variables
api_id = int(os.getenv("API_ID", "27758818"))
api_hash = os.getenv("API_HASH", "f618d737aeaa7578fa0fa30c8c5572de")
string_session = os.getenv("STRING_SESSION", "").strip()  # Strip whitespace
channel_username = os.getenv("CHANNEL_USERNAME", "@PocketSignalsM1")
webhook_url = os.getenv("WEBHOOK_URL", "https://marisbriedis.app.n8n.cloud/webhook/fd2ddf25-4b6c-4d7b-9ee1-0d927fda2a41")

# Telegram bot and channel details
BOT_TOKEN = os.getenv("BOT_TOKEN", "7711621476:AAHPgGsxmviRFIRSHtZ8FlQdPdH7lbhrzuM")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002383089858"))

# Clean and validate session string
if string_session:
    # Remove any leading/trailing whitespace and common prefixes that might be added
    string_session = string_session.strip()
    if string_session.startswith('='):
        string_session = string_session[1:]  # Remove leading =
    string_session = string_session.strip()  # Strip again after removing =

# Debug the actual values (safely)
print(f"🔍 STRING_SESSION length: {len(string_session) if string_session else 0}")
print(f"🔍 STRING_SESSION starts with: {string_session[:10] if string_session else 'EMPTY'}...")
print(f"🔍 STRING_SESSION ends with: ...{string_session[-10:] if string_session and len(string_session) > 10 else 'EMPTY'}")

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


def is_valid_session_string(session_str):
    """Validate if the session string looks correct"""
    if not session_str or len(session_str) < 100:
        return False
    
    # Session strings are typically base64-like and quite long
    # They should not contain spaces or special characters except + / =
    import string
    allowed_chars = string.ascii_letters + string.digits + '+/='
    return all(c in allowed_chars for c in session_str)


async def main():
    print("📡 Starting Telegram Bot...")
    print(f"📡 Listening for messages on {channel_username}...")
    
    # Initialize client - use session string if available and valid
    client = None
    
    if string_session and is_valid_session_string(string_session):
        print("🔐 Using string session...")
        try:
            client = TelegramClient(StringSession(string_session), api_id, api_hash)
            # Test the session by trying to connect
            await client.connect()
            if not await client.is_user_authorized():
                print("❌ Session string is not authorized")
                client = None
            else:
                print("✅ String session is valid and authorized!")
        except Exception as e:
            print(f"❌ Error with string session: {str(e)}")
            client = None
    
    # If string session failed, try to create a new session
    if client is None:
        print("📁 Creating new session...")
        print("⚠️ This will require manual authentication which won't work in Railway.")
        print("💡 Please generate a valid session string locally and set it in Railway environment variables.")
        
        # For Railway deployment, we can't do interactive authentication
        # The bot will exit here and you need to set a proper session string
        print("❌ Cannot proceed without valid session string in Railway environment.")
        print("🔧 Please:")
        print("1. Run generate_session.py locally to get a valid session string")
        print("2. Set the STRING_SESSION environment variable in Railway")
        print("3. Redeploy the application")
        return

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
