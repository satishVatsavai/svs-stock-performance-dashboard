"""
Price Fetcher Module
Centralized price fetching logic with smart caching and fallback mechanisms

This module provides:
1. Smart price fetching from yfinance with rate limit handling
2. Automatic caching to archivesCSV/backupPrices.csv
3. Fallback to cached prices when API fails
4. Support for SGBs via NSE API
5. Historical price fetching for snapshots
"""

import pandas as pd
import os
import warnings
import logging
import requests
from datetime import datetime, date

# Suppress warnings
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Suppress yfinance logger messages
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Default backup prices file path
BACKUP_PRICES_FILE = 'archivesCSV/backupPrices.csv'


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def load_backup_prices(backup_csv_path=BACKUP_PRICES_FILE):
    """
    Load prices from backup CSV file as fallback when Yahoo Finance has rate limits
    Supports both old format (Ticker, Current Price) and new format (Ticker, Date, Closing Price)
    
    Returns:
        Tuple of (current_prices, previous_prices) dictionaries
        - current_prices: Most recent price for each ticker
        - previous_prices: Second most recent price (for daily change calculation)
        Example: ({'AAPL': 150.0}, {'AAPL': 149.5})
    """
    if not os.path.exists(backup_csv_path):
        return {}, {}
    
    try:
        backup_df = pd.read_csv(backup_csv_path)
        current_prices = {}
        prev_prices = {}
        
        # Check which format we're dealing with
        if 'Closing Price' in backup_df.columns:
            # New format: Ticker, Date, Closing Price
            for ticker in backup_df['Ticker'].unique():
                ticker_rows = backup_df[backup_df['Ticker'] == ticker]
                # Get rows with valid prices
                valid_prices = ticker_rows[ticker_rows['Closing Price'].notna()]
                if not valid_prices.empty:
                    # Sort by date (most recent first)
                    if 'Date' in valid_prices.columns:
                        valid_prices = valid_prices.sort_values('Date', ascending=False)
                        # Remove duplicate dates - keep first (most recent) occurrence
                        valid_prices = valid_prices.drop_duplicates(subset='Date', keep='first')
                    
                    # Get most recent price
                    price = float(valid_prices.iloc[0]['Closing Price'])
                    current_prices[ticker] = price
                    
                    # Get previous close (second most recent unique date)
                    if len(valid_prices) >= 2:
                        prev_price = float(valid_prices.iloc[1]['Closing Price'])
                        prev_prices[ticker] = prev_price
                    else:
                        # No previous price available, use current as previous
                        prev_prices[ticker] = price
        
        elif 'Current Price' in backup_df.columns:
            # Old format: Ticker, Current Price (no date info)
            for _, row in backup_df.iterrows():
                ticker = row['Ticker']
                price = float(row['Current Price']) if pd.notna(row['Current Price']) else None
                if price is not None:
                    current_prices[ticker] = price
                    prev_prices[ticker] = price  # Same as current (no daily change data)
        else:
            print(f"⚠️ Unrecognized format in {backup_csv_path}")
            return {}, {}
        
        print(f"📋 Loaded {len(current_prices)} prices from {backup_csv_path}")
        return current_prices, prev_prices
    except Exception as e:
        print(f"⚠️ Could not load backup prices from {backup_csv_path}: {e}")
        return {}, {}


def save_backup_prices(prices_dict, backup_csv_path=BACKUP_PRICES_FILE):
    """
    Save/update prices to backup CSV file
    - If Ticker-Date combination exists: UPDATE the price (don't create duplicate)
    - If Ticker-Date combination doesn't exist: CREATE new record
    
    Args:
        prices_dict: Dictionary with ticker as key and price as value
        backup_csv_path: Path to the CSV file
    """
    try:
        current_date = date.today().strftime('%Y-%m-%d')
        
        # Load existing prices
        if os.path.exists(backup_csv_path):
            existing_df = pd.read_csv(backup_csv_path)
            
            # Check format
            if 'Closing Price' in existing_df.columns and 'Date' in existing_df.columns:
                # New format - update existing or append new records
                updated_count = 0
                new_count = 0
                
                for ticker, price in prices_dict.items():
                    # Check if this Ticker-Date combination exists
                    mask = (existing_df['Ticker'] == ticker) & (existing_df['Date'] == current_date)
                    
                    if mask.any():
                        # Update existing record
                        existing_df.loc[mask, 'Closing Price'] = price
                        updated_count += 1
                    else:
                        # Add new record
                        new_record = pd.DataFrame([{
                            'Ticker': ticker,
                            'Date': current_date,
                            'Closing Price': price
                        }])
                        existing_df = pd.concat([existing_df, new_record], ignore_index=True)
                        new_count += 1
                
                # Sort by Ticker and Date (most recent first)
                existing_df = existing_df.sort_values(['Ticker', 'Date'], ascending=[True, False])
                existing_df.to_csv(backup_csv_path, index=False)
                
                if updated_count > 0 or new_count > 0:
                    print(f"💾 Backup prices: Updated {updated_count}, Added {new_count} to {backup_csv_path}")
                return
            
            # Old format - convert to new format
            existing_prices = dict(zip(existing_df['Ticker'], existing_df.get('Current Price', [])))
        else:
            existing_prices = {}
        
        # Create new file with new format or migrate old format
        new_records = []
        for ticker, price in prices_dict.items():
            new_records.append({
                'Ticker': ticker,
                'Date': current_date,
                'Closing Price': price
            })
        
        if new_records:
            new_df = pd.DataFrame(new_records)
            new_df = new_df.sort_values(['Ticker', 'Date'], ascending=[True, False])
            new_df.to_csv(backup_csv_path, index=False)
            print(f"💾 Created {backup_csv_path} with {len(prices_dict)} prices")
        
    except Exception as e:
        print(f"⚠️ Could not save backup prices to {backup_csv_path}: {e}")


