#!/usr/bin/env python3
"""
Tradebook Builder - Consolidated Trade Management System

This module consolidates all tradebook management functionality including:
- Trade file parsing and consolidation
- Exchange rate caching
- SGB price caching
- CLI management commands

Usage:
  python3 tradebook_builder.py [command]

Commands:
  status      - Show current tradebook and cache status (default)
  consolidate - Build/update tradebook from source files
  rebuild     - Force rebuild the entire tradebook
  clear       - Clear tradebook and metadata files
  sgb-status  - Show SGB price cache status
  sgb-clear   - Clear SGB price cache
  help        - Show help message

As a module:
  from tradebook_builder import load_or_create_tradebook, get_sgb_price_cached
"""

import pandas as pd
import json
import os
import glob
import yfinance as yf
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import time

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

# Determine the working directory - always use archivesCSV
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'archivesCSV')

# Ensure working directory exists
if not os.path.exists(WORKING_DIR):
    print(f"❌ Error: archivesCSV directory not found at {WORKING_DIR}")
    exit(1)

TRADEBOOK_FILE = os.path.join(WORKING_DIR, 'tradebook.csv')
PROCESSED_FILES_METADATA = os.path.join(WORKING_DIR, 'tradebook_processed_files.json')
SGB_PRICE_CACHE_FILE = os.path.join(WORKING_DIR, 'sgb_price_cache.json')
CACHE_VALIDITY_HOURS = 6
FALLBACK_USD_INR_RATE = float(os.getenv('FALLBACK_USD_INR_RATE', '90.0'))

# Global cache for exchange rates during current session
_exchange_rate_session_cache = {}


# ============================================================================
# TRADEBOOK MANAGEMENT
# ============================================================================

def get_trade_files():
    """Get all trade CSV files in the archivesCSV directory"""
    trade_files = glob.glob(os.path.join(WORKING_DIR, 'trades*.csv')) + glob.glob(os.path.join(WORKING_DIR, 'SGBs.csv'))
    return [f for f in trade_files if os.path.isfile(f)]


