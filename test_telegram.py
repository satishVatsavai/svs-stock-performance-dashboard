"""
Test script to verify Telegram notification setup
Sends a single test message without scheduling
"""

import os
from dotenv import load_dotenv
from telegram import Bot
import asyncio

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


async def send_test_message():
    """Send a test message to Telegram"""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        test_message = """
🧪 *Test Message*

✅ Your Telegram bot is configured correctly!

This is a test message to verify that:
• Your bot token is valid
• Your chat ID is correct
• The bot can send messages

If you're seeing this, the setup is successful! 🎉

You can now run `python telegram_notifier.py` to start the scheduler.
"""
        
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=test_message,
            parse_mode='Markdown'
        )
        print("✅ Test message sent successfully!")
        print("Check your Telegram to verify you received it.")
        return True
        
    except Exception as e:
        print(f"❌ Error sending test message: {str(e)}")
        return False


def validate_config():
    """Validate configuration"""
    print("🔍 Validating configuration...")
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'your_bot_token_here':
        print("❌ TELEGRAM_BOT_TOKEN not configured!")
        print("Please set TELEGRAM_BOT_TOKEN in .env file")
        return False
    else:
        print(f"✅ Bot token found: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == 'your_chat_id_here':
        print("❌ TELEGRAM_CHAT_ID not configured!")
        print("Please set TELEGRAM_CHAT_ID in .env file")
        return False
    else:
        print(f"✅ Chat ID found: {TELEGRAM_CHAT_ID}")
    
    return True


def main():
    """Main test function"""
    print("🧪 Telegram Configuration Test")
    print("=" * 50)
    print()
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file (copy from .env.example)")
        print("See TELEGRAM_SETUP.md for instructions")
        return
    
    # Validate configuration
    if not validate_config():
        print("\n📚 See TELEGRAM_SETUP.md for setup instructions")
        return
    
    print("\n📤 Sending test message...")
    success = asyncio.run(send_test_message())
    
    if success:
        print("\n🎉 Configuration test successful!")
        print("Next steps:")
        print("1. Check your Telegram app for the test message")
        print("2. Run 'python telegram_notifier.py' to start the scheduler")
        print("   OR")
        print("3. Run './start_notifier.sh' for automated startup")
    else:
        print("\n❌ Configuration test failed!")
        print("Please check your bot token and chat ID")
        print("See TELEGRAM_SETUP.md for troubleshooting")


if __name__ == "__main__":
    main()
