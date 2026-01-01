# Telegram Portfolio Notifications Guide

## Overview

Get automated portfolio updates on Telegram 3 times a day, plus daily profit/loss alerts for stocks in specific ranges.

## Features

- 📱 **Portfolio Summary**: Automated updates 3x daily with all key metrics
- 🔔 **P/L Alerts**: Daily notifications for stocks with 5-10% profit at 3:00 PM
- ⏰ **Customizable Times**: Set your preferred notification schedule
- 🔄 **Background Service**: Runs continuously without manual intervention

## Quick Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat and send `/newbot`
3. Follow prompts to name your bot (e.g., "My Portfolio Bot")
4. Save the **Bot Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID

**Option A - Using @userinfobot:**
1. Search for **@userinfobot** in Telegram
2. Start a chat with it
3. Note your **Chat ID** (number like `123456789`)

**Option B - Using API:**
1. Start a chat with your new bot (send any message)
2. Visit: `https://api.telegram.org/bot<YourBotToken>/getUpdates`
3. Look for `"chat":{"id":123456789}` in the response

### 3. Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

Add your values:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Customize notification times (24-hour format)
NOTIFICATION_TIME_1=09:00
NOTIFICATION_TIME_2=14:00
NOTIFICATION_TIME_3=18:00

# P/L Alert time
PL_ALERT_TIME=15:00
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Test Your Setup

```bash
python3 archivesPY/test_telegram.py
```

You should receive a test message immediately!

### 6. Start the Notifier

```bash
./start_notifier.sh
```

Or manually:
```bash
python3 telegram_notifier.py
```

## Notification Types

### Portfolio Summary (3x Daily)

Default times: **9:00 AM**, **2:00 PM**, **6:00 PM**

**Message format:**
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

