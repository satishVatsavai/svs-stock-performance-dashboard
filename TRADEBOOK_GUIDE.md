# Tradebook Building Guide

## Overview

The tradebook consolidates all your trades from multiple CSV files into a single `tradebook.csv` file. This consolidated file is then used by the dashboard for portfolio calculations.

## Key Principle

**The dashboard ONLY reads the tradebook - it never modifies it.**

You have full control over when and how the tradebook is updated.

## Quick Start

```bash
# Build or update your tradebook
python3 tradebook_builder.py consolidate

# Check what's in your tradebook
python3 tradebook_builder.py status

# Rebuild from scratch (clears processing history)
python3 tradebook_builder.py rebuild
```

## How It Works

### Source Files

The builder scans for these CSV files:
- `trades*.csv` - Your equity/MF trades (e.g., `trades2025EquityKite.csv`)
- `SGBs.csv` - Sovereign Gold Bonds

### Output Files

1. **`tradebook.csv`** - Consolidated trade data with exchange rates
2. **`tradebook_processed_files.json`** - Tracks which files have been processed and their checksums

## Commands

### 1. Consolidate (Recommended)

```bash
python3 tradebook_builder.py consolidate
```

**What it does:**
- Scans for new or modified CSV files
- Adds only new trades to `tradebook.csv`
- Updates the processing history
- **Smart**: Only processes files that have changed

**Use this when:**
- Adding new trade files
- Updating existing trade files with new trades
- Regular maintenance

### 2. Status

```bash
python3 tradebook_builder.py status
```

**What it does:**
- Shows total trades in `tradebook.csv`
- Lists all processed files with their record counts
- Displays last modification times
- Helps verify what's been processed

### 3. Rebuild

```bash
python3 tradebook_builder.py rebuild
```

**What it does:**
- Deletes `tradebook_processed_files.json`
- Rebuilds `tradebook.csv` from scratch
- Processes all trade files again

**⚠️ Use with caution when:**
- Tradebook is corrupted
- Need to completely reset processing history
- Restructuring your trade files

## CSV File Format

### Required Columns

Your trade CSV files should have these columns:

```csv
Date,Ticker,Country,Type,Qty,Price,Currency
2025-01-15,AAPL,USA,BUY,10,150.00,USD
2025-01-16,RELIANCE.NS,IND,BUY,5,2450.00,INR
2025-01-17,AAPL,USA,SELL,5,155.00,USD
```

**Column Details:**
- **Date**: YYYY-MM-DD format
- **Ticker**: Stock symbol (e.g., `AAPL`, `RELIANCE.NS`)
- **Country**: `USA` or `IND` (for exchange rate conversion)
- **Type**: `BUY` or `SELL`
- **Qty**: Quantity (number of shares)
- **Price**: Price per share
- **Currency**: `USD` or `INR`

### Special: SGBs.csv

Sovereign Gold Bonds file with additional columns:
```csv
Date,Ticker,Country,Type,Qty,Price,Currency,Issue Date,Maturity Date,Series
```

## Exchange Rates

The builder automatically:
- Fetches historical USD/INR exchange rates for each trade date
- Stores rates in the tradebook
- Uses Yahoo Finance API with fallback to exchangerate-api.com
- Caches rates to avoid redundant API calls

## Workflow for Adding New Trades

### Step 1: Add Trades to CSV

Edit your existing file or create a new one:
```bash
nano trades2025EquityKite.csv
# Add your new trades
```

### Step 2: Update Tradebook

```bash
python3 tradebook_builder.py consolidate
```

Output example:
```
📂 Scanning for trade files...
Found 5 trade files

📊 Processing trade files...
✅ trades2025EquityKite.csv: 15 new records
✅ trades2024EquityKite.csv: already processed (unchanged)

💾 Saving consolidated tradebook...
✅ Tradebook updated: 127 total records

💾 Updating processing history...
✅ Processing history saved
```

### Step 3: Verify

```bash
python3 tradebook_builder.py status
```

### Step 4: Test Locally

```bash
streamlit run performanceDashboard.py
```

