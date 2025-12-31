# Stock Performance Dashboard

A comprehensive portfolio tracking system with Streamlit dashboard and Telegram notifications.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Build your tradebook
python3 tradebook_builder.py consolidate

# 3. Run the dashboard
streamlit run performanceDashboard.py
```

## ✨ Features

### 📊 Interactive Dashboard
- **Real-time portfolio metrics**: Total value, P&L, XIRR, daily changes
- **Holdings view**: Detailed breakdown with live prices
- **Trade history**: Complete transaction log
- **Multi-currency support**: Automatic USD/INR conversion

### 📱 Telegram Notifications
- **Automated updates**: 3 times daily (customizable)
- **P/L alerts**: Daily notifications for stocks with 5-10% profit
- **Background service**: Runs continuously without manual intervention

### 📈 Portfolio Analytics
- **XIRR calculation**: Annualized returns accounting for cash flow timing
- **Realized vs Unrealized P&L**: Track actual profits vs paper gains
- **Per-stock performance**: Individual stock P&L and percentages
- **Daily tracking**: Monitor day-over-day changes

## 📚 Documentation

### Core Guides

- **[Dashboard Guide](DASHBOARD_GUIDE.md)** - Using the Streamlit dashboard
  - Running locally and deploying to Streamlit Cloud
  - Understanding metrics and calculations
  - Troubleshooting and optimization
  
- **[Tradebook Guide](TRADEBOOK_GUIDE.md)** - Building and managing your tradebook
  - CSV format and requirements
  - Consolidating trade files
  - Updating and maintaining tradebook
  
- **[Telegram Guide](TELEGRAM_GUIDE.md)** - Setting up automated notifications
  - Creating Telegram bot
  - Configuring notifications
  - Running as background service

### Quick References

- **[Quick Start](QUICK_START.txt)** - Fast setup commands
- **[Requirements](requirements.txt)** - Python dependencies

## 🎯 Workflow

### 1. Manage Your Trades

```bash
# Add trades to CSV files
# trades2025EquityKite.csv, trades2025MFsCoin.csv, etc.

# Consolidate into tradebook
python3 tradebook_builder.py consolidate

# Verify
python3 tradebook_builder.py status
```

### 2. View Your Portfolio

```bash
# Local dashboard
streamlit run performanceDashboard.py

# Or deploy to Streamlit Cloud
# See DASHBOARD_GUIDE.md for deployment instructions
```

### 3. Get Notifications (Optional)

```bash
# Setup Telegram bot (one-time)
cp .env.example .env
# Edit .env with your credentials

# Start notifier
./start_notifier.sh

# See TELEGRAM_GUIDE.md for detailed setup
```

## 🏗️ Architecture

```
Trade CSV Files
    ├── trades2025EquityKite.csv
    ├── trades2024MFsCoin.csv
    └── SGBs.csv
         ↓
tradebook_builder.py  →  tradebook.csv
         ↓
    ┌────────────────────────┐
    ↓                        ↓
performanceDashboard.py  telegram_notifier.py
    ↓                        ↓
portfolio_calculator.py (shared)
    ↓
Yahoo Finance (live prices)
```

## 📦 Key Files

| File | Purpose |
|------|---------|
| `performanceDashboard.py` | Streamlit dashboard UI |
| `portfolio_calculator.py` | Portfolio calculation engine |
| `tradebook_builder.py` | CLI tool to build tradebook |
| `telegram_notifier.py` | Automated Telegram notifications |
| `tradebook.csv` | Consolidated trade data |
| `requirements.txt` | Python dependencies |

## 🔧 Technologies

- **Streamlit** - Interactive web dashboard
- **pandas** - Data manipulation and analysis
- **yfinance** - Live stock price fetching
- **pyxirr** - XIRR (Extended Internal Rate of Return) calculations
- **python-telegram-bot** - Telegram notifications
- **schedule** - Automated task scheduling

## 📊 CSV Format

Your trade files should follow this format:

```csv
Date,Ticker,Country,Type,Qty,Price,Currency
2025-01-15,AAPL,USA,BUY,10,150.00,USD
2025-01-16,RELIANCE.NS,IND,BUY,5,2450.00,INR
2025-01-17,AAPL,USA,SELL,5,155.00,USD
```

**Column descriptions:**
- **Date**: YYYY-MM-DD format
- **Ticker**: Stock symbol (e.g., AAPL, RELIANCE.NS)
- **Country**: USA or IND (for exchange rates)
- **Type**: BUY or SELL
- **Qty**: Quantity of shares
- **Price**: Price per share
- **Currency**: USD or INR

Exchange rates are automatically fetched and added by `tradebook_builder.py`.

## 🚀 Deployment

### Local Usage

Perfect for personal use:
```bash
streamlit run performanceDashboard.py
```

### Streamlit Cloud

For web access from anywhere:

1. Push code to GitHub
2. Deploy on [share.streamlit.io](https://share.streamlit.io)
3. Set main file: `performanceDashboard.py`

**See [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) for detailed deployment instructions.**

## 🔐 Security

- ✅ Keep `.env` file local (never commit)
- ✅ Use private GitHub repo for confidential data
- ✅ Telegram bot tokens are secret credentials
- ✅ `.env` is already in `.gitignore`

## 📝 Example Notifications

### Portfolio Summary (3x daily)
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
```

### P/L Alert (Daily at 3 PM)
```
📊 Daily P/L Alert - 5% to 10% Range

Found 2 stock(s) in profit range:

*RELIANCE.NS*
  • P&L: ₹9,875 (8.06%)
  • Consider booking profits

*TCS.NS*
  • P&L: ₹5,280 (5.50%)
  • Consider booking profits
```

## 🆘 Support

### Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Dashboard won't load | Run `python3 tradebook_builder.py consolidate` |
| Holdings not showing | Wait 5 min (cache/rate limit), then refresh |
| 429 errors | Normal - rate limiting protection active |
| Telegram not working | Run `python3 test_telegram.py` |
| Wrong calculations | Run `python3 tradebook_builder.py rebuild` |

**For detailed troubleshooting, see the relevant guide:**
- Dashboard issues → [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)
- Tradebook issues → [TRADEBOOK_GUIDE.md](TRADEBOOK_GUIDE.md)
- Telegram issues → [TELEGRAM_GUIDE.md](TELEGRAM_GUIDE.md)

## 📈 Performance

- **Small portfolio** (< 20 stocks): ~5-10 seconds first load
- **Medium portfolio** (20-50 stocks): ~20-30 seconds first load
- **Large portfolio** (50+ stocks): ~40-60 seconds first load
- **Cached loads**: Instant (5-minute cache)

Rate limiting protection ensures high success rate (>95%) even with large portfolios.

## 🎯 Roadmap

Current features are production-ready. Potential enhancements:
- Historical performance charts
- Multiple portfolio support
- Tax reports
- Dividend tracking
- More data source integrations

## 📄 License

Personal use project. Modify as needed for your portfolio tracking needs.

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Dashboard framework
- [yfinance](https://github.com/ranaroussi/yfinance) - Market data
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram integration

---

**Get Started:** Choose your guide:
- 📊 [Dashboard Guide](DASHBOARD_GUIDE.md) - Run the portfolio dashboard
- 📚 [Tradebook Guide](TRADEBOOK_GUIDE.md) - Manage your trade data
- 📱 [Telegram Guide](TELEGRAM_GUIDE.md) - Setup automated notifications
