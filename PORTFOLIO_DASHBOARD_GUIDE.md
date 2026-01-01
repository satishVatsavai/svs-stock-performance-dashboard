# Stock Performance Dashboard Guide

Complete guide for using the Streamlit-based portfolio dashboard to view holdings, track performance, and manage your portfolio.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Dashboard Sections](#dashboard-sections)
- [Features](#features)
- [Handling Missing Price Data](#handling-missing-price-data)
- [Understanding Metrics](#understanding-metrics)
- [Performance & Caching](#performance--caching)
- [Troubleshooting](#troubleshooting)

---

## Overview

A Streamlit-based portfolio tracker that displays live stock prices and calculates comprehensive portfolio performance metrics with automatic handling of missing price data.

### Key Features

- 📊 **Real-time Portfolio Metrics** - Total invested, current value, P&L, XIRR
- 📈 **Holdings View** - Detailed breakdown of current positions with live prices
- 📚 **Trade Book** - Complete transaction history
- 🌍 **Multi-Currency Support** - Automatic USD to INR conversion
- ⚡ **Performance Optimized** - Smart caching, snapshot system, handles 50+ holdings
- 🎯 **Graceful Error Handling** - Displays holdings even when prices unavailable
- 🟧 **Visual Indicators** - Color-coded P&L ranges and missing data

---

## Quick Start

### Prerequisites

1. Python 3.8 or higher
2. Tradebook must be ready (see `TRADES_AND_PROCESSING_GUIDE.md`)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Dashboard

```bash
# Ensure tradebook is up to date
cd archivesCSV
python3 ../archivesPY/tradebook_builder.py consolidate

# Start the dashboard
cd ..
streamlit run performanceDashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

---

## Dashboard Sections

### 1. Portfolio Summary (Top Section)

**Metrics displayed:**

```
💼 Total Invested: ₹12,50,000
💎 Current Value: ₹15,75,000
💰 Unrealized P&L: ₹3,25,000 (26.00%)
✅ Realized Profit: ₹1,50,000
📈 Daily Change: ₹25,000 (1.61%)
📈 XIRR: 18.50%
📦 Holdings: 15 stocks
```

**Action Buttons:**
- **💰 Refresh Prices** (Normal Use): Fast refresh using snapshots
- **🔄 Full Recalc** (Verification): Processes full tradebook, slower but comprehensive

### 2. Holdings Tab

**Interactive table showing:**

| Ticker | Company | Qty | Avg Buy | Current | Invested | Value | P&L | P&L % |
|--------|---------|-----|---------|---------|----------|-------|-----|-------|
| RELIANCE.NS | Reliance Ind. | 50 | ₹2,450 | ₹2,648 | ₹1,22,500 | ₹1,32,375 | ₹9,875 | 8.06% |
| AAPL | Apple Inc. | 100 | $150.00 | $165.00 | ₹1,05,000 | ₹1,15,500 | ₹10,500 | 10.00% |

**Table Features:**
- ✅ Sortable columns (click headers)
- ✅ Live market prices
- ✅ Color-coded P&L ranges (see below)
- ✅ Formatted currency values
- ✅ Search/filter capability
- ✅ Orange highlighting for missing data

**Color Coding:**
- 🟢 **Green**: P&L between 5-10% (tactical profit booking range)
- 🟧 **Orange**: Missing price data (cannot calculate P&L)
- ⚪ **White**: Normal holdings

### 3. Trade Book Tab

**Complete transaction history:**

| Date | Ticker | Type | Qty | Price | Amount | Currency |
|------|--------|------|-----|-------|--------|----------|
| 2025-01-15 | AAPL | BUY | 10 | $150.00 | $1,500 | USD |
| 2025-01-16 | RELIANCE.NS | BUY | 5 | ₹2,450 | ₹12,250 | INR |
| 2025-01-20 | AAPL | SELL | 5 | $160.00 | $800 | USD |

**Features:**
- ✅ Paginated (20 records per page)
- ✅ Date-sorted (newest first)
- ✅ All transaction details
- ✅ Exchange rates included

---

## Features

### Real-Time Price Updates

**Data Source:**
- Yahoo Finance via `yfinance` library
- Automatic ticker detection from tradebook
- Update frequency: Every 5 minutes (via cache)

**Supported Markets:**
- 🇮🇳 Indian stocks (NSE/BSE): `.NS`, `.BO` suffix
- 🇺🇸 US stocks: No suffix (e.g., `AAPL`, `MSFT`)
- Mutual funds and ETFs

### Multi-Currency Support

**Automatic Conversion:**
- All amounts displayed in INR (₹)
- USD trades converted using historical exchange rates
- Exchange rates fetched and stored in tradebook

**Example:**
```
Trade: Buy 10 AAPL @ $150.00 (Exchange rate: ₹83.50/USD)
Invested (INR): 10 × 150 × 83.50 = ₹1,25,250
```

### Performance Optimization

**Snapshot System:**
- Uses year-end holdings snapshots
- Processes only current year trades
- 80-90% faster than full recalculation
- See `TRADES_AND_PROCESSING_GUIDE.md` for details

**Smart Caching:**
- 5-minute cache on price data
- Session state management
- Reduces API calls
- Prevents rate limiting

---

## Handling Missing Price Data

### The Problem

Sometimes Yahoo Finance cannot return prices due to:
- **Rate limiting** (429 errors - too many requests)
- **Network issues**
- **Invalid/delisted tickers**
- **Market holidays**

### The Solution

Holdings with missing prices are still displayed with available data:

**What's Always Shown:**
- ✅ Ticker symbol
- ✅ Company name
- ✅ Quantity held
- ✅ Average buy price (from historical trades)
- ✅ Currency
- ✅ Invested value (Qty × Avg Price × Exchange Rate)

**What Shows "N/A":**
- ❌ Current price
- ❌ Current value
- ❌ P&L (INR)
- ❌ P&L %

### Visual Indicators

#### 1. Orange Highlighting 🟧
Rows with missing price data are highlighted in orange, making them instantly recognizable.

**Example:**
| Ticker | Name | Qty | Avg Buy | Current | Invested | Value | P&L | P&L % |
|--------|------|-----|---------|---------|----------|-------|-----|-------|
| 🟧 QQQM | Invesco QQQ | 477.52 | $210.48 | **N/A** | ₹8,537,754 | **N/A** | **N/A** | **N/A** |
| ITC.NS | ITC Limited | 250 | ₹464.75 | ₹510.50 | ₹100,188 | ₹127,625 | ₹27,438 | 27.38% |

#### 2. Warning Banner
At the top of the holdings table:
```
⚠️ 31 holding(s) with missing price data (highlighted in orange). 
P/L and XIRR calculations exclude these holdings.
```

#### 3. Console Messages
During calculation, you'll see:
```
⚠️ Could not fetch price for QQQM: 429 Client Error: Too Many Requests
⚠️ Skipping P/L calculation for QQQM due to missing price data
```

### Impact on Metrics

**Total Invested:** ✅ Includes ALL holdings (based on historical trades)
```
Example: ₹53,373,410.77 (all 32 holdings)
```

**Current Value:** ⚠️ Includes only holdings with valid prices
```
Example: ₹7,299,500.00 (only 1 holding with valid price)
```

**Unrealized P&L:** ⚠️ Calculated from holdings with valid prices only
```
Example: Current Value - Invested (for valid holdings only)
```

**XIRR:** ⚠️ Calculated from holdings with valid prices only
```
Example: Annualized return based on available data
```

**Holdings Count:** ⚠️ Shows only holdings with valid prices
```
Example: 1 (out of 32 total holdings in portfolio)
```

### Real-World Example

**Scenario: Rate Limiting on 31 out of 32 holdings**

**Console Output:**
```
📊 PORTFOLIO SUMMARY:
   Total Holdings: 32
   With Valid Prices: 1
   With Missing Prices: 31
   Coverage: 3.1%

💰 FINANCIAL SUMMARY:
   Total Invested: ₹53,373,410.77    ✅ All holdings included
   Current Value: ₹7,299,500.00       ✅ Only 1 valid holding
   Unrealized P&L: ₹-46,073,910.77    ⚠️ Based on limited data
   XIRR: 0.00%                         ⚠️ Low due to limited data

✅ Dashboard remains fully functional!
```

**Dashboard Display:**
- ✅ All 32 holdings visible in table
- 🟧 31 rows highlighted in orange with "N/A" values
- ⚪ 1 row showing full calculated data
- ⚠️ Warning banner explaining the situation

### Best Practices

**If you see missing prices:**
1. **Wait a few minutes** - Rate limiting is temporary
2. **Click "💰 Refresh Prices"** - Retry with new cache
3. **Check later** - Prices usually available after cooldown period
4. **Verify tickers** - Ensure ticker symbols are correct

**What NOT to do:**
- ❌ Don't panic - your data is safe
- ❌ Don't repeatedly refresh - Worsens rate limiting
- ❌ Don't delete holdings - They'll reappear when prices available

---

## Understanding Metrics

### Total Invested
Sum of all BUY transactions (excluding SELLs).

**Calculation:**
```
For each holding:
  Invested = Quantity × Avg Buy Price × Exchange Rate

Total = Sum of all holdings' invested amounts
```

**Includes:**
- ✅ All holdings (even those with missing prices)
- ✅ Historical cost basis (FIFO method)
- ✅ Exchange rate conversions

### Current Value
Sum of current market value of all holdings.

**Calculation:**
```
For each holding with valid price:
  Current Value = Quantity × Current Price × Exchange Rate

Total = Sum of all holdings with valid prices
```

**Excludes:**
- ❌ Holdings with missing current prices (shown as N/A)

### Unrealized P&L
Paper gains/losses on current holdings.

**Calculation:**
```
Unrealized P&L = Current Value - Total Invested
Unrealized P&L % = (Unrealized P&L / Total Invested) × 100
```

**Notes:**
- Based only on holdings with valid current prices
- Does not include realized profits from past sells
- Changes daily with market movements

### Realized Profit
Actual profit/loss from completed SELL transactions.

**Calculation (FIFO Method):**
```
For each SELL:
  1. Take earliest remaining BUY lot
  2. Calculate: (Sell Price - Buy Price) × Quantity × Exchange Rate
  3. Repeat until SELL quantity fulfilled

Total = Sum of all SELL profits/losses
```

**Example:**
```
BUY 10 AAPL @ $150 (Jan 1)
BUY 10 AAPL @ $160 (Jan 15)
SELL 5 AAPL @ $170 (Feb 1)

Realized = 5 × ($170 - $150) × 83.50 = ₹8,350
(Uses first BUY lot per FIFO)
```

### Daily Change
Portfolio value change from yesterday's close to today.

**Calculation:**
```
Daily Change = Today's Current Value - Yesterday's Current Value
Daily Change % = (Daily Change / Yesterday's Current Value) × 100
```

**Notes:**
- Only calculated for holdings with valid prices
- Resets each market day
- Not cumulative

### XIRR (Extended Internal Rate of Return)
Annualized return rate considering cash flows and timing.

**Calculation:**
Uses Newton-Raphson method to find rate where NPV = 0:
```
For each BUY transaction:
  Cash flow = -Amount (outflow)

For current holdings (with valid prices):
  Cash flow = +Current Value (as if liquidated today)

XIRR = Annualized rate that balances all cash flows
```

**Why XIRR?**
- ✅ Accounts for timing of investments
- ✅ Handles irregular cash flows
- ✅ Industry-standard metric
- ✅ Better than simple percentage return

**Example:**
```
Invested ₹1,00,000 on Jan 1, 2025
Invested ₹50,000 on Jul 1, 2025
Current value ₹1,80,000 on Jan 1, 2026

Simple return: (180k - 150k) / 150k = 20%
XIRR: ~23.5% (accounts for mid-year investment)
```

### Holdings Count
Number of unique tickers currently held with valid prices.

**Counted:**
- ✅ Holdings with quantity > 0
- ✅ Holdings with valid current price

**Not counted:**
- ❌ Holdings with missing prices (but still displayed)
- ❌ Fully sold positions (quantity = 0)

---

## Performance & Caching

### How It Works

```
User opens dashboard
     ↓
Load tradebook.csv
     ↓
Load latest snapshot (e.g., 2025)
     ↓
Process only 2026 trades (incremental)
     ↓
Fetch current prices (with 5-min cache)
     ↓
Calculate metrics (FIFO, XIRR, etc.)
     ↓
Display in Streamlit
```

### Caching Strategy

**Level 1 - Streamlit Cache (5 minutes):**
```python
@st.cache_data(ttl=300)
def load_portfolio_data():
    # Expensive operations cached here
    # - Load tradebook
    # - Fetch market prices
    # - Calculate metrics
```

**Benefits:**
- ✅ Fast tab switching (no reloading)
- ✅ Reduced API calls to Yahoo Finance
- ✅ Lower chance of rate limiting
- ✅ Better user experience

**Level 2 - Session State:**
```python
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = True
    # Load data once per session
```

**Benefits:**
- ✅ Maintains state across interactions
- ✅ Preserves user selections
- ✅ Smooth navigation

### Rate Limiting Protection

**Yahoo Finance Limits:**
- ~1,000-2,000 requests per hour
- Varies by IP and usage patterns
- Returns 429 error when exceeded

**Dashboard Protection:**
- ✅ 5-minute cache reduces requests
- ✅ Graceful handling of missing prices
- ✅ Orange highlighting for affected holdings
- ✅ Dashboard remains functional

**Best Practices:**
- Don't spam refresh button
- Wait 5 minutes between manual refreshes
- Use "Full Recalc" sparingly (processes all tickers)

---

## Troubleshooting

### Dashboard Won't Load

**Check dependencies:**
```bash
pip install -r requirements.txt
```

**Verify tradebook exists:**
```bash
ls -la archivesCSV/tradebook.csv
```

**Check for errors:**
```bash
streamlit run performanceDashboard.py
# Look for error messages in console
```

### No Holdings Displayed

**Verify tradebook has data:**
```bash
wc -l archivesCSV/tradebook.csv
# Should show more than 1 line
```

**Check for open positions:**
```bash
# Ensure you have BUY transactions without matching SELLs
head -20 archivesCSV/tradebook.csv
```

**Verify date format:**
```bash
# Dates should be YYYY-MM-DD
grep -v "^Date" archivesCSV/tradebook.csv | head -5
```

### Incorrect Metrics

**Use Full Recalc:**
1. Click "🔄 Full Recalc" button
2. Processes full tradebook (bypasses snapshots)
3. Compare with normal mode

**Regenerate snapshots:**
```bash
python3 generate_snapshots.py
```

**Rebuild tradebook:**
```bash
cd archivesCSV
python3 ../archivesPY/tradebook_builder.py rebuild
```

### Missing Prices (Orange Rows)

**Rate limiting (most common):**
- Wait 5-10 minutes
- Click "💰 Refresh Prices"
- Check again later

**Invalid ticker:**
```bash
# Verify ticker format
# Indian: RELIANCE.NS, INFY.NS
# US: AAPL, MSFT (no suffix)
```

**Delisted stock:**
- Price may be permanently unavailable
- Holding will always show as orange
- Consider removing from portfolio

### Slow Performance

**Too many trades:**
```bash
# Check tradebook size
wc -l archivesCSV/tradebook.csv

# If > 10,000 trades, ensure snapshots are being used
ls -la archivesCSV/holdings_snapshot_*.csv
```

**No snapshots:**
```bash
# Generate snapshots
python3 generate_snapshots.py

# Verify creation
ls -la archivesCSV/holdings_snapshot_*.csv
```

**Cache not working:**
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/cache

# Restart dashboard
streamlit run performanceDashboard.py
```

---

## Summary

### Quick Reference

**Start Dashboard:**
```bash
streamlit run performanceDashboard.py
```

**Refresh Prices:**
- Click "💰 Refresh Prices" button

**Verify Accuracy:**
- Click "🔄 Full Recalc" button

**Understanding Colors:**
- 🟢 Green: 5-10% profit (good for booking)
- 🟧 Orange: Missing price data
- ⚪ White: Normal holdings

**Missing Prices:**
- Holdings still displayed with available data
- Wait and refresh if rate limited
- Check ticker symbols if persistent

### Key Points

1. **Dashboard is read-only** - Never modifies your trade data
2. **Snapshots speed things up** - 80-90% faster calculations
3. **Missing prices are handled gracefully** - Portfolio remains functional
4. **XIRR is the gold standard** - Better than simple returns
5. **5-minute cache** - Balances freshness and performance

For trade processing and tradebook management, see `TRADES_AND_PROCESSING_GUIDE.md`.

For Telegram notifications, see `TELEGRAM_NOTIFICATIONS_GUIDE.md`.
