# Price Caching System

## Overview
The portfolio calculator intelligently caches prices in `archivesCSV/tempCurrentPrices.csv` to handle Yahoo Finance rate limits efficiently. When API calls fail (429 rate limit), the system automatically uses cached prices.

## CSV Structure
**Simple 2-column format:**
```csv
Ticker,Current Price
SGBSEP29VI,14599.0
QQQM,252.92
VOO,627.13
ANGELONE.NS,2362.8
```

## How It Works

### Smart Fetching Logic
1. **Try API First** → Yahoo Finance (equities/MFs) or NSE API (SGBs)
2. **If Success** → Use price + save to cache automatically
3. **If Fail (429)** → Use cached price from CSV
4. **If No Cache** → Mark as NaN

## Price Source Logging

Every portfolio calculation shows where each price came from:

| Icon | Source | Meaning |
|------|--------|---------|
| ✅ | Yahoo Finance | Fetched fresh from yfinance API |
| ✅ | NSE API (SGBs) | Fetched fresh from NSE (Sovereign Gold Bonds) |
| 💾 | Cached | Loaded from archivesCSV/tempCurrentPrices.csv (rate limit fallback) |
| ❌ | Not Available | Not found in API or cache (marked as NaN) |

### Example Output

**Scenario 1: Heavy Rate Limiting (typical)**
```
📊 PRICE SOURCE SUMMARY
----------------------------------------------------------------------
✅ NSE API (SGBs): 1/36 tickers
   • SGBSEP29VI
💾 Cached (archivesCSV/tempCurrentPrices.csv): 35/36 tickers
   • INF959L01FV0, INF209KB18C5, CFLT, VOO, QQQM
   ... and 30 more
⚠️  Yahoo Finance rate limit hit 35 times
----------------------------------------------------------------------
```
**This is normal!** The 💾 cached fallback is working as designed.

**Scenario 2: All Fresh Fetches (rare but ideal)**
```
📊 PRICE SOURCE SUMMARY
----------------------------------------------------------------------
✅ Yahoo Finance: 35/36 tickers
   • AAPL, GOOGL, MSFT, TSLA, META ... and 30 more
✅ NSE API (SGBs): 1/36 tickers
   • SGBSEP29VI
----------------------------------------------------------------------
```

**Scenario 3: Some Unavailable**
```
📊 PRICE SOURCE SUMMARY
----------------------------------------------------------------------
✅ Yahoo Finance: 30/36 tickers
💾 Cached: 3/36 tickers
❌ Not Available: 3/36 tickers
   • INVALID.NS, NOTFOUND.NS, MISSING.NS
----------------------------------------------------------------------
```
Invalid tickers will show as NaN in portfolio.

## Key Functions

```python
# Load cached prices (automatically called)
prices = load_temp_prices()  # Returns: {'AAPL': 150.0, 'GOOGL': 145.5}

# Save prices (automatically called after fetching)
save_temp_prices({'AAPL': 150.25})  # Merges with existing, maintains sorted order

# Fetch with auto-caching and logging
market_data, names, prev_close = get_market_data(df, tickers)
```

## Benefits

✅ **Resilient**: Works despite rate limits (429 errors)  
✅ **Automatic**: No manual saves or loads needed  
✅ **Transparent**: See exactly where each price came from  
✅ **Simple**: Just 2 columns, easy to edit manually  
✅ **Incremental**: Each successful fetch updates the cache  

## Usage

```python
from portfolio_calculator import calculate_portfolio_summary

# Automatically handles caching and logging
summary = calculate_portfolio_summary()
```

**Typical Output:**
```
📂 Loading archivesCSV/tradebook.csv...
   Loaded 4891 trades
📋 Loaded 36 prices from archivesCSV/tempCurrentPrices.csv
💾 Saved 1 new/updated prices to archivesCSV/tempCurrentPrices.csv

📊 PRICE SOURCE SUMMARY
----------------------------------------------------------------------
✅ NSE API (SGBs): 1/36 tickers
💾 Cached (archivesCSV/tempCurrentPrices.csv): 35/36 tickers
⚠️  Yahoo Finance rate limit hit 35 times
----------------------------------------------------------------------

📈 XIRR calculated: 23.89% (from 4891 transactions)
```

## Manual Editing

You can manually update prices if needed:

```bash
# Edit the CSV with any text editor
nano archivesCSV/tempCurrentPrices.csv
```

Just maintain the 2-column format with `Ticker,Current Price` header.

## Troubleshooting

**Q: Why so many rate limits?**  
A: Yahoo Finance limits free API calls. The cache handles this gracefully.

**Q: Are cached prices stale?**  
A: System tries fresh fetches first. Cache is only used when API fails.

**Q: Should I delete the cache?**  
A: No need. Fresh fetches update it automatically. Delete only if prices seem wrong.

**Q: How to force fresh fetches?**  
A: Just run again later - Yahoo Finance rate limits reset periodically.