### Step 5: Deploy (if using Streamlit Cloud)

```bash
git add tradebook.csv tradebook_processed_files.json
git commit -m "Add trades for January 2025"
git push
```

Streamlit Cloud will automatically redeploy with the updated tradebook.

## Best Practices

### ✅ Do's

- **Keep source files organized**: Use descriptive names like `trades2025EquityKite.csv`
- **Use consolidate regularly**: It's smart and only processes changes
- **Commit both files**: Always commit `tradebook.csv` AND `tradebook_processed_files.json` together
- **Test before deploying**: Run the dashboard locally first
- **Keep backups**: Your source CSV files are your backup

### ❌ Don'ts

- **Don't edit tradebook.csv directly**: Edit your source CSV files instead
- **Don't delete processing history unnecessarily**: It prevents duplicate processing
- **Don't mix manual and automated updates**: Stick to using the builder
- **Don't commit .env files**: Keep credentials secure

## Understanding the Processing History

The `tradebook_processed_files.json` file tracks:

```json
{
  "trades2025EquityKite.csv": {
    "checksum": "a1b2c3d4...",
    "record_count": 15,
    "last_modified": "2025-01-15T10:30:00"
  }
}
```

**Purpose:**
- Prevents reprocessing unchanged files
- Detects when files are modified
- Tracks what's been consolidated

**Why it matters:**
- Makes `consolidate` fast and efficient
- Prevents accidental duplicates
- Maintains processing state

## Troubleshooting

### "No tradebook.csv found"

**Solution:** Run `python3 tradebook_builder.py consolidate` to create it

### "Duplicate records in tradebook"

**Cause:** Processing history was lost or corrupted

**Solution:**
```bash
# Option 1: Rebuild from scratch
python3 tradebook_builder.py rebuild

# Option 2: Manually remove duplicates from source files
```

**Note:** Identical trades on the same date are VALID (e.g., multiple buys), so manual review is important.

### "Exchange rate fetch failed"

**Cause:** API rate limiting or network issues

**Solution:**
- Wait a few minutes and retry
- Check internet connection
- Rates are cached, so most should succeed on retry

### "File format error"

**Cause:** Missing required columns or incorrect format

**Solution:**
- Verify CSV has all required columns
- Check date format is YYYY-MM-DD
- Ensure Type is BUY or SELL
- Verify Currency is USD or INR

## Integration with Dashboard

The dashboard (`performanceDashboard.py`) uses the tradebook like this:

```python
# Dashboard loads tradebook.csv as-is
df = pd.read_csv('tradebook.csv')

# Performs standard transformations only:
# - Uppercase Type column
# - Parse Date column
# - Calculate portfolio metrics
```

**Key points:**
- ✅ Dashboard never modifies `tradebook.csv`
- ✅ Dashboard never calls `tradebook_builder.py`
- ✅ Dashboard is read-only for trade data
- ✅ You control when tradebook is updated

## Advanced Usage

### Processing Only Specific Files

Edit `tradebook_builder.py` to customize which files to scan:

```python
def scan_trade_files():
    pattern = "trades*.csv"  # Change this pattern
    # ...
```

### Custom Exchange Rate Sources

The builder uses:
1. Yahoo Finance (primary)
2. exchangerate-api.com (fallback)

To add more sources, edit the `add_exchange_rates_to_trades()` function.

### Handling Large Portfolios

For 100+ trades:
- `consolidate` is very fast (only processes changes)
- `rebuild` may take a minute (processes everything)
- Exchange rate API calls are cached

## Quick Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `consolidate` | Add new/changed trades | Regular updates |
| `status` | View tradebook info | Check what's processed |
| `rebuild` | Start fresh | Fix corruption |

## Support

For issues or questions:
1. Check `status` output for clues
2. Verify CSV file format
3. Test locally before deploying
4. Check console output for specific errors

---

**Related Documentation:**
- `DASHBOARD_GUIDE.md` - How to use the Streamlit dashboard
- `TELEGRAM_GUIDE.md` - Setting up portfolio notifications