def load_processed_files_metadata():
    """Load metadata about which files have been processed"""
    if os.path.exists(PROCESSED_FILES_METADATA):
        try:
            with open(PROCESSED_FILES_METADATA, 'r') as f:
                metadata = json.load(f)
                
                # Convert old formats to new simplified format if needed
                converted = {}
                for filename, value in metadata.items():
                    if isinstance(value, (int, float)):
                        # Old format: Unix timestamp - convert to ISO string
                        converted[filename] = datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(value, dict):
                        # Dict format with both timestamp and modified_time - extract modified_time
                        converted[filename] = value.get('modified_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    elif isinstance(value, str):
                        # New format: already a string
                        converted[filename] = value
                    else:
                        # Unexpected format - skip
                        continue
                
                return converted
        except json.JSONDecodeError:
            print(f"⚠️ Warning: Could not read {PROCESSED_FILES_METADATA}, starting fresh")
            return {}
    return {}


def save_processed_files_metadata(metadata):
    """Save metadata about processed files in human-readable format"""
    with open(PROCESSED_FILES_METADATA, 'w') as f:
        json.dump(metadata, f, indent=2, sort_keys=True)


def get_file_modification_time(filepath):
    """Get the modification time of a file as a timestamp"""
    return os.path.getmtime(filepath)


def get_file_modification_time_string(filepath):
    """Get file modification time as a human-readable string"""
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')


def identify_new_or_modified_files(trade_files, metadata):
    """Identify which files are new or have been modified since last processing"""
    new_or_modified = []
    
    for filepath in trade_files:
        # Use basename for metadata key to ensure consistency
        file_key = os.path.basename(filepath)
        current_mtime = get_file_modification_time(filepath)
        
        # Get stored timestamp string and convert to Unix timestamp for comparison
        if file_key in metadata:
            stored_time_str = metadata[file_key]
            try:
                # Parse the stored time string to Unix timestamp
                stored_dt = datetime.strptime(stored_time_str, '%Y-%m-%d %H:%M:%S')
                processed_mtime = stored_dt.timestamp()
            except (ValueError, AttributeError):
                # If parsing fails, treat as not processed
                processed_mtime = 0
        else:
            processed_mtime = 0
        
        if current_mtime > processed_mtime:
            new_or_modified.append(filepath)
    
    return new_or_modified


def parse_trade_file(filepath):
    """Parse a single trade file and return a DataFrame"""
    try:
        df = pd.read_csv(filepath)
        
        # Add source file column using basename only
        df['Source_File'] = os.path.basename(filepath)
        
        # Detect if it's an SGB file
        is_sgb = 'SGB' in filepath or (
            'Ticker' in df.columns and 
            df['Ticker'].astype(str).str.contains('SGB', na=False).any()
        )
        df['Is_SGB'] = is_sgb
        
        return df
    except Exception as e:
        print(f"⚠️ Error parsing {filepath}: {e}")
        return None


def get_exchange_rate(currency, trade_date):
    """
    Get exchange rate for a given currency and date.
    Returns 1.0 for INR, fetches rate for USD and other currencies.
    
    Data sources (in order of preference):
    1. Yahoo Finance
    2. exchangerate-api.com (current rate as fallback)
    3. Environment variable FALLBACK_USD_INR_RATE (last resort)
    """
    if currency == 'INR':
        return 1.0
    
    if currency == 'USD':
        import sys
        from io import StringIO
        
        # Check session cache first
        cache_key = f"{currency}_{trade_date}"
        if cache_key in _exchange_rate_session_cache:
            return _exchange_rate_session_cache[cache_key]
        
        # Check if we already have a fallback rate cached for this currency
        fallback_key = f"{currency}_fallback"
        if fallback_key in _exchange_rate_session_cache:
            rate = _exchange_rate_session_cache[fallback_key]
            _exchange_rate_session_cache[cache_key] = rate
            return rate
        
        # Try Yahoo Finance first with multiple ticker formats (suppress output)
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        
        try:
            # Convert trade_date to datetime if it's a string
            if isinstance(trade_date, str):
                date_obj = pd.to_datetime(trade_date)
            else:
                date_obj = trade_date
            
            date_str = date_obj.strftime('%Y-%m-%d')
            
            for ticker in ['INR=X', 'USDINR=X']:
                try:
                    data = yf.download(ticker, start=date_str, end=date_str, progress=False)
                    
                    if not data.empty and 'Close' in data.columns:
                        rate = float(data['Close'].iloc[0])
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
                        _exchange_rate_session_cache[cache_key] = rate
                        return rate
                except Exception:
                    continue
            
            # If exact date fails, try a few days before
            for ticker in ['INR=X', 'USDINR=X']:
                for days_back in [1, 2, 3, 7]:
                    try:
                        past_date = (date_obj - pd.Timedelta(days=days_back)).strftime('%Y-%m-%d')
                        data = yf.download(ticker, start=past_date, end=past_date, progress=False)
                        if not data.empty and 'Close' in data.columns:
                            rate = float(data['Close'].iloc[0])
                            sys.stdout = old_stdout
                            sys.stderr = old_stderr
                            _exchange_rate_session_cache[cache_key] = rate
                            return rate
                    except Exception:
                        continue
        finally:
            # Always restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        # Try exchangerate-api.com (current rate - free API)
        try:
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and 'INR' in data['rates']:
                    rate = float(data['rates']['INR'])
                    # Cache this as fallback rate for all dates
                    _exchange_rate_session_cache[fallback_key] = rate
                    _exchange_rate_session_cache[cache_key] = rate
                    return rate
        except Exception:
            pass  # Continue to last resort
        
        # Last resort: use fallback rate from environment
        rate = FALLBACK_USD_INR_RATE
        _exchange_rate_session_cache[fallback_key] = rate
        _exchange_rate_session_cache[cache_key] = rate
        return rate
    
    # For other currencies, return 1.0 (or implement additional logic)
    return 1.0


def add_exchange_rates_to_trades(df):
    """
    Add Exchange_Rate column to trades DataFrame.
    Only calculates rates for trades that don't have them yet.
    """
    if 'Exchange_Rate' not in df.columns:
        df['Exchange_Rate'] = None
    
    # Find trades without exchange rates
    missing_rate_mask = df['Exchange_Rate'].isna()
    
    if not missing_rate_mask.any():
        return df
    
    print(f"📊 Calculating exchange rates for {missing_rate_mask.sum()} trades...")
    
    # Get unique currency-date combinations that need rates
    needs_rate = df[missing_rate_mask][['Currency', 'Date']].drop_duplicates()
    
    # Build a cache of rates
    rate_cache = {}
    # Also cache API fallback rates per currency to avoid repeated API calls
    currency_fallback_cache = {}
    
    for _, row in needs_rate.iterrows():
        currency = row['Currency']
        trade_date = row['Date']
        
        cache_key = f"{currency}_{trade_date}"
        if cache_key not in rate_cache:
            rate = get_exchange_rate(currency, trade_date)
            rate_cache[cache_key] = rate
            
            # If we got a fallback rate, cache it for this currency
            if currency not in currency_fallback_cache:
                currency_fallback_cache[currency] = rate
    
    # Apply rates to all trades
    for idx in df[missing_rate_mask].index:
        currency = df.at[idx, 'Currency']
        trade_date = df.at[idx, 'Date']
        cache_key = f"{currency}_{trade_date}"
        df.at[idx, 'Exchange_Rate'] = rate_cache.get(cache_key, 1.0)
    
    print(f"✅ Exchange rates calculated for {missing_rate_mask.sum()} trades")
    
    return df


def load_or_create_tradebook():
    """
    Load existing tradebook or create new one from source files.
    Only processes new or modified files incrementally.
    """
    trade_files = get_trade_files()
    metadata = load_processed_files_metadata()
    
    # Check if tradebook exists
    if os.path.exists(TRADEBOOK_FILE):
        # Load existing tradebook
        df = pd.read_csv(TRADEBOOK_FILE)
        print(f"📂 Loaded existing tradebook: {len(df)} trades")
        
        # Check for new or modified files
        new_files = identify_new_or_modified_files(trade_files, metadata)
        
        if new_files:
            print(f"🔄 Found {len(new_files)} new or modified file(s) to process:")
            for filepath in new_files:
                print(f"   - {os.path.basename(filepath)}")
            
            # Parse and append new trades
            new_trades = []
            for filepath in new_files:
                file_basename = os.path.basename(filepath)
                print(f"   Parsing {file_basename}...")
                file_df = parse_trade_file(filepath)
                
                if file_df is not None and not file_df.empty:
                    # Check if trades from this file already exist in tradebook
                    existing_from_file = df[df['Source_File'] == file_basename]
                    
                    if len(existing_from_file) > 0:
                        print(f"   ⚠️  Found {len(existing_from_file)} existing trades from {file_basename}")
                        print(f"   🔍 Checking for duplicates...")
                        
                        # Remove existing trades from this file to avoid duplicates
                        df = df[df['Source_File'] != file_basename]
                        print(f"   🗑️  Removed existing trades from {file_basename}")
                    
                    new_trades.append(file_df)
                    # Update metadata using new format
                    metadata[file_basename] = get_file_modification_time_string(filepath)
            
            if new_trades:
                # Combine new trades
                new_df = pd.concat(new_trades, ignore_index=True)
                print(f"   ✅ Parsed {len(new_df)} trades from modified file(s)")
                
                # Add exchange rates to new trades
                new_df = add_exchange_rates_to_trades(new_df)
                
                # Append to existing tradebook
                df = pd.concat([df, new_df], ignore_index=True)
                
                # Sort by date to keep chronological order
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date').reset_index(drop=True)
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                
                # Save updated tradebook
                df.to_csv(TRADEBOOK_FILE, index=False)
                save_processed_files_metadata(metadata)
                
                print(f"✅ Updated tradebook: {len(df)} total trades")
            else:
                print("   ℹ️ No new trades found in modified files")
        else:
            print("✅ Tradebook is up to date")
        
        return df
    
    else:
        # Create new tradebook from all source files
        print(f"🔨 Creating new tradebook from {len(trade_files)} source file(s)...")
        
        all_trades = []
        for filepath in trade_files:
            print(f"   Parsing {os.path.basename(filepath)}...")
            file_df = parse_trade_file(filepath)
            
            if file_df is not None and not file_df.empty:
                all_trades.append(file_df)
                # Update metadata using new format
                metadata[os.path.basename(filepath)] = get_file_modification_time_string(filepath)
        
        if not all_trades:
            print("⚠️ No trade data found in source files")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['Date', 'Ticker', 'Country', 'Type', 'Qty', 'Price', 
                                        'Currency', 'Source_File', 'Is_SGB', 'Exchange_Rate'])
        
        # Combine all trades
        df = pd.concat(all_trades, ignore_index=True)
        print(f"✅ Parsed {len(df)} trades from {len(all_trades)} file(s)")
        
        # Add exchange rates
        df = add_exchange_rates_to_trades(df)
        
        # Save tradebook
        df.to_csv(TRADEBOOK_FILE, index=False)
        save_processed_files_metadata(metadata)
        
        print(f"✅ Created tradebook: {len(df)} trades")
        
        return df