**Includes:**
- Total invested amount
- Current portfolio value
- Unrealized P&L (paper gains/losses)
- Realized profit (from completed sells)
- Daily change (today's movement)
- XIRR (annualized return rate)
- Number of holdings

### P/L Alerts (Daily at 3:00 PM)

Notifies you about stocks with **5-10% profit** - the sweet spot for tactical profit booking.

**Message format:**
```
📊 Daily P/L Alert - 5% to 10% Range
🕒 31-Dec-2025 03:00 PM

Found 2 stock(s) in the profit range:

*RELIANCE.NS* - Reliance Industries Ltd
  • Qty: 50
  • Avg Buy: INR 2,450.00
  • Current: INR 2,647.50
  • Invested: ₹122,500
  • Current: ₹132,375
  • P&L: ₹9,875 (8.06%)

*TCS.NS* - Tata Consultancy Services Ltd
  • Qty: 30
  • Avg Buy: INR 3,200.00
  • Current: INR 3,376.00
  • Invested: ₹96,000
  • Current: ₹101,280
  • P&L: ₹5,280 (5.50%)

💡 Consider booking profits on these positions.
```

**Why 5-10%?**
- Not too small (< 5%) - want to hold longer
- Not too large (> 10%) - might want to ride momentum
- **Ideal range for tactical profit booking**

## Running as Background Service

### Option 1: Quick Start Script

```bash
./start_notifier.sh
```

This script:
- ✅ Checks dependencies
- ✅ Validates configuration
- ✅ Starts notifier in background using `screen`

To check if running:
```bash
screen -ls
```

To reattach:
```bash
screen -r portfolio_notifier
```

### Option 2: Using screen (Manual)

```bash
screen -S portfolio_notifier
python3 telegram_notifier.py
# Press Ctrl+A then D to detach
```

### Option 3: Using nohup

```bash
nohup python3 telegram_notifier.py > notifier.log 2>&1 &
```

Check logs:
```bash
tail -f notifier.log
```

### Option 4: Using launchd (Mac)

Create `~/Library/LaunchAgents/com.portfolio.notifier.plist`:

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

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.portfolio.notifier.plist
launchctl start com.portfolio.notifier
```

Check status:
```bash
launchctl list | grep portfolio
tail -f /tmp/portfolio-notifier.log
```

### Option 5: Using systemd (Linux)

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
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable portfolio-notifier
sudo systemctl start portfolio-notifier
sudo systemctl status portfolio-notifier
```

View logs:
```bash
sudo journalctl -u portfolio-notifier -f
```

## Customization

### Change Notification Times

Edit `.env`:
```env
# Morning update
NOTIFICATION_TIME_1=08:30

# Midday update
NOTIFICATION_TIME_2=13:00

# Evening update
NOTIFICATION_TIME_3=20:00

# P/L alert
PL_ALERT_TIME=15:00
```

### Add More Notifications

Edit `telegram_notifier.py`:

```python
# Add more scheduled times
schedule.every().day.at("11:00").do(send_portfolio_update)
schedule.every().day.at("16:30").do(send_portfolio_update)
```

### Change P/L Alert Range

Edit `telegram_notifier.py` in the `send_pl_alert()` function:

```python
# Current: 5-10% range
alert_stocks = [
    stock for stock in portfolio_rows
    if 5.0 <= stock['P/L %'] <= 10.0
]

# Examples:
# For 3-8% range:
if 3.0 <= stock['P/L %'] <= 8.0

# For 10-15% range:
if 10.0 <= stock['P/L %'] <= 15.0

# For any profit:
if stock['P/L %'] > 0

# For loss alerts (-10% to -5%):
if -10.0 <= stock['P/L %'] <= -5.0
```

### Disable P/L Alerts

Comment out the P/L alert schedule in `telegram_notifier.py`:

```python
# Comment this line:
# schedule.every().day.at(pl_alert_time).do(send_pl_alert)
```

### Always Get P/L Alert (Even if Empty)

Edit `telegram_notifier.py` in `send_pl_alert()`:

```python
if not alert_stocks:
    print("ℹ️ No stocks with P/L between 5% and 10%")
    # Uncomment these lines:
    message = "📊 *P/L Alert (3:00 PM)*\n\nNo stocks with P/L between 5% and 10% today."
    asyncio.run(send_telegram_message(message))
    return
```

## Managing the Service

### Check if Running

```bash
# For screen
screen -ls

# For systemd (Linux)
sudo systemctl status portfolio-notifier

# For launchd (Mac)
launchctl list | grep portfolio

# General (any method)
ps aux | grep telegram_notifier
```

### Stop the Service

```bash
# If using screen
screen -r portfolio_notifier
# Then press Ctrl+C

# If using systemd
sudo systemctl stop portfolio-notifier

# If using launchd
launchctl stop com.portfolio.notifier

# Kill by process
pkill -f telegram_notifier.py
```

### Restart the Service

```bash
# If using systemd
sudo systemctl restart portfolio-notifier

# If using launchd
launchctl stop com.portfolio.notifier
launchctl start com.portfolio.notifier

# Manual restart
pkill -f telegram_notifier.py
./start_notifier.sh
```

### View Logs

```bash
# If using nohup
tail -f notifier.log

# If using systemd
sudo journalctl -u portfolio-notifier -f

# If using launchd
tail -f /tmp/portfolio-notifier.log

# If using screen
screen -r portfolio_notifier
# Then scroll up
```

## Troubleshooting

### "TELEGRAM_BOT_TOKEN not configured"

**Cause:** Missing or incorrect `.env` file

**Solution:**
1. Verify `.env` exists (not `.env.example`)
2. Check token is correct
3. Ensure no quotes around the token:
   ```env
   # ✅ Correct
   TELEGRAM_BOT_TOKEN=123456789:ABCdef...
   
   # ❌ Wrong
   TELEGRAM_BOT_TOKEN="123456789:ABCdef..."
   ```

### "TELEGRAM_CHAT_ID not configured"

**Cause:** Missing chat ID in `.env`

**Solution:**
1. Verify you got your chat ID from @userinfobot
2. Add it to `.env` without quotes
3. Make sure you started a chat with your bot first

### Messages Not Being Sent

**Possible causes:**
- Bot token is invalid
- Chat ID is incorrect
- Bot is blocked
- No internet connection

**Solutions:**
1. Test with `python3 archivesPY/test_telegram.py`
2. Verify you started a chat with the bot (send any message first)
3. Check bot isn't blocked in Telegram
4. Verify credentials in `.env`
5. Check console/log output for specific errors

### Bot Doesn't Respond

**Solution:**
1. Start a conversation with your bot first
2. Send any message to activate the chat
3. Then run the notifier

### Import Errors

**Cause:** Missing dependencies

**Solution:**
```bash
pip install -r requirements.txt
```

### No P/L Alerts at 3:00 PM

**Checks:**
1. Verify notifier is running: `ps aux | grep telegram_notifier`
2. Check `.env` has `PL_ALERT_TIME=15:00`
3. Verify stocks are in 5-10% range: `python3 archivesPY/test_telegram.py`
4. Check logs for errors

### Rate Limit Errors (429)

**Cause:** Yahoo Finance API rate limiting

**Impact:** Some stocks may not have current prices

**Solution:**
- This is normal and temporary
- Script uses fallback (last trade price)
- Most data will still be available
- Try again after a few minutes

## Security

### ⚠️ Important Security Notes

- **Never commit `.env` to git** (already in `.gitignore`)
- **Keep your bot token secret** - treat it like a password
- **Don't share your chat ID publicly**
- **Restrict who can message your bot**

### Best Practices

✅ **Do:**
- Keep `.env` file local only
- Use environment-specific credentials
- Regularly rotate bot tokens if compromised

❌ **Don't:**
- Share bot token in screenshots or logs
- Commit `.env` or `.env.example` with real credentials
- Use the same bot for multiple purposes

## Testing

### Test Configuration

```bash
python3 archivesPY/test_telegram.py
```

**Expected output:**
```
✅ Configuration loaded successfully
✅ Bot token configured
✅ Chat ID configured
📱 Sending test message...
✅ Test message sent successfully!
Check your Telegram for the message.
```

### Test P/L Alerts

Create a test script or check manually:

```bash
python3 telegram_notifier.py
```

This will:
1. Send an immediate portfolio summary
2. Send an immediate P/L alert (if stocks in range)
3. Start the scheduler for future notifications

### Manual Test Message

Edit `telegram_notifier.py` temporarily:

```python
# Add at the end of the file
if __name__ == "__main__":
    asyncio.run(send_telegram_message("Test message"))
```

## Integration with Portfolio

The notifier uses `portfolio_calculator.py` which:
- ✅ Reads `tradebook.csv` as-is (same as dashboard)
- ✅ Fetches live market prices
- ✅ Calculates all metrics identically to dashboard
- ✅ Ensures consistency between notifications and dashboard

**This means:**
- Portfolio summary matches dashboard exactly
- P/L alerts use same calculations
- No data discrepancies

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./start_notifier.sh` | Start notifier (recommended) |
| `python3 archivesPY/test_telegram.py` | Test configuration |
| `screen -ls` | Check if running (screen) |
| `ps aux \| grep telegram` | Check if running (general) |
| `pkill -f telegram_notifier` | Stop notifier |
| `tail -f notifier.log` | View logs (nohup) |

## Files

| File | Purpose |
|------|---------|
| `.env` | Your credentials (never commit) |
| `.env.example` | Template for `.env` |
| `telegram_notifier.py` | Main notification script |
| `archivesPY/test_telegram.py` | Configuration tester |
| `start_notifier.sh` | Quick start script |
| `portfolio_calculator.py` | Calculation engine |

## Support

If you encounter issues:
1. Run `python3 archivesPY/test_telegram.py` first
2. Check logs for specific error messages
3. Verify `.env` configuration
4. Ensure bot has been activated (send message first)
5. Check internet connectivity

---

**Related Documentation:**
- `TRADEBOOK_GUIDE.md` - Building your tradebook
- `DASHBOARD_GUIDE.md` - Using the Streamlit dashboard
