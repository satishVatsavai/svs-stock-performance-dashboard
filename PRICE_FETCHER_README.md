# price_fetcher.py - Quick Reference

## Purpose
Centralized module for fetching stock/mutual fund prices with smart caching and fallback mechanisms.

## Quick Start

```python
from price_fetcher import fetch_price_with_fallback

# Fetch a single price
price, name, prev_close, source = fetch_price_with_fallback('AAPL', is_sgb=False)

if source == 'yfinance':
    print(f"✅ Fresh price: ₹{price}")
elif source == 'cached':
    print(f"💾 Using cached: ₹{price}")
elif source == 'unavailable':
    print(f"❌ Not available")
```

## Main Functions

### `fetch_price_with_fallback(ticker, is_sgb=False, backup_csv_path=BACKUP_PRICES_FILE)`
**The main function you should use for fetching prices.**

**Returns:** `(price, company_name, previous_close, source)`
- `price` - Current price (float) or None
- `company_name` - Company name or ticker
- `previous_close` - Previous close price (float) or None
- `source` - One of: `'yfinance'`, `'nse'`, `'cached'`, `'unavailable'`

**Logic:**
1. Try fetching from API (yfinance or NSE)
2. If successful → Log ✅, save to cache, return
3. If failed → Try cache, log 💾, return
4. If not in cache → Log ❌, return None

**Example:**
```python
price, name, prev, source = fetch_price_with_fallback('AAPL', is_sgb=False)
# ✅ Fetched AAPL from yfinance: ₹150.25
# 💾 Backup prices: Updated 1, Added 0 to archivesCSV/backupPrices.csv
```

### `load_backup_prices(backup_csv_path=BACKUP_PRICES_FILE)`
Load cached prices from CSV.

**Returns:** `(current_prices_dict, previous_prices_dict)`
- `current_prices_dict` - Most recent price for each ticker
- `previous_prices_dict` - Second most recent price (for daily change)

**Example:**
```python
current, previous = load_backup_prices()
# 📋 Loaded 36 prices from archivesCSV/backupPrices.csv
# current = {'AAPL': 150.25, 'GOOGL': 145.50, ...}
# previous = {'AAPL': 149.80, 'GOOGL': 145.00, ...}
```

### `save_backup_prices(prices_dict, backup_csv_path=BACKUP_PRICES_FILE)`
Save/update prices to CSV (automatically handles duplicates).

**Parameters:**
- `prices_dict` - Dictionary of {ticker: price}

**Behavior:**
- If Ticker-Date exists → UPDATE the price
- If Ticker-Date doesn't exist → CREATE new record

**Example:**
```python
save_backup_prices({'AAPL': 150.25, 'GOOGL': 145.50})
# 💾 Backup prices: Updated 1, Added 1 to archivesCSV/backupPrices.csv
```

### `fetch_price_from_yfinance(ticker)`
Direct Yahoo Finance API call (use `fetch_price_with_fallback` instead for most cases).

**Returns:** `(price, company_name, previous_close)`
- Returns `'RATE_LIMITED'` as price if rate limit hit

**Example:**
```python
price, name, prev = fetch_price_from_yfinance('AAPL')
if price == 'RATE_LIMITED':
    print("Rate limit hit!")
elif price:
    print(f"Got price: {price}")
```

### `fetch_sgb_price(ticker)`
Fetch SGB price from NSE API.

**Returns:** `price` (float) or None

**Example:**
```python
price = fetch_sgb_price('SGBSEP29VI')
# ✅ Fetched SGBSEP29VI (SGB) from NSE: ₹14599.00
```

### `fetch_historical_price(ticker, target_date, is_sgb=False)`
Fetch historical price for a specific date (used for snapshots).

**Returns:** `(price, source)`

**Example:**
```python
price, source = fetch_historical_price('AAPL', '2025-12-31', is_sgb=False)
# ✅ Fetched historical price for AAPL on 2025-12-31: ₹150.25
```