# ============================================================================
# SGB PRICE CACHING
# ============================================================================

def load_sgb_cache():
    """Load the SGB price cache from JSON file"""
    if os.path.exists(SGB_PRICE_CACHE_FILE):
        try:
            with open(SGB_PRICE_CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Warning: Could not read {SGB_PRICE_CACHE_FILE}, starting fresh")
            return {}
    return {}


def save_sgb_cache(cache):
    """Save the SGB price cache to JSON file"""
    with open(SGB_PRICE_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def is_cache_valid(cached_time_str, validity_hours=CACHE_VALIDITY_HOURS):
    """Check if cached data is still valid based on timestamp"""
    try:
        cached_time = datetime.fromisoformat(cached_time_str)
        age = datetime.now() - cached_time
        return age.total_seconds() < (validity_hours * 3600)
    except Exception:
        return False


def fetch_sgb_price_from_nse(ticker):
    """
    Fetch current SGB price from NSE website
    Returns price or None if failed
    """
    try:
        # NSE requires proper headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # The NSE API endpoint for bond quotes
        # Note: NSE API structure may change, this is a common pattern
        url = f"https://www.nseindia.com/api/quote-equity?symbol={ticker}"
        
        # Add a small delay to be respectful to NSE servers
        time.sleep(0.5)
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Try to get the price from various possible fields
        price = None
        if 'priceInfo' in data and 'lastPrice' in data['priceInfo']:
            price = data['priceInfo']['lastPrice']
        elif 'lastPrice' in data:
            price = data['lastPrice']
        
        if price is not None:
            return float(price)
        
        return None
    
    except Exception as e:
        print(f"⚠️ Could not fetch SGB price from NSE for {ticker}: {e}")
        return None


def get_sgb_price_cached(ticker, df=None):
    """
    Get SGB price with caching.
    First checks cache, if expired or missing, fetches from NSE.
    Falls back to last known price from trades if NSE fetch fails.
    
    Args:
        ticker: The SGB ticker symbol
        df: Optional DataFrame of trades to use as fallback
    
    Returns:
        Price as float or None if not available
    """
    cache = load_sgb_cache()
    
    # Check if we have a valid cached price
    if ticker in cache and 'timestamp' in cache[ticker]:
        if is_cache_valid(cache[ticker]['timestamp']):
            price = cache[ticker].get('price')
            if price is not None:
                return float(price)
    
    # Cache is expired or missing, fetch fresh price
    price = fetch_sgb_price_from_nse(ticker)
    
    if price is not None:
        # Cache the fresh price
        cache[ticker] = {
            'price': price,
            'timestamp': datetime.now().isoformat()
        }
        save_sgb_cache(cache)
        return price
    else:
        # Fallback to last known price from trades if available
        if df is not None:
            try:
                recent_price = df[df['Ticker'] == ticker]['Price'].dropna().iloc[-1]
                price = float(recent_price)
                print(f"⚠️ Using fallback price from trades for {ticker}: {price}")
                
                # Cache the fallback price (it's better than nothing)
                cache[ticker] = {
                    'price': price,
                    'timestamp': datetime.now().isoformat(),
                    'fallback': True
                }
                save_sgb_cache(cache)
                return price
            except Exception:
                pass
        
        # If we have an old cached price, use it as last resort
        if ticker in cache and 'price' in cache[ticker]:
            print(f"⚠️ Using stale cached price for {ticker}: {cache[ticker]['price']}")
            return cache[ticker]['price']
        
        return None


def clear_sgb_cache():
    """Clear the SGB price cache"""
    if os.path.exists(SGB_PRICE_CACHE_FILE):
        os.remove(SGB_PRICE_CACHE_FILE)
        print(f"✅ Cleared SGB price cache")
    else:
        print(f"ℹ️  No SGB price cache found")


def show_sgb_cache_status():
    """Show the current SGB cache status"""
    if not os.path.exists(SGB_PRICE_CACHE_FILE):
        print("❌ No SGB price cache found")
        return
    
    cache = load_sgb_cache()
    
    print(f"📊 SGB Price Cache Status")
    print(f"   Total cached tickers: {len(cache)}")
    print()
    
    now = datetime.now()
    
    for ticker, data in sorted(cache.items()):
        price = data.get('price', 'N/A')
        timestamp_str = data.get('timestamp', '')
        is_fallback = data.get('fallback', False)
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age = now - timestamp
            age_str = f"{age.total_seconds() / 3600:.1f} hours ago"
            
            if is_cache_valid(timestamp_str):
                status = "✅ VALID"
            else:
                status = "⏰ EXPIRED"
        except Exception:
            age_str = "Unknown"
            status = "❓ INVALID"
        
        fallback_tag = " (fallback)" if is_fallback else ""
        print(f"   {status} {ticker}: ₹{price}{fallback_tag} - cached {age_str}")


# ============================================================================
# CLI COMMANDS
# ============================================================================

def tradebook_status():
    """Show the current tradebook status"""
    print("📊 Tradebook Status")
    print("=" * 60)
    
    if os.path.exists(TRADEBOOK_FILE):
        tradebook_size = os.path.getsize(TRADEBOOK_FILE)
        tradebook_mtime = os.path.getmtime(TRADEBOOK_FILE)
        tradebook_date = datetime.fromtimestamp(tradebook_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"✅ Tradebook exists: {TRADEBOOK_FILE}")
        print(f"   Size: {tradebook_size:,} bytes")
        print(f"   Last modified: {tradebook_date}")
        
        try:
            df = pd.read_csv(TRADEBOOK_FILE)
            print(f"   Total trades: {len(df):,}")
            if 'Date' in df.columns:
                print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
            if 'Source_File' in df.columns:
                sources = df['Source_File'].unique()
                print(f"   Source files: {len(sources)}")
        except Exception as e:
            print(f"   ⚠️ Error reading tradebook: {e}")
    else:
        print("❌ Tradebook does not exist")
        print("   Run with 'consolidate' command to create it from source files")
    
    print()
    
    if os.path.exists(PROCESSED_FILES_METADATA):
        print(f"✅ Metadata exists: {PROCESSED_FILES_METADATA}")
        metadata = load_processed_files_metadata()
        print(f"   Processed files tracked: {len(metadata)}")
        print()
        print("   Already processed:")
        for file_key in sorted(metadata.keys()):
            # Metadata is now simply a string in 'YYYY-MM-DD HH:MM:SS' format
            mtime_str = metadata[file_key]
            
            full_path = os.path.join(WORKING_DIR, file_key)
            exists = "✅" if os.path.exists(full_path) else "🗑️ (deleted)"
            print(f"     {exists} {file_key} (processed: {mtime_str})")
    else:
        print("❌ Metadata does not exist")
    
    print()
    print("📁 Current Source Trade Files:")
    trade_files = get_trade_files()
    
    if trade_files:
        print(f"   Found {len(trade_files)} source trade file(s):")
        metadata = load_processed_files_metadata()
        
        for filepath in sorted(trade_files):
            file_key = os.path.basename(filepath)
            current_mtime = get_file_modification_time(filepath)
            
            # Get stored timestamp string and convert for comparison
            if file_key in metadata:
                stored_time_str = metadata[file_key]
                try:
                    stored_dt = datetime.strptime(stored_time_str, '%Y-%m-%d %H:%M:%S')
                    processed_mtime = stored_dt.timestamp()
                except (ValueError, AttributeError):
                    processed_mtime = 0
            else:
                processed_mtime = 0
            
            mtime_str = datetime.fromtimestamp(current_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # Add 1-second tolerance to handle timestamp precision differences
            if current_mtime > processed_mtime + 1:
                status = "🔄 NEW/MODIFIED - Will be processed"
            else:
                status = "✅ Already processed"
            
            print(f"     {status}")
            print(f"        {file_key} (modified: {mtime_str})")
    else:
        print("   ℹ️  No source trade files found")
        print("   This is normal if all trades have been consolidated into tradebook.csv")


def clear_tradebook():
    """Clear the tradebook and metadata"""
    print("🗑️  Clearing tradebook...")
    
    deleted = []
    if os.path.exists(TRADEBOOK_FILE):
        os.remove(TRADEBOOK_FILE)
        deleted.append(TRADEBOOK_FILE)
        print(f"   ✅ Deleted {TRADEBOOK_FILE}")
    
    if os.path.exists(PROCESSED_FILES_METADATA):
        os.remove(PROCESSED_FILES_METADATA)
        deleted.append(PROCESSED_FILES_METADATA)
        print(f"   ✅ Deleted {PROCESSED_FILES_METADATA}")
    
    if not deleted:
        print("   ℹ️  No tradebook files found")
    else:
        print(f"\n✅ Tradebook cleared successfully. Deleted {len(deleted)} file(s).")


def rebuild_tradebook():
    """Force rebuild of the tradebook"""
    print("🔨 Rebuilding tradebook from source files...")
    clear_tradebook()
    print()
    
    df = load_or_create_tradebook()
    
    print()
    print(f"✅ Tradebook rebuilt successfully!")
    print(f"   Total trades: {len(df):,}")


def consolidate_trades():
    """Build/update tradebook and show which source files can be deleted"""
    print("📦 Consolidating trades into tradebook...")
    print("=" * 60)
    
    df = load_or_create_tradebook()
    
    print()
    print("=" * 60)
    print(f"✅ Consolidation complete!")
    print(f"   Total trades in tradebook: {len(df):,}")
    print()
    
    trade_files = get_trade_files()
    metadata = load_processed_files_metadata()
    
    can_delete = []
    for filepath in trade_files:
        file_key = os.path.basename(filepath)
        if file_key in metadata:
            can_delete.append(os.path.basename(filepath))
    
    if can_delete:
        print("💡 The following source files have been processed and can be safely deleted:")
        print()
        for filename in sorted(can_delete):
            print(f"   📄 {filename}")
        print()
        print("   To delete them from archivesCSV directory, run:")
        print(f"   cd {WORKING_DIR} && rm {' '.join(can_delete)}")
    else:
        print("ℹ️  No source files to delete (none have been fully processed yet)")


def show_help():
    """Show help message"""
    print("Tradebook Builder - Consolidated Trade Management System")
    print("=" * 60)
    print()
    print("Usage: python3 tradebook_builder.py [command]")
    print()
    print("Commands:")
    print("  rebuild     - Force rebuild the entire tradebook (default)")
    print("  status      - Show current tradebook status")
    print("  consolidate - Build/update tradebook from source files")
    print("  clear       - Clear tradebook and metadata files")
    print("  sgb-status  - Show SGB price cache status")
    print("  sgb-clear   - Clear SGB price cache")
    print("  help        - Show this help message")
    print()
    print("Workflow:")
    print("  1. Run 'consolidate' to build tradebook.csv from all trades*.csv files")
    print("  2. After consolidation, you can delete the source trades*.csv files")
    print("  3. In the future, add new trades*.csv files and run 'consolidate' again")
    print("  4. Only new files will be processed and added to tradebook.csv")
    print()
    print("Features:")
    print("  - Incremental file processing (only new/modified files)")
    print("  - Exchange rate caching (USD/INR stored in tradebook)")
    print("  - SGB price caching (6-hour validity)")
    print("  - Persistent metadata tracking")
    print()
    print("Examples:")
    print("  python3 tradebook_builder.py status")
    print("  python3 tradebook_builder.py consolidate")
    print("  python3 tradebook_builder.py sgb-status")


def main():
    """Main entry point for CLI"""
    import sys
    
    command = sys.argv[1] if len(sys.argv) > 1 else "rebuild"
    
    if command == "status":
        tradebook_status()
    elif command == "consolidate":
        consolidate_trades()
    elif command == "clear":
        clear_tradebook()
    elif command == "rebuild":
        rebuild_tradebook()
    elif command == "sgb-status":
        show_sgb_cache_status()
    elif command == "sgb-clear":
        clear_sgb_cache()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        print()
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
