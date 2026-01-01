# Adding New Trades - Quick Guide

## Workflow for 2026 Trades (Current Year)

When you add new trades to your 2026 CSV files, follow these simple steps:

### 📝 Step 1: Add Your Trades

Edit the appropriate CSV file in `archivesCSV/`:
- **Equity trades**: `trades2026EquityKite.csv`
- **MF trades**: `trades2026MFsCoin.csv`
- **US trades**: `trades2026SVsUS.csv` or `trades2026AnushasUS.csv`

Add new rows with your trade data and save the file.

### 🔄 Step 2: Process New Trades

```bash
cd archivesCSV
python3 ../archivesPY/tradebook_builder.py consolidate
```

**What happens:**
- ✅ System detects **only the new trades** you added
- ✅ Adds them to `archivesCSV/tradebook.csv`
- ✅ Updates `tradebook_processed_files.json` to track what's processed
- ✅ Fast operation (no API calls, takes seconds)

**Example output:**
```
📊 Processing Summary:
   • Found 14 trade files
   • Total trades in tradebook.csv: 4,895 (+4 new)
   • New trades added from:
     - trades2026EquityKite.csv: 4 trades
```

### 📊 Step 3: View Updated Dashboard

```bash
streamlit run performanceDashboard.py
```

**Dashboard automatically:**
- ✅ Loads from `archivesCSV/tradebook.csv`
- ✅ Shows your updated 2026 holdings
- ✅ Calculates current P&L, XIRR with latest prices
- ✅ Fetches current prices from yfinance on demand

---

## 💡 Key Points

### No Snapshot Needed for Current Year
- Snapshots are only for **historical years** (2022-2025)
- For 2026 (current year), the dashboard uses all trades directly
- This ensures you always see up-to-date holdings and prices

### Incremental Processing
- System remembers what's already processed in `tradebook_processed_files.json`
- Only **new trades** are added each time you run consolidate
- Safe to run multiple times - won't create duplicates

### Fast Operation
- Processing new trades is fast (seconds, not minutes)
- No API calls during consolidation (uses trade data only)
- yfinance is called only when you view the dashboard (for current prices)

---

## 🔍 Verification

After processing, you can verify:

```bash
# Check trade count
wc -l archivesCSV/tradebook.csv

# View your latest 2026 trades
grep "2026" archivesCSV/tradebook.csv | tail -10

# Check what files have been processed
cat archivesCSV/tradebook_processed_files.json
```

---

## 🚨 Troubleshooting

### "No new trades found"
- Normal if you haven't added any new trades
- System has already processed everything in the CSV files

### "Tradebook not found"
- Run: `cd archivesCSV && python3 ../archivesPY/tradebook_builder.py rebuild`
- Or use: `python3 rebuild_all.py` (from root directory)

### Want to Start Fresh?
If you need to rebuild everything from scratch:

```bash
python3 rebuild_all.py
```

This will:
1. Delete tradebook and tracking files
2. Rebuild tradebook from ALL CSV files
3. Regenerate all snapshots (2022-2025)

---

## 📚 Related Guides

- **Trade Processing Details**: See `TRADES_AND_PROCESSING_GUIDE.md`
- **Dashboard Usage**: See `PORTFOLIO_DASHBOARD_GUIDE.md`
- **Complete Rebuild**: See `README.md` → "Complete Rebuild (When Needed)"
