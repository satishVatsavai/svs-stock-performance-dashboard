# Trade Processing and Portfolio Setup Guide

Complete guide for managing trade files, building tradebook, creating holdings snapshots, and maintaining your portfolio data.

## Table of Contents
- [Quick Start](#quick-start)
- [Trade File Management](#trade-file-management)
- [Building Tradebook](#building-tradebook)
- [Holdings Snapshots](#holdings-snapshots)
- [Adding New Trades](#adding-new-trades)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Daily Workflow

1. **Add trades** to CSV files in `archivesCSV/`
2. **Consolidate tradebook**: `python3 archivesPY/tradebook_builder.py consolidate`
3. **View dashboard**: `streamlit run performanceDashboard.py`

### Annual Maintenance (Once Per Year)

On January 1st of each new year:
```bash
python3 archivesPY/generate_snapshots.py single 2026
```

---

## Trade File Management

### File Location
All trade CSV files should be placed in the `archivesCSV/` directory.

### File Naming Patterns

**By Source (Recommended):**
```
trades2026EquityKite.csv    # Equity trades from Kite
trades2026MFsCoin.csv       # Mutual fund trades from Coin
trades2026SVsUS.csv         # Your US stock trades
trades2026AnushasUS.csv     # Partner's US stock trades
```

**By Quarter:**
```
trades2026Q1.csv    # Jan-Mar
trades2026Q2.csv    # Apr-Jun
trades2026Q3.csv    # Jul-Sep
trades2026Q4.csv    # Oct-Dec
```

**By Month:**
```
trades2026-01.csv    # January
trades2026-02.csv    # February
...
trades2026-12.csv    # December
```

### CSV File Format

**Required Columns:**
```csv
Date,Ticker,Type,Qty,Price,Currency,Is_SGB
2026-01-15,AAPL,BUY,10,230.50,USD,FALSE
2026-01-20,INFY.NS,BUY,50,1850.00,INR,FALSE
2026-01-25,RELIANCE.NS,SELL,25,2650.00,INR,FALSE
```

**Column Details:**
- **Date**: YYYY-MM-DD format
- **Ticker**: Stock symbol (e.g., `AAPL`, `RELIANCE.NS`, `INFY.NS`)
- **Type**: `BUY` or `SELL`
- **Qty**: Quantity (number of shares)
- **Price**: Price per share
- **Currency**: `USD` or `INR`
- **Is_SGB**: `TRUE` for Sovereign Gold Bonds, `FALSE` for stocks

**Special File: SGBs.csv**
For Sovereign Gold Bonds, additional columns are required:
```csv
Date,Ticker,Country,Type,Qty,Price,Currency,Issue Date,Maturity Date,Series
```

---

## Building Tradebook

The tradebook consolidates all your trades from multiple CSV files into a single `tradebook.csv` file used by the dashboard.

### Commands

#### 1. Consolidate (Most Common)
```bash
cd archivesCSV
python3 ../archivesPY/tradebook_builder.py consolidate
```

**What it does:**
- Scans for new or modified CSV files
- Adds only new trades to `tradebook.csv`
- Updates processing history in `tradebook_processed_files.json`
- Smart: Only processes files that have changed

**Example Output:**
```
📂 Scanning for trade files...
Found 5 trade files

📊 Processing trade files...
✅ trades2026EquityKite.csv: 4 new records
✅ trades2025EquityKite.csv: already processed (unchanged)

💾 Saving consolidated tradebook...
✅ Tradebook updated: 4,894 total records
```

#### 2. Status (Check Current State)
```bash
python3 tradebook_builder.py status
```

**What it shows:**
- Total trades in `tradebook.csv`
- List of all processed files with record counts
- Last modification times
- Helps verify what's been processed

#### 3. Rebuild (Use with Caution)
```bash
python3 tradebook_builder.py rebuild
```

**What it does:**
- Deletes `tradebook_processed_files.json`
- Rebuilds `tradebook.csv` from scratch
- Processes all trade files again

**⚠️ Use only when:**
- Tradebook is corrupted
- Need to completely reset processing history
- Restructuring your trade files

#### 4. Complete Rebuild (Recommended for Full Reset)
```bash
python3 rebuild_all.py
```

**What it does:**
1. Deletes tradebook and processing history
2. Rebuilds tradebook from all CSV files
3. Deletes all holdings snapshots
4. Regenerates all snapshots (2022-2025)

**✨ Features:**
- ✅ Interactive confirmation prompt
- ✅ Shows what will be processed
- ✅ No API calls (uses historical data only)
- ✅ Fast operation (completes in seconds)
- ✅ Safe: Source CSV files never touched
- ✅ Complete data validation

**Use when:**
- After fixing historical trade errors
- For periodic data validation
- When you want to start completely fresh
- After major corrections to source CSV files

**Example Output:**
```
✅ Found 14 trade file(s) to process
⚠️  WARNING: This will:
   1. Delete tradebook.csv and tradebook_processed_files.json
   2. Rebuild tradebook from scratch (all CSV files)
   3. Delete all holdings_snapshot_*.csv files
   4. Regenerate all snapshots from tradebook

   Continue? (yes/no): yes

✅ REBUILD COMPLETE!
📊 Summary:
   Tradebook: 4,891 trades
   Snapshots: 4 files created
```

### Exchange Rates

The builder automatically:
- Fetches historical USD/INR exchange rates for each trade date
- Stores rates in the tradebook
- Uses Yahoo Finance API with fallback to exchangerate-api.com
- Caches rates to avoid redundant API calls

---

## Holdings Snapshots

### What Are Snapshots?

Snapshots capture your portfolio state at the end of each year, dramatically speeding up calculations.

**Performance Benefits:**
- **Before**: Process 4,887 trades every time (~45-60 seconds)
- **After**: Load 2025 snapshot + process 2026 trades only (~5-10 seconds)
- **Improvement**: 80-90% faster! 🚀

### How Snapshots Work

```
Traditional Method:
┌─────────────────┐
│ Load tradebook  │ → Process 4,887 trades → Calculate → Display
│  (4,887 trades) │      (~45 seconds)
└─────────────────┘

Optimized Method (2026):
┌──────────────────┐
│ Load 2025        │ → Process 60 trades → Calculate → Display
│  snapshot        │      (~5 seconds)
│  (33 holdings)   │
└──────────────────┘
```

### Snapshot Files

Snapshots are stored in `archivesCSV/`:
```
holdings_snapshot_2022.csv  (3 holdings)
holdings_snapshot_2023.csv  (117 holdings)
holdings_snapshot_2024.csv  (28 holdings)
holdings_snapshot_2025.csv  (33 holdings)
```

### Snapshot File Format

Each snapshot contains per-ticker:
```csv
Ticker,Qty,Avg_Buy_Price,Total_Invested_INR,Realized_Profit_INR,Currency,Exchange_Rate,Is_SGB
QQQM,477.52,150.67,6033852.45,25000.00,USD,83.50,False
INFY.NS,100,1450.00,145000.00,0,INR,1.0,False
```

### Creating Snapshots

#### Generate All Snapshots (2022-2025)
```bash
python3 archivesPY/generate_snapshots.py
```

#### Generate Snapshot for Specific Year
```bash
python3 archivesPY/generate_snapshots.py single 2025
```

#### Verify a Snapshot
```bash
python3 archivesPY/generate_snapshots.py verify archivesCSV/holdings_snapshot_2025.csv
```

**Example Output:**
```
📸 Generating snapshot for 2025...
   Processing 4,887 trades up to 2025-12-31
   ✅ Snapshot created: holdings_snapshot_2025.csv
   Holdings: 33 tickers
   Total Invested: ₹53,373,410.77
   Realized Profit: ₹2,500,000.00
```

### When to Regenerate Snapshots

**✅ Required:**
- End of each year (e.g., Jan 1, 2027 to create 2026 snapshot)

**✅ Optional (but recommended):**
- After fixing historical trade errors
- After major data corrections
- When verifying accuracy

**❌ Not Needed:**
- Adding new trades during current year (processed separately)
- Updating stock prices (snapshots don't store prices)
- Regular dashboard usage

---

## Adding New Trades

### The System Auto-Detects New Trades!

You don't need to tell the system about new trades. It automatically:
1. Loads the full `tradebook.csv` (including all new trades)
2. Loads the latest snapshot (e.g., 2025)
3. Filters trades by date (only keeps trades after snapshot date)
4. Processes only those filtered trades

### Real-Time Example

**Morning (Before Adding Trades):**
```bash
streamlit run performanceDashboard.py
```
Console shows:
```
📸 Loading snapshot: holdings_snapshot_2025.csv
   Snapshot date: 2025-12-31
   Holdings in snapshot: 33 tickers
📊 Processing 0 trades since 2025-12-31
   (Skipped 4,887 historical trades)
```

**Afternoon (You Add 3 New Trades):**
```bash
# 1. Add trades to CSV
cat > archivesCSV/trades2026Q1.csv << EOF
Date,Ticker,Type,Qty,Price,Currency,Is_SGB
2026-01-15,AAPL,BUY,10,230.50,USD,FALSE
2026-01-20,INFY.NS,BUY,50,1850.00,INR,FALSE
2026-01-25,META,SELL,5,585.00,USD,FALSE
EOF

# 2. Consolidate
cd archivesCSV
python3 ../archivesPY/tradebook_builder.py consolidate
```

**Evening (Open Dashboard Again):**
```bash
streamlit run performanceDashboard.py
```
Console shows:
```
📸 Loading snapshot: holdings_snapshot_2025.csv
   Snapshot date: 2025-12-31
   Holdings in snapshot: 33 tickers
📊 Processing 3 trades since 2025-12-31  ← Automatically detected!
   (Skipped 4,887 historical trades)
```

### Growth Throughout the Year

**January 2026:**
- Snapshot + 15 trades = Fast!

**June 2026:**
- Snapshot + 300 trades = Still fast!

**December 2026:**
- Snapshot + 600 trades = Still much faster than 5,000+ trades!

---

## Performance Optimization

### Automatic Optimization Features

1. **Snapshot Loading**
   - Dashboard automatically detects and uses latest snapshot
   - No configuration needed
   - Falls back to full calculation if no snapshot exists

2. **Incremental Processing**
   - Only processes trades after snapshot date
   - Maintains 80-90% speed improvement throughout the year

3. **Accuracy Preserved**
   - Uses same FIFO (First In First Out) calculation method
   - Realized profits tracked correctly
   - All metrics identical to full recalculation

### Verification

To verify snapshots are working:

**1. Check Dashboard Startup Logs:**
```
📸 Loading snapshot: holdings_snapshot_2025.csv
   Snapshot date: 2025-12-31
   Holdings in snapshot: 33 tickers
📊 Processing 15 trades since 2025-12-31
   (Skipped 4,887 historical trades)
✅ Calculation completed in 6.23 seconds
```

**2. Use Force Recalculation:**
- Click "🔄 Full Recalc" button in dashboard
- Processes full tradebook (slower but verifies accuracy)
- Compare values with normal mode - should be identical

**3. Performance Check:**
- Normal mode: ~5-10 seconds
- Full recalc mode: ~45-60 seconds
- Should see 80-90% improvement

---

## Troubleshooting

### Snapshot Issues

**Snapshot not being used:**
```bash
# Check if files exist
ls -la archivesCSV/holdings_snapshot_*.csv

# Verify filename pattern
# Should be: holdings_snapshot_YYYY.csv

# Check console for messages like "No snapshots found"
```

**Incorrect values:**
```bash
# Regenerate snapshots
python3 archivesPY/generate_snapshots.py

# Use dashboard's "Full Recalc" to compare
```

**Missing tickers:**
```bash
# Ensure tradebook has all historical trades
wc -l archivesCSV/tradebook.csv

# Check for missing trade files
ls -la archivesCSV/trades*.csv
```

### Tradebook Issues

**Trades not appearing in dashboard:**
```bash
# 1. Check if consolidation ran successfully
cd archivesCSV
python3 ../archivesPY/tradebook_builder.py status

# 2. Verify trades are in tradebook
grep "2026" tradebook.csv

# 3. Check file was processed
cat tradebook_processed_files.json
```

**Duplicate trades:**
```bash
# Rebuild from scratch
python3 tradebook_builder.py rebuild
```

**Exchange rate errors:**
```bash
# Check console output during consolidation
# Builder will show warnings if rates couldn't be fetched
# Verify dates are in YYYY-MM-DD format in CSV
```

### File Organization Issues

**Too many trade files:**
```bash
# Consolidate similar files
# For example, merge all 2025 files into one
cat trades2025*.csv > trades2025_all.csv
# Then rebuild tradebook
python3 tradebook_builder.py rebuild
```

**Lost track of processed files:**
```bash
# Check processing history
cat tradebook_processed_files.json

# Or view status
python3 tradebook_builder.py status
```

---

## Best Practices

### File Management
- ✅ Use consistent naming patterns
- ✅ Keep one file per source or quarter
- ✅ Don't modify files after consolidation (add new files instead)
- ✅ Backup your `tradebook.csv` regularly

### Snapshots
- ✅ Generate new snapshot on January 1st each year
- ✅ Verify accuracy with "Full Recalc" button
- ✅ Keep all historical snapshots (disk space is cheap)

### Workflow
- ✅ Add trades to CSV files as they happen
- ✅ Run consolidate at end of day/week
- ✅ Don't manually edit `tradebook.csv`
- ✅ Let the system handle date filtering automatically

### Performance
- ✅ Use snapshots for 80-90% speed improvement
- ✅ Organize files to minimize processing
- ✅ Verify accuracy periodically with full recalc

---

## Summary

**Core Workflow:**
```
1. Add trades to CSV files in archivesCSV/
   ↓
2. python3 tradebook_builder.py consolidate
   ↓
3. streamlit run performanceDashboard.py
   ↓
4. System automatically uses snapshot + new trades
   ↓
5. Fast, accurate portfolio calculations!
```

**Annual Maintenance:**
```
January 1st each year:
→ python3 archivesPY/generate_snapshots.py single [previous_year]
→ New snapshot ready for the new year!
```

**Key Principle:**
> The dashboard ONLY reads data. You control when and how data is updated through the tradebook builder and snapshot generator.