## Logging

All functions produce clear logs:

| Log | Meaning |
|-----|---------|
| `✅ Fetched {ticker} from yfinance: ₹{price}` | Successfully fetched from API |
| `✅ Fetched {ticker} (SGB) from NSE: ₹{price}` | Successfully fetched SGB from NSE |
| `💾 Using cached price for {ticker}: ₹{price}` | Using cached price (API failed) |
| `❌ ERROR: Could not fetch {ticker}...` | Not available in API or cache |
| `📋 Loaded {n} prices from {file}` | Loaded cache file |
| `💾 Backup prices: Updated {n}, Added {m}...` | Saved to cache |

## Constants

```python
BACKUP_PRICES_FILE = 'archivesCSV/backupPrices.csv'
```

## CSV Format

```csv
Ticker,Date,Closing Price
AAPL,2026-01-02,150.25
GOOGL,2026-01-02,145.50
SGBSEP29VI,2026-01-02,14599.00
```

## Integration Examples

### In portfolio_calculator.py
```python
from price_fetcher import fetch_price_with_fallback, load_backup_prices

def get_market_data(df, currently_held_tickers):
    for ticker in currently_held_tickers:
        is_sgb = df[df['Ticker'] == ticker]['Is_SGB'].iloc[0]
        price, name, prev, source = fetch_price_with_fallback(ticker, is_sgb)
        # ... use price, name, prev, source
```

### In generate_snapshots.py
```python
from price_fetcher import fetch_historical_price

def generate_snapshot(year):
    target_date = f"{year}-12-31"
    for ticker in tickers:
        price, source = fetch_historical_price(ticker, target_date, is_sgb)
        # ... use price
```

### In custom scripts
```python
from price_fetcher import fetch_price_with_fallback

def check_portfolio_value():
    tickers = ['AAPL', 'GOOGL', 'MSFT']
    total = 0
    
    for ticker in tickers:
        price, _, _, source = fetch_price_with_fallback(ticker)
        if price:
            total += price * get_quantity(ticker)
    
    return total
```

## Error Handling

The module handles errors gracefully:

1. **Rate Limits**: Automatically falls back to cache
2. **Network Errors**: Falls back to cache
3. **Invalid Tickers**: Returns None with error log
4. **Missing Cache**: Returns None with error log

You don't need try-except blocks when using `fetch_price_with_fallback()` - it handles everything internally.

## Testing

Run the test suite:
```bash
python3 test_price_fetcher.py
```

## Dependencies

- `pandas` - CSV operations
- `yfinance` - Yahoo Finance API
- `requests` - NSE API calls
- Python standard library (os, warnings, logging, datetime)

## Performance

- **Cache Loading**: O(n) where n = number of cached prices
- **Single Fetch**: ~1-2 seconds per ticker (API dependent)
- **Cache Fallback**: Instant (no API call)
- **Save**: O(n) where n = number of cached prices (CSV rewrite)

## Best Practices

1. ✅ **Always use `fetch_price_with_fallback()`** for current prices
2. ✅ **Let the module handle caching** - don't manually manage backupPrices.csv
3. ✅ **Check the source** returned to know if price is fresh or cached
4. ✅ **Use historical fetch** only for snapshots, not current prices
5. ❌ **Don't call `fetch_price_from_yfinance()` directly** unless you need specific behavior

## Troubleshooting

**Q: Prices are always cached?**  
A: Yahoo Finance has rate limits. This is expected and the cache is working correctly.

**Q: Price is None?**  
A: Ticker might be invalid or not in cache yet. Check logs for details.

**Q: Want to force fresh fetch?**  
A: Delete `archivesCSV/backupPrices.csv` (backup first!) or wait for rate limits to reset.

**Q: Cache file corrupted?**  
A: Delete it - the module will recreate it on next successful fetch.