# ============================================================================
# PRICE FETCHING - YFINANCE
# ============================================================================

def fetch_price_from_yfinance(ticker, target_date=None):
    """
    Fetch price from Yahoo Finance for a ticker
    
    Args:
        ticker: Stock ticker symbol
        target_date: Optional date to fetch historical price for (datetime or string)
                    If None, fetches current price
        
    Returns:
        If target_date is None:
            Tuple of (price, company_name, previous_close):
            - price: Current price (float) or 'RATE_LIMITED' if rate limit hit, or None if failed
            - company_name: Company name (string) or None
            - previous_close: Previous close price (float) or None
        
        If target_date is provided:
            Tuple of (price, source):
            - price: Historical price (float) or None
            - source: 'yfinance' or 'unavailable'
    """
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        
        # Historical price fetch (for snapshots)
        if target_date is not None:
            # Convert target_date to datetime if it's a string
            if isinstance(target_date, str):
                target_date = pd.to_datetime(target_date)
            
            start_date = target_date - pd.Timedelta(days=7)
            end_date = target_date + pd.Timedelta(days=7)
            
            hist = stock.history(start=start_date, end=end_date)
            
            if not hist.empty:
                # Get the closest date to target
                closest_idx = hist.index[hist.index <= target_date].max() if any(hist.index <= target_date) else hist.index[0]
                price = hist.loc[closest_idx, 'Close']
                print(f"✅ Fetched historical price for {ticker} on {target_date.date()}: ₹{price:.2f}")
                return float(price), 'yfinance'
            
            # If history failed, try current info as fallback
            info = stock.info
            price = (info.get('currentPrice') or 
                    info.get('regularMarketPrice') or 
                    info.get('previousClose'))
            
            if price:
                print(f"💾 Using current price for {ticker} (historical not available): ₹{price:.2f}")
                return float(price), 'yfinance'
            
            return None, 'unavailable'
        
        # Current price fetch
        info = stock.info
        
        company_name = (info.get('longName') or 
                      info.get('shortName') or 
                      ticker)
        
        price = (info.get('currentPrice') or 
                info.get('regularMarketPrice') or 
                info.get('previousClose') or
                info.get('regularMarketPreviousClose'))
        
        prev_close = info.get('regularMarketPreviousClose') or info.get('previousClose')
        
        if price is None:
            hist = stock.history(period="1mo")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[-2]
        
        if price is not None:
            print(f"✅ Fetched {ticker} from yfinance: ₹{price:.2f}")
            return float(price), company_name, float(prev_close) if prev_close else float(price)
        
        return None, company_name, None
        
    except Exception as e:
        error_str = str(e)
        if '429' in error_str or 'Too Many Requests' in error_str:
            if target_date is not None:
                return None, 'unavailable'
            return 'RATE_LIMITED', None, None
        
        if target_date is not None:
            print(f"❌ ERROR: Could not fetch historical price for {ticker}: {e}")
            return None, 'unavailable'
        return None, None, None


# ============================================================================
# PRICE FETCHING - NSE (SGBs)
# ============================================================================

