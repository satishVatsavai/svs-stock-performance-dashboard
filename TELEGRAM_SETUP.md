# Telegram Notification Setup Guide

This guide will help you set up automated Telegram notifications for your portfolio summary.

## Features
- 📱 Sends portfolio summary to Telegram 3 times a day
- 📊 Includes all key metrics: invested amount, current value, P&L, XIRR, daily changes
- 🔔 **NEW:** Daily P/L alerts for stocks with 5%-10% profit at 3:00 PM
- ⏰ Customizable notification times
- 🔄 Runs continuously in the background

## Setup Instructions

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat with BotFather
3. Send the command `/newbot`
4. Follow the prompts to name your bot (e.g., "My Portfolio Bot")
5. BotFather will give you a **Bot Token** - save this! It looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### Step 2: Get Your Chat ID

1. Search for **@userinfobot** in Telegram
2. Start a chat with it
3. It will reply with your user information
4. Note down your **Chat ID** (a number like `123456789`)

Alternatively:
1. Start a chat with your newly created bot
2. Send any message to it
3. Visit: `https://api.telegram.org/bot<YourBotToken>/getUpdates`
4. Look for `"chat":{"id":123456789}` in the response

### Step 3: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your values:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789
   
   # Customize notification times (24-hour format)
   NOTIFICATION_TIME_1=07:00
   NOTIFICATION_TIME_2=15:00
   NOTIFICATION_TIME_3=23:00
   
   # P/L Alert time for stocks between 5% and 10% profit
   PL_ALERT_TIME=15:00
   ```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Test the Notification

Run the notifier once to test:
```bash
python telegram_notifier.py
```

You should receive a test message immediately with your portfolio summary!

### Step 6: Run as a Background Service

#### Option A: Using screen (Linux/Mac)
```bash
screen -S portfolio_notifier
python telegram_notifier.py
# Press Ctrl+A then D to detach
```

To reattach: `screen -r portfolio_notifier`

#### Option B: Using nohup (Linux/Mac)
```bash
nohup python telegram_notifier.py > notifier.log 2>&1 &
```

To stop: `pkill -f telegram_notifier.py`

#### Option C: Using launchd (Mac)
Create a file at `~/Library/LaunchAgents/com.portfolio.notifier.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.portfolio.notifier</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/full/path/to/telegram_notifier.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/full/path/to/your/project</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/portfolio-notifier.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/portfolio-notifier.err</string>
</dict>
</plist>
```

Then run:
```bash
launchctl load ~/Library/LaunchAgents/com.portfolio.notifier.plist
```

#### Option D: Using systemd (Linux)
Create `/etc/systemd/system/portfolio-notifier.service`:

```ini
[Unit]
Description=Portfolio Telegram Notifier
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/your/project
ExecStart=/usr/bin/python3 /path/to/your/project/telegram_notifier.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable portfolio-notifier
sudo systemctl start portfolio-notifier
sudo systemctl status portfolio-notifier
```

## Message Format

The notification will include:
- 💼 Total Invested Amount
- 💎 Current Portfolio Value
- 💰/⚠️ Unrealized P&L (with percentage)
- ✅ Realized Profit
- 📈/📉 Daily Change (with percentage)
- 📈 XIRR (annualized return)
- 📦 Number of holdings

## Customization

### Change Notification Times
Edit the times in your `.env` file (use 24-hour format):
```
NOTIFICATION_TIME_1=08:30
NOTIFICATION_TIME_2=13:00
NOTIFICATION_TIME_3=20:00
```

### Add More Notifications
Edit `telegram_notifier.py` and add more scheduled times:
```python
schedule.every().day.at("11:00").do(send_portfolio_update)
schedule.every().day.at("16:00").do(send_portfolio_update)
```

## Troubleshooting

### "TELEGRAM_BOT_TOKEN not configured" error
- Make sure you created a `.env` file (not `.env.example`)
- Check that your bot token is correct
- Ensure there are no quotes around the token in `.env`

### "TELEGRAM_CHAT_ID not configured" error
- Verify your chat ID is correct
- Make sure you started a chat with your bot first

### Messages not being sent
- Check that your bot token and chat ID are correct
- Verify your bot is not blocked
- Check the log file for error messages
- Ensure you have internet connectivity

### Bot doesn't respond
- Make sure you started a conversation with your bot in Telegram first
- Send any message to your bot before running the script

## Security Notes

⚠️ **Important**: 
- Never commit your `.env` file to version control
- Keep your bot token secret
- The `.env` file is already in `.gitignore`

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify all environment variables are set correctly
3. Test with a simple message first
4. Check Telegram's API status

## Example Output

```
📊 SV's Portfolio Update
━━━━━━━━━━━━━━━━━━━

💼 Total Invested: ₹12,50,000
💎 Current Value: ₹15,75,000

💰 Unrealized P&L: ₹3,25,000 (26.00%)
✅ Realized Profit: ₹1,50,000

📈 Daily Change: ₹25,000 (1.61%)

📈 XIRR: 18.50%
📦 Holdings: 15 stocks

━━━━━━━━━━━━━━━━━━━
Updated: 31 December 2025
```
