# P/L Alert Feature

## Overview
The Telegram notifier now includes a **daily P/L alert** feature that automatically notifies you about stocks in your portfolio with profit/loss between **5% and 10%** at **3:00 PM** every day.

## Why This Feature?
Stocks with 5-10% profit are in the "sweet spot" for potential profit booking:
- Not too small (< 5%) where you might want to hold longer
- Not too large (> 10%) where you might want to keep riding the momentum
- Ideal range for tactical profit booking decisions

## How It Works

### Daily Schedule
- **3:00 PM (15:00)**: Checks all holdings for stocks with P/L between 5% and 10%
- If any stocks match, sends a detailed notification via Telegram
- If no stocks match, no notification is sent (optional: can be configured to send "no alerts" message)

### Notification Format
When stocks are found in the 5-10% range, you'll receive a message like:

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

## Configuration

### Environment Variables (.env)
```bash
# P/L Alert time (24-hour format)
PL_ALERT_TIME=15:00
```

You can change the time by modifying `PL_ALERT_TIME` in your `.env` file.

### Customizing the P/L Range
To change the 5-10% range, edit `telegram_notifier.py`:

```python
# Find this line in send_pl_alert() function:
alert_stocks = [
    stock for stock in portfolio_rows
    if 5.0 <= stock['P/L %'] <= 10.0  # Change these values
]
```

Examples:
- For 3-8% range: `if 3.0 <= stock['P/L %'] <= 8.0`
- For 10-15% range: `if 10.0 <= stock['P/L %'] <= 15.0`
- For any profit: `if stock['P/L %'] > 0`

## Testing

### Test Without Sending to Telegram
```bash
python3 test_pl_alert.py
```

This will:
- Show you all current holdings
- Display which stocks are in the 5-10% range
- Preview the alert message without sending to Telegram

### Test the Full Notification
```bash
python3 telegram_notifier.py
```

This will:
- Send a test portfolio summary immediately
- Send a test P/L alert immediately
- Then start the scheduler for automatic daily notifications

## Features

### Smart Sorting
Stocks are sorted by P/L percentage (highest first), so you see the most profitable ones at the top.

### Complete Information
Each alert includes:
- Stock ticker and full company name
- Current quantity held
- Average buy price
- Total invested amount
- Current value
- Absolute P&L in rupees
- P&L percentage

### No Spam
- Only sends alerts when stocks are actually in the 5-10% range
- Won't send empty notifications if no stocks match

## Running in Background

### Option 1: Using the start_notifier.sh script
```bash
./start_notifier.sh
```

### Option 2: Using screen
```bash
screen -S portfolio_notifier
python3 telegram_notifier.py
# Press Ctrl+A then D to detach
```

### Option 3: Using nohup
```bash
nohup python3 telegram_notifier.py > notifier.log 2>&1 &
```

## Stopping the Notifier

```bash
pkill -f telegram_notifier.py
```

Or find the process ID:
```bash
ps aux | grep telegram_notifier
kill <process_id>
```

## Troubleshooting

### No Alerts Received at 3:00 PM
1. Check that `telegram_notifier.py` is running: `ps aux | grep telegram_notifier`
2. Verify your `.env` has `PL_ALERT_TIME=15:00`
3. Run test script to see if any stocks are in range: `python3 test_pl_alert.py`

### Yahoo Finance Rate Limits (429 Errors)
The script fetches market prices from Yahoo Finance. If you see "429 Too Many Requests" errors:
- This is normal occasionally
- The script will continue to work with available data
- Most recent trade prices are used as fallback for missing data

### Want to Always Get a Notification
Edit `telegram_notifier.py` and uncomment these lines in `send_pl_alert()`:

```python
if not alert_stocks:
    print("ℹ️ No stocks with P/L between 5% and 10%")
    # Uncomment the next two lines to get a "no alerts" message
    message = "📊 *P/L Alert (3:00 PM)*\n\nNo stocks with P/L between 5% and 10% today."
    asyncio.run(send_telegram_message(message))
    return
```

## Example Scenarios

### Scenario 1: Conservative Profit Booking
**Range**: 5-8%
**Strategy**: Book profits early, minimize downside risk

### Scenario 2: Moderate Profit Booking
**Range**: 5-10% (default)
**Strategy**: Balance between capturing gains and holding for more upside

### Scenario 3: Aggressive Profit Booking
**Range**: 10-15%
**Strategy**: Let winners run, book profits on strong performers

## Integration with Portfolio

The P/L alert uses the same `calculate_detailed_portfolio()` function as the Streamlit dashboard, ensuring:
- ✅ Consistent calculations
- ✅ Real-time market prices
- ✅ Accurate P/L percentages
- ✅ Exchange rate conversions for USD stocks

## Future Enhancements

Potential additions (not yet implemented):
- Multiple alert ranges (e.g., 5-10% AND 15-20%)
- Loss alerts (e.g., stocks down 5-10%)
- Weekly summary of all alerts
- Custom alert ranges per stock
- Alert history tracking