def fetch_sgb_price(ticker):
    """
    Fetch SGB price from NSE using a lightweight requests call.
    
    Args:
        ticker: SGB ticker symbol
        
    Returns:
        Price (float) or None if fetch failed
    """
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }

        sess = requests.Session()
        resp = sess.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        if data and isinstance(data, dict) and 'priceInfo' in data:
            price = data['priceInfo'].get('lastPrice') or data['priceInfo'].get('close')
            if price is not None:
                price_f = float(price)
                print(f"✅ Fetched {ticker} (SGB) from NSE: ₹{price_f:.2f}")
                return price_f
    except Exception as e:
        print(f"⚠️ Error fetching SGB price for {ticker} from NSE: {e}")

    return None


# ============================================================================
# SMART PRICE FETCHING WITH FALLBACK
# ============================================================================

def fetch_price_with_fallback(ticker, is_sgb=False, backup_csv_path=BACKUP_PRICES_FILE):
    """
    Fetch price with smart fallback mechanism:
    1. Try fetching from yfinance (for stocks/MFs) or NSE (for SGBs)
    2. If successful, cache the price and return it
    3. If rate limited or failed, try backup CSV
    4. If not in backup CSV, log error and return None
    
    Args:
        ticker: Stock ticker symbol
        is_sgb: Whether this is a Sovereign Gold Bond
        backup_csv_path: Path to backup CSV file
        
    Returns:
        Tuple of (price, company_name, previous_close, source):
        - price: Current price (float) or None
        - company_name: Company name (string) or ticker
        - previous_close: Previous close price (float) or None
        - source: 'yfinance', 'nse', 'cached', or 'unavailable'
    """
    # Load backup prices for potential fallback
    backup_prices, prev_backup_prices = load_backup_prices(backup_csv_path)
    
    # Try fetching from API first
    if is_sgb:
        # Fetch from NSE for SGBs
        price = fetch_sgb_price(ticker)
        if price is not None:
            # Success - cache it
            save_backup_prices({ticker: price}, backup_csv_path)
            return price, f"{ticker} (Sovereign Gold Bond)", price, 'nse'
        else:
            # NSE fetch failed - try backup
            if ticker in backup_prices:
                print(f"💾 Using cached price for {ticker} (SGB): ₹{backup_prices[ticker]:.2f}")
                return (backup_prices[ticker], f"{ticker} (Sovereign Gold Bond)", 
                       prev_backup_prices.get(ticker, backup_prices[ticker]), 'cached')
            else:
                print(f"❌ ERROR: Could not fetch {ticker} (SGB) from NSE and no backup price available")
                return None, f"{ticker} (SGB - Price N/A)", None, 'unavailable'
    else:
        # Fetch from yfinance for regular stocks/MFs
        price, company_name, prev_close = fetch_price_from_yfinance(ticker)
        
        if price == 'RATE_LIMITED':
            # Rate limited - try backup
            if ticker in backup_prices:
                print(f"💾 Using cached price for {ticker} (rate limited): ₹{backup_prices[ticker]:.2f}")
                return (backup_prices[ticker], ticker, 
                       prev_backup_prices.get(ticker, backup_prices[ticker]), 'cached')
            else:
                print(f"❌ ERROR: Rate limit hit for {ticker} and no backup price available")
                return None, ticker, None, 'unavailable'
        elif price is not None:
            # Success - cache it
            save_backup_prices({ticker: price}, backup_csv_path)
            return price, company_name, prev_close, 'yfinance'
        else:
            # Fetch failed (not rate limit) - try backup
            if ticker in backup_prices:
                print(f"💾 Using cached price for {ticker}: ₹{backup_prices[ticker]:.2f}")
                return (backup_prices[ticker], ticker, 
                       prev_backup_prices.get(ticker, backup_prices[ticker]), 'cached')
            else:
                print(f"❌ ERROR: Could not fetch {ticker} from yfinance and no backup price available")
                return None, ticker, None, 'unavailable'


# ============================================================================
# HISTORICAL PRICE FETCHING (FOR SNAPSHOTS)
# ============================================================================

def fetch_historical_price(ticker, target_date, is_sgb=False):
    """
    Fetch historical price for a ticker at a specific date
    Used for generating year-end snapshots
    
    This is a convenience wrapper around fetch_price_from_yfinance with target_date parameter
    
    Args:
        ticker: Stock ticker symbol
        target_date: Date to fetch price for (datetime or string)
        is_sgb: Whether this is a Sovereign Gold Bond
    
    Returns:
        Tuple of (price, source):
        - price: Historical price (float) or None
        - source: 'yfinance', 'nse_current', or 'unavailable'
    """
    if is_sgb:
        # For SGBs, fetch current price from NSE as approximation
        price = fetch_sgb_price(ticker)
        if price:
            return price, 'nse_current'
        return None, 'unavailable'
    
    # For stocks/MFs, use the unified fetch_price_from_yfinance
    return fetch_price_from_yfinance(ticker, target_date=target_date)
