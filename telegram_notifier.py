"""
Telegram Notification Scheduler
Sends portfolio summary to Telegram at scheduled times (3 times a day)
Also sends daily alerts for stocks with P/L between 5% and 10% at 3:00 PM
"""

import os
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
import asyncio
from portfolio_calculator import calculate_portfolio_summary, calculate_detailed_portfolio, format_summary_message

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Get notification times from environment (default to 9 AM, 2 PM, 6 PM)
NOTIFICATION_TIME_1 = os.getenv('NOTIFICATION_TIME_1', '09:00')
NOTIFICATION_TIME_2 = os.getenv('NOTIFICATION_TIME_2', '14:00')
NOTIFICATION_TIME_3 = os.getenv('NOTIFICATION_TIME_3', '18:00')

# Special notification time for P/L alerts (3:00 PM)
PL_ALERT_TIME = os.getenv('PL_ALERT_TIME', '15:00')


async def send_telegram_message(message):
    """Send message to Telegram using async"""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        print(f"✅ Message sent to Telegram at {datetime.now()}")
        return True
    except Exception as e:
        print(f"❌ Error sending Telegram message: {str(e)}")
        return False


def send_portfolio_update():
    """Calculate portfolio summary and send to Telegram"""
    print(f"🔄 Calculating portfolio summary at {datetime.now()}...")
    
    try:
        # Calculate summary
        summary = calculate_portfolio_summary()
        
        if summary:
            # Format message
            message = format_summary_message(summary)
            
            # Send to Telegram (using asyncio)
            asyncio.run(send_telegram_message(message))
        else:
            print("⚠️ Could not calculate portfolio summary")
            
    except Exception as e:
        print(f"❌ Error in send_portfolio_update: {str(e)}")


def send_pl_alert():
    """Send alert for stocks with P/L between 5% and 10%"""
    print(f"🔔 Checking for stocks with P/L between 5% and 10% at {datetime.now()}...")
    
    try:
        # Get detailed portfolio
        portfolio_rows, summary_metrics, _ = calculate_detailed_portfolio()
        
        if not portfolio_rows:
            print("⚠️ No portfolio data available")
            return
        
        # Filter stocks with P/L between 5% and 10%
        alert_stocks = [
            stock for stock in portfolio_rows
            if 5.0 <= stock['P/L %'] <= 10.0
        ]
        
        if not alert_stocks:
            print("ℹ️ No stocks with P/L between 5% and 10%")
            # Optionally send a "no alerts" message
            # message = "📊 *P/L Alert (3:00 PM)*\n\nNo stocks with P/L between 5% and 10% today."
            # asyncio.run(send_telegram_message(message))
            return
        
        # Format alert message
        message = "📊 *Daily P/L Alert - 5% to 10% Range*\n"
        message += f"🕒 {datetime.now().strftime('%d-%b-%Y %I:%M %p')}\n\n"
        message += f"Found *{len(alert_stocks)}* stock(s) in the profit range:\n\n"
        
        # Sort by P/L percentage descending
        alert_stocks.sort(key=lambda x: x['P/L %'], reverse=True)
        
        for stock in alert_stocks:
            message += f"*{stock['Ticker']}* - {stock['Name']}\n"
            message += f"  • Qty: {stock['Qty']}\n"
            message += f"  • Avg Buy: {stock['Currency']} {stock['Avg Buy Price']:.2f}\n"
            message += f"  • Current: {stock['Currency']} {stock['Current Price']:.2f}\n"
            message += f"  • Invested: ₹{stock['Invested Value (INR)']:,.0f}\n"
            message += f"  • Current: ₹{stock['Current Value (INR)']:,.0f}\n"
            message += f"  • P&L: ₹{stock['P&L (INR)']:,.0f} ({stock['P/L %']:.2f}%)\n"
            message += "\n"
        
        message += "💡 *Consider booking profits on these positions.*"
        
        # Send to Telegram
        asyncio.run(send_telegram_message(message))
        print(f"✅ Sent P/L alert for {len(alert_stocks)} stock(s)")
        
    except Exception as e:
        print(f"❌ Error in send_pl_alert: {str(e)}")


def validate_config():
    """Validate that required configuration is present"""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'your_bot_token_here':
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not configured!")
        print("Please set TELEGRAM_BOT_TOKEN in .env file")
        return False
    
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == 'your_chat_id_here':
        print("❌ ERROR: TELEGRAM_CHAT_ID not configured!")
        print("Please set TELEGRAM_CHAT_ID in .env file")
        return False
    
    return True


def main():
    """Main scheduler function"""
    print("🤖 Starting Telegram Portfolio Notifier...")
    print(f"📅 Portfolio summary times: {NOTIFICATION_TIME_1}, {NOTIFICATION_TIME_2}, {NOTIFICATION_TIME_3}")
    print(f"🔔 P/L Alert time (5%-10%): {PL_ALERT_TIME}")
    
    # Validate configuration
    if not validate_config():
        print("\n📝 Setup Instructions:")
        print("1. Create a Telegram bot via @BotFather")
        print("2. Get your bot token")
        print("3. Start a chat with your bot")
        print("4. Get your chat ID from @userinfobot")
        print("5. Create a .env file (copy from .env.example)")
        print("6. Add your bot token and chat ID to .env")
        return
    
    # Schedule portfolio summary notifications
    schedule.every().day.at(NOTIFICATION_TIME_1).do(send_portfolio_update)
    schedule.every().day.at(NOTIFICATION_TIME_2).do(send_portfolio_update)
    schedule.every().day.at(NOTIFICATION_TIME_3).do(send_portfolio_update)
    
    # Schedule P/L alert notification at 3:00 PM
    schedule.every().day.at(PL_ALERT_TIME).do(send_pl_alert)
    
    print("✅ Scheduler started successfully!")
    print("💡 Press Ctrl+C to stop")
    
    # Optional: Send an immediate test notification
    print("\n🧪 Sending test notification...")
    send_portfolio_update()
    
    print("\n🧪 Testing P/L Alert...")
    send_pl_alert()
    
    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped by user")


if __name__ == "__main__":
    main()
