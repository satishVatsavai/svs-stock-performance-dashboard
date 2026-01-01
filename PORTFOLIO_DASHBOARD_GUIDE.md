# Stock Performance Dashboard Guide

Complete guide for using the Streamlit-based portfolio dashboard to view holdings, track performance, and manage your portfolio.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Dashboard Sections](#dashboard-sections)
- [Features](#features)
- [Handling Missing Price Data](#handling-missing-price-data)
- [Understanding Metrics](#understanding-metrics)
- [Per-Year XIRR Analysis](#per-year-xirr-analysis)
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

### 2. Portfolio Overview Tab

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

### 3. Per-Year XIRR Tab

**Comprehensive year-by-year performance analysis showing:**

#### Summary Metrics (Top Row)
- **Current XIRR**: Latest cumulative return with improvement from inception
- **Total Invested**: Amount invested up to latest year-end
- **Portfolio Value**: Portfolio value at latest year-end
- **Total Returns**: Cash returns received over the period

#### Year-by-Year Breakdown Table

Shows detailed metrics for each year (e.g., 2022-2025):

| 📊 | Year | XIRR % | Period | First Invest | Total Invested | Total Returns | Portfolio Value | Absolute Gain | Holdings | Transactions |
|---|------|--------|--------|--------------|----------------|---------------|-----------------|---------------|----------|--------------|
| 🚀 | 2022 | -0.00% | 1.3 yrs | Sep 13, 2021 | ₹43,40,900 | ₹0 | ₹43,40,900 | ₹-100 | 3 | 5 |
| 📈 | 2023 | 6.77% | 2.3 yrs | Sep 13, 2021 | ₹2,62,68,344 | ₹12,45,678 | ₹1,49,94,127 | ₹1,12,85,783 | 117 | 234 |
| ✅ | 2024 | 15.68% | 3.3 yrs | Sep 13, 2021 | ₹9,10,81,320 | ₹45,12,345 | ₹3,68,44,424 | ₹4,57,63,104 | 28 | 312 |
| ➡️ | 2025 | 10.62% | 4.3 yrs | Sep 13, 2021 | ₹14,14,56,133 | ₹89,23,456 | ₹5,36,01,411 | ₹6,25,24,867 | 33 | 456 |

**Status Emoji Indicators:**
- 🚀 **>20%**: Exceptional performance
- 📈 **15-20%**: Strong performance
- ✅ **10-15%**: Good performance
- ➡️ **0-10%**: Solid/Modest performance
- 📉 **<0%**: Negative performance

**Color Coding:**
- **Dark Green** (>20%): 🚀 Exceptional
- **Forest Green** (15-20%): 📈 Strong
- **Lime Green** (10-15%): ✅ Good
- **Light Green** (5-10%): Solid
- **Light Yellow** (0-5%): Modest
- **Light Red** (<0%): Negative

#### Year-over-Year Changes Table

Compares XIRR performance between consecutive years:

| Trend | Period | Previous XIRR | Current XIRR | Change | Invested Change | Value Change |
|-------|--------|---------------|--------------|--------|-----------------|--------------|
| 📈 | 2023 → 2024 | 6.77% | 15.68% | **+8.91%** | +₹6,48,12,976 | +₹2,18,50,297 |
| 📉 | 2024 → 2025 | 15.68% | 10.62% | **-5.06%** | +₹5,03,74,813 | +₹1,67,56,987 |

**Trend Indicators:**
- 📈 Green rows: Positive XIRR improvement
- 📉 Red rows: XIRR decline

#### Download Feature
- **📥 Download Raw Data (JSON)** button
- Exports complete yearly metrics including price source breakdown
- Useful for external analysis or record-keeping

#### Help Section
Expandable "ℹ️ How to interpret this data" section explaining:
- What cumulative XIRR means
- How to read year-over-year changes
- Price sources and their impact on accuracy
- How to improve data accuracy

**Understanding Cumulative XIRR:**

Each year shows **cumulative return from your FIRST investment** (e.g., Sep 13, 2021) up to that year-end.

**Example:**
- **2022: -0.00%** → Portfolio from Sep 2021 to Dec 2022 had near-zero return
- **2023: 6.77%** → Portfolio from Sep 2021 to Dec 2023 grew at 6.77% annually
- **2024: 15.68%** → Portfolio from Sep 2021 to Dec 2024 grew at 15.68% annually
- **2025: 10.62%** → Portfolio from Sep 2021 to Dec 2025 is growing at 10.62% annually

**Year-over-Year Change Example:**
- **2023 → 2024: +8.91%** → Cumulative XIRR improved significantly (strong 2024 performance)
- **2024 → 2025: -5.06%** → Cumulative XIRR declined (but still positive overall)

**Key Points:**
- ✅ NOT isolated yearly returns - cumulative from inception
- ✅ Shows portfolio trajectory over time
- ✅ Helps identify periods of strong/weak performance
- ✅ Year-over-year changes reveal performance trends

### 4. Trade Book Tab

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

## Per-Year XIRR Analysis

The **📅 Per-Year XIRR** tab provides comprehensive year-by-year analysis of your portfolio's performance, helping you understand how your investments have grown over time.

### What is Cumulative XIRR?

**Key Concept:** Each year's XIRR shows the **annualized return from your very first investment** up to that year-end, NOT an isolated yearly return.

**Think of it as:** "If I had invested all my money at once on Day 1, what would my annualized return be by the end of this year?"

**Example Interpretation:**

```
First Investment: Sep 13, 2021

Year 2022: XIRR = -0.00%
→ From Sep 2021 to Dec 2022 (1.3 years), portfolio had near-zero return

Year 2023: XIRR = 6.77%
→ From Sep 2021 to Dec 2023 (2.3 years), portfolio grew at 6.77% per year

Year 2024: XIRR = 15.68%
→ From Sep 2021 to Dec 2024 (3.3 years), portfolio grew at 15.68% per year

Year 2025: XIRR = 10.62%
→ From Sep 2021 to Dec 2025 (4.3 years), portfolio grew at 10.62% per year
```

### Why Cumulative vs Isolated Returns?

**Cumulative XIRR (What we show):**
- ✅ Industry-standard metric for portfolio performance
- ✅ Accounts for all cash flows from inception
- ✅ Considers timing of investments (when you added money)
- ✅ Shows true long-term portfolio trajectory
- ✅ Comparable across different investment periods

**Isolated Yearly Returns (Not shown):**
- ❌ Can be misleading with irregular cash flows
- ❌ Doesn't account for investment timing
- ❌ Hard to interpret when adding/removing money
- ❌ Not standard in financial industry

### Reading Year-over-Year Changes

The YoY changes table shows how your cumulative XIRR **improved or declined** between years.

**Positive Change (📈 Green):**
```
2023 → 2024: +8.91%
→ Strong 2024 performance improved overall portfolio return
→ Cumulative XIRR went from 6.77% to 15.68%
```

**Negative Change (📉 Red):**
```
2024 → 2025: -5.06%
→ 2025 underperformed, reducing overall portfolio return
→ Cumulative XIRR dropped from 15.68% to 10.62%
→ But still positive! Portfolio is still growing
```

**Important:** A negative YoY change doesn't mean you lost money! It means recent performance was lower than the historical average.

### Data Sources and Accuracy

The Per-Year XIRR tab uses **year-end snapshots** for calculations, with the following data sources:

**Priority Order for Prices:**
1. **Year_End_Price** in snapshot (most accurate)
2. **yFinance API** (historical year-end data)
3. **backupPrices.csv** (cached current prices)
4. **Book Value** (average buy price - least accurate)

**Common Warnings:**
```
⚠️ Using book value for TICKER_NAME (No Year_End_Price available)
→ XIRR calculation may be slightly underestimated
→ Generate year-end prices for better accuracy
```

**Impact on Accuracy:**
- Using **Year_End_Price**: ✅✅✅ Highly accurate
- Using **yFinance/cached**: ✅✅ Good accuracy (within 1-2%)
- Using **Book Value**: ✅ Fair accuracy (may underestimate by 3-5%)

### How to Improve Accuracy

**Regenerate Snapshots with Year-End Prices**
```bash
python3 archivesPY/generate_snapshots.py
```
This fetches actual Dec 31 closing prices for each year and updates all snapshots.

### Use Cases

**1. Performance Tracking**
- Monitor if you're meeting target returns (e.g., beating Nifty50's ~12%)
- Identify years of exceptional or poor performance
- Understand long-term portfolio trajectory

**2. Investment Strategy**
- See impact of major investments (look at "Invested Change" column)
- Correlate market events with performance changes
- Plan future investment timing

**3. Goal Planning**
- Check if current XIRR supports retirement/goal targets
- Calculate how much more to invest to reach goals
- Adjust risk based on historical volatility

**4. Comparative Analysis**
- Compare your XIRR vs market indices
- Benchmark against inflation (~6-7% in India)
- Evaluate fund manager performance (if using managed funds)

**5. Tax Planning**
- Year-end portfolio values for tax filings
- Understand gains distribution across years
- Plan harvest of gains/losses

### Technical Details

**Caching:**
- Per-Year XIRR data cached for **1 hour** (3600 seconds)
- Portfolio overview cached for **5 minutes** (300 seconds)
- Use refresh buttons to override cache when needed

**Data Files Used:**
- `archivesCSV/cashflows_snapshot_YYYY.json` - Cash flow data per year
- `archivesCSV/holdings_snapshot_YYYY.csv` - Year-end holdings with prices
- `archivesCSV/backupPrices.csv` - Cached current prices (fallback)

**Calculation Method:**
- Uses `pyxirr` library (same as portfolio overview)
- FIFO (First In, First Out) for cost basis
- Considers all cash flows: BUYs, SELLs, dividends (if tracked)
- Year-end portfolio value treated as final cash inflow

**Functions:**
- `calculate_xirr_per_year()` in `portfolio_calculator.py` (line 1146)
- `load_yearly_xirr_data()` in `performanceDashboard.py` (cached wrapper)
- `format_yearly_xirr_report()` for console output

### Tips for Best Results

**1. Regular Snapshot Updates**
```bash
# Run quarterly or after major market movements
python3 archivesPY/generate_snapshots.py
```

**2. Price Accuracy**
- Ensure tickers in tradebook match Yahoo Finance format
- Use `.NS` suffix for NSE stocks (e.g., `RELIANCE.NS`)
- US stocks need no suffix (e.g., `AAPL`)

**3. Data Validation**
- Review year-by-year breakdown for anomalies
- Check if "Holdings" count makes sense for each year
- Verify "Total Invested" increases logically over time

**4. Understanding Trends**
- Look for consistent XIRR growth (📈 good sign)
- Investigate sudden drops (may indicate market correction)
- Compare with major market events (COVID crash, bull runs)

**5. Export for Analysis**
- Use "📥 Download Raw Data (JSON)" button
- Import into Excel/Python for custom analysis
- Track XIRR changes over multiple dashboard runs

### Limitations and Considerations

**⚠️ Important to Know:**

1. **Cumulative Nature**
   - Not isolated yearly returns
   - Later years include all previous performance
   - A bad year affects all future cumulative XIRRs

2. **Data Dependencies**
   - Accuracy depends on price data quality
   - Missing Year_End_Price uses fallbacks (less accurate)
   - Book values underestimate returns

3. **Timing Effects**
   - Large investments in down markets improve XIRR
   - Large investments in up markets may reduce XIRR
   - Year-end cutoff is Dec 31 (not customizable)

4. **Snapshot Limitations**
   - Shows only holdings held at year-end
   - Doesn't show intra-year trades that were closed
   - Realized profits from SELLs included in returns

5. **Comparison Context**
   - Your XIRR depends on when you invested
   - Can't directly compare with others' XIRRs
   - Market index returns may differ based on timing

### Dashboard Layout

```
📊 SV's Stock Portfolio
┌─────────────────────────────────────────────────────────────┐
│  Total Invested | Current Value | Unrealized P&L | XIRR ... │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  📈 Portfolio Overview | 📅 Per-Year XIRR | 📖 Trade Book   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Per-Year XIRR Tab]                                         │
│                                                               │
│  📊 Cumulative XIRR Summary                                  │
│  ┌────────────────────────────────────────────────┐         │
│  │ Current XIRR | Total Invested | Portfolio Value│         │
│  │ 10.62% (+10.62 since inception) | ₹14.14 Cr    │         │
│  └────────────────────────────────────────────────┘         │
│                                                               │
│  📈 Year-by-Year Breakdown                                   │
│  [Color-coded table: 2022, 2023, 2024, 2025]                │
│  [Status emojis: 🚀📈✅➡️📉]                                 │
│                                                               │
│  📊 Year-over-Year XIRR Changes                              │
│  [Trend table: 2023→2024 (+8.91%), 2024→2025 (-5.06%)]    │
│                                                               │
│  📥 Download Raw Data (JSON)                                 │
│  ℹ️ How to interpret this data [expandable]                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

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

### Cache Duration

**Portfolio Overview Tab:**
- **Cache TTL**: 5 minutes (300 seconds)
- **What's cached**: Price data, holdings calculation, metrics
- **When to refresh**: After market hours or significant movements

**Per-Year XIRR Tab:**
- **Cache TTL**: 1 hour (3600 seconds)
- **What's cached**: Yearly XIRR calculations, year-end snapshots
- **When to refresh**: After regenerating snapshots or fetching historical prices

**Trade Book Tab:**
- **Cache**: None (reads directly from tradebook.csv)
- **Updates**: Real-time when tradebook changes

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
python3 archivesPY/generate_snapshots.py
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
python3 archivesPY/generate_snapshots.py

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
