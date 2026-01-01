# Price Caching System

## Overview
The portfolio calculator uses a centralized **`price_fetcher.py`** module that intelligently fetches and caches prices in `archivesCSV/backupPrices.csv` to handle Yahoo Finance rate limits efficiently. When API calls fail (429 rate limit), the system automatically uses cached prices.

## Architecture

### Centralized Price Fetching Module: `price_fetcher.py`

All price fetching logic is now centralized in a single module with clear separation of concerns:

**Key Functions:**

1. **`fetch_price_with_fallback(ticker, is_sgb, backup_csv_path)`**
   - Smart price fetching with automatic fallback mechanism
   - Returns: `(price, company_name, previous_close, source)`
   - Sources: `'yfinance'`, `'nse'`, `'cached'`, or `'unavailable'`

2. **`load_backup_prices(backup_csv_path)`**
   - Loads cached prices from CSV
   - Returns: `(current_prices_dict, previous_prices_dict)`

3. **`save_backup_prices(prices_dict, backup_csv_path)`**
   - Saves/updates prices to CSV with automatic deduplication
   - Updates existing Ticker-Date records or creates new ones

4. **`fetch_price_from_yfinance(ticker)`**
   - Direct Yahoo Finance API call
   - Returns: `(price, company_name, previous_close)` or `'RATE_LIMITED'`

5. **`fetch_sgb_price(ticker)`**
   - Fetches SGB prices from NSE API
   - Returns: `price` or `None`

6. **`fetch_historical_price(ticker, target_date, is_sgb)`**
   - Fetches historical prices for snapshot generation
   - Returns: `(price, source)`

### How Other Files Use It

**`portfolio_calculator.py`** - Main dashboard calculations
```python
from price_fetcher import (
    fetch_price_with_fallback,
    load_backup_prices,
    save_backup_prices,
    fetch_sgb_price
)

# In get_market_data():
price, company_name, prev_close, source = fetch_price_with_fallback(ticker, is_sgb)
```

**`archivesPY/generate_snapshots.py`** - Year-end snapshots
```python
from price_fetcher import fetch_historical_price, fetch_sgb_price

price, source = fetch_historical_price(ticker, target_date, is_sgb)
```

## CSV Structure
**New 3-column format (with date tracking):**
```csv
Ticker,Date,Closing Price
SGBSEP29VI,2026-01-02,14599.0
QQQM,2026-01-02,252.92
VOO,2026-01-02,627.13
ANGELONE.NS,2026-01-02,2362.8
```

The system automatically handles old 2-column format (`Ticker,Current Price`) and migrates it to the new format.

## How It Works

### Smart Fetching Logic (Unified Across All Files)

1. **Try API First**
   - Yahoo Finance for equities/MFs
   - NSE API for SGBs (Sovereign Gold Bonds)
   
2. **If Fetch Successful**
   - ✅ Log success message: `"Fetched {ticker} from yfinance: ₹{price}"`
   - 💾 Automatically save to `backupPrices.csv`
   - If Ticker-Date exists: UPDATE the price
   - If not exists: CREATE new record
   
3. **If Fetch Fails (Rate Limited/Error)**
   - 💾 Try loading from `backupPrices.csv`
   - If found: Log `"Using cached price for {ticker}: ₹{price}"`
   
4. **If Not in Cache**
   - ❌ Log error: `"Could not fetch {ticker} and no backup price available"`
   - Return `None` (marked as NaN in portfolio)

### Logging Examples

**Successful Fetch:**
```
✅ Fetched AAPL from yfinance: ₹150.25
💾 Backup prices: Updated 1, Added 0 to archivesCSV/backupPrices.csv
```

**Rate Limited, Using Cache:**
```
💾 Using cached price for GOOGL (rate limited): ₹145.50
```

**Error - Not Available:**
```
❌ ERROR: Could not fetch INVALID.NS from yfinance and no backup price available
```

## Price Source Logging

Every portfolio calculation shows where each price came from:

| Icon | Source | Meaning |
|------|--------|---------|
| ✅ | Yahoo Finance | Fetched fresh from yfinance API |
| ✅ | NSE API (SGBs) | Fetched fresh from NSE (Sovereign Gold Bonds) |
| 💾 | Cached | Loaded from archivesCSV/backupPrices.csv (rate limit fallback) |
| ❌ | Not Available | Not found in API or cache (marked as NaN) |

### Example Output

**Scenario 1: Heavy Rate Limiting (typical)**
```
📊 PRICE SOURCE SUMMARY
----------------------------------------------------------------------
✅ NSE API (SGBs): 1/36 tickers
   • SGBSEP29VI
💾 Cached (archivesCSV/backupPrices.csv): 35/36 tickers
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

## Benefits

✅ **Centralized**: All price fetching logic in one module (`price_fetcher.py`)  
✅ **Resilient**: Works despite rate limits (429 errors)  
✅ **Automatic**: Saves on successful fetch, updates or creates records intelligently  
✅ **Transparent**: See exactly where each price came from with detailed logging  
✅ **Simple**: Easy to understand CSV format with date tracking  
✅ **Incremental**: Each successful fetch updates the cache  
✅ **DRY**: No code duplication across files  

## Usage

### In Your Own Scripts

```python
from price_fetcher import fetch_price_with_fallback

# Fetch a single price with smart fallback
price, company_name, prev_close, source = fetch_price_with_fallback(
    ticker='AAPL',
    is_sgb=False
)

if source == 'yfinance':
    print(f"Got fresh price: {price}")
elif source == 'cached':
    print(f"Using cached price: {price}")
elif source == 'unavailable':
    print(f"Price not available for {ticker}")
```

### Historical Price Fetching (for snapshots)

```python
from price_fetcher import fetch_historical_price

price, source = fetch_historical_price(
    ticker='AAPL',
    target_date='2025-12-31',
    is_sgb=False
)
```

**Typical Output:**
```
📂 Loading archivesCSV/tradebook.csv...
   Loaded 4891 trades
📋 Loaded 36 prices from archivesCSV/backupPrices.csv
✅ Fetched AAPL from yfinance: ₹150.25
💾 Backup prices: Updated 1, Added 0 to archivesCSV/backupPrices.csv

📊 PRICE SOURCE SUMMARY
----------------------------------------------------------------------
✅ Yahoo Finance: 1/36 tickers
   • AAPL
✅ NSE API (SGBs): 1/36 tickers
   • SGBSEP29VI
💾 Cached (archivesCSV/backupPrices.csv): 34/36 tickers
   • INF959L01FV0, INF209KB18C5, CFLT, VOO, QQQM
   ... and 29 more
----------------------------------------------------------------------

📈 XIRR calculated: 23.89% (from 4891 transactions)
```

## Manual Editing

You can manually update prices if needed:

```bash
# Edit the CSV with any text editor
nano archivesCSV/backupPrices.csv
```

Maintain the 3-column format: `Ticker,Date,Closing Price`

## Troubleshooting

**Q: Why so many rate limits?**  
A: Yahoo Finance limits free API calls. The cache handles this gracefully.

**Q: Are cached prices stale?**  
A: System tries fresh fetches first. Cache is only used when API fails.

**Q: Should I delete the cache?**  
A: No need. Fresh fetches update it automatically. Delete only if prices seem wrong.

**Q: How to force fresh fetches?**  
A: Just run again later - Yahoo Finance rate limits reset periodically.

**Q: Where is the price fetching code?**  
A: All centralized in `price_fetcher.py` module. Other files import from there.

**Q: Can I add my own price source?**  
A: Yes! Add your fetching function to `price_fetcher.py` and update `fetch_price_with_fallback()` to try your source.
