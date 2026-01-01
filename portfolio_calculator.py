"""
Portfolio Summary Calculator Module
Extracts portfolio calculation logic for reuse in dashboard and Telegram notifications
"""
import yfinance as yf
import warnings
import logging
# Suppress urllib3 SSL warning for macOS with LibreSSL
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')
# Suppress yfinance warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Suppress yfinance logger messages
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

import pandas as pd
from pyxirr import xirr
from datetime import date, datetime
import glob
import os
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()


def format_indian_number(number):
    """Format number with Indian numbering system (lakhs and crores)"""
    s = str(int(round(number)))
    if len(s) <= 3:
        return s
    
    last_three = s[-3:]
    remaining = s[:-3]
    
    result = ""
    while len(remaining) > 2:
        result = "," + remaining[-2:] + result
        remaining = remaining[:-2]
    
    if remaining:
        result = remaining + result
    
    return result + "," + last_three


def get_sgb_price(ticker):
    """Fetch SGB price from NSE using a lightweight requests call."""
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
                try:
                    price_f = float(price)
                    return price_f
                except Exception:
                    return None
    except Exception as e:
        print(f"⚠️ Error fetching SGB price for {ticker} from NSE via requests: {e}")

    return None


def get_exchange_rate(currency, trade_date):
    """
    Get historical exchange rate for a given currency and date.
    
    Data sources (in order of preference):
    1. Yahoo Finance
    2. exchangerate-api.com (current rate as fallback)
    3. Environment variable FALLBACK_USD_INR_RATE (last resort)
    """
    if currency == 'INR':
        return 1.0
    
    import sys
    from io import StringIO
    import requests
    
    # Try Yahoo Finance first
    try:
        start_date = trade_date - pd.Timedelta(days=7)
        end_date = trade_date + pd.Timedelta(days=1)
        
        # Suppress all output from yfinance
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        
        try:
            # Try multiple ticker formats
            for ticker in ['INR=X', 'USDINR=X']:
                try:
                    fx_data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
                    
                    if not fx_data.empty:
                        rate = float(fx_data['Close'].iloc[-1].iloc[0]) if hasattr(fx_data['Close'].iloc[-1], 'iloc') else float(fx_data['Close'].iloc[-1])
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
                        print(f"✅ Exchange rate fetched from yFinance: 1 USD = {rate} INR")
                        return round(rate, 2)
                except Exception:
                    continue
            
            # Try history method as last Yahoo attempt
            for ticker in ['INR=X', 'USDINR=X']:
                try:
                    fx_data = yf.Ticker(ticker).history(period='5d')
                    if not fx_data.empty:
                        rate = float(fx_data['Close'].iloc[-1])
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
                        print(f"✅ Exchange rate fetched from yFinance: 1 USD = {rate} INR")
                        return round(rate, 2)
                except Exception:
                    continue
        finally:
            # Always restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
    except Exception:
        pass  # Continue to fallback
    
    # Try exchangerate-api.com (current rate - free API)
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'rates' in data and 'INR' in data['rates']:
                rate = float(data['rates']['INR'])
                print(f"⚠️ Using current exchange rate from exchangerate-api.com: 1 USD = {rate} INR")
                return round(rate, 2)
    except Exception:
        pass  # Continue to last resort
    
    # Fallback to configured rate from .env file (default: 83.0)
    fallback_rate = float(os.getenv('FALLBACK_USD_INR_RATE', '83.0'))
    print(f"⚠️ Using fallback exchange rate from .env: 1 USD = {fallback_rate} INR")
    return fallback_rate


def load_trade_data():
    """Load tradebook.csv as-is without any processing or updates"""
    # Simply load the tradebook CSV file directly
    # User maintains this file manually using tradebook_builder.py
    
    tradebook_file = 'archivesCSV/tradebook.csv'
    
    if not os.path.exists(tradebook_file):
        raise FileNotFoundError(
            f"❌ {tradebook_file} not found! "
            f"Please create it first by running: cd archivesCSV && python3 ../archivesPY/tradebook_builder.py consolidate"
        )
    
    print(f"📂 Loading {tradebook_file}...")
    df = pd.read_csv(tradebook_file)
    print(f"   Loaded {len(df)} trades")
    
    # Apply standard transformations
    df['Type'] = df['Type'].str.upper()
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Verify required columns exist
    required_columns = ['Date', 'Ticker', 'Type', 'Qty', 'Price', 'Currency', 'Exchange_Rate']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(
            f"❌ Missing required columns in {tradebook_file}: {', '.join(missing_columns)}\n"
            f"   Please rebuild the tradebook: python3 tradebook_builder.py rebuild"
        )
    
    return df


def get_latest_snapshot(snapshot_dir='archivesCSV'):
    """
    Find and load the most recent holdings snapshot
    
    Returns:
        tuple: (snapshot_df, snapshot_year) or (None, None) if no snapshots found
    """
    # Find all snapshot files
    snapshot_pattern = os.path.join(snapshot_dir, 'holdings_snapshot_*.csv')
    snapshot_files = glob.glob(snapshot_pattern)
    
    if not snapshot_files:
        return None, None
    
    # Extract years and find the latest
    snapshots_with_years = []
    for file in snapshot_files:
        try:
            year = int(file.split('_')[-1].replace('.csv', ''))
            snapshots_with_years.append((file, year))
        except ValueError:
            continue
    
    if not snapshots_with_years:
        return None, None
    
    # Get the latest snapshot
    latest_file, latest_year = max(snapshots_with_years, key=lambda x: x[1])
    
    print(f"📸 Loading snapshot: {os.path.basename(latest_file)}")
    snapshot_df = pd.read_csv(latest_file)
    print(f"   Snapshot date: {latest_year}-12-31")
    print(f"   Holdings in snapshot: {len(snapshot_df)} tickers")
    
    return snapshot_df, latest_year


def load_trade_data_with_snapshot(force_full_recalc=False):
    """
    Load trade data, using snapshots for optimization if available
    
    Args:
        force_full_recalc: If True, ignore snapshots and process full tradebook
    
    Returns:
        tuple: (df, snapshot_df, snapshot_year, incremental_df)
            - df: Full tradebook dataframe (for display purposes)
            - snapshot_df: Holdings snapshot dataframe (or None)
            - snapshot_year: Year of the snapshot (or None)
            - incremental_df: Trades after snapshot (or full df if no snapshot)
    """
    # Load full tradebook (always needed for display)
    df = load_trade_data()
    
    # Check if we should use snapshots
    if force_full_recalc:
        print("🔄 Force recalculation enabled - processing full tradebook")
        return df, None, None, df
    
    # Try to load latest snapshot
    snapshot_df, snapshot_year = get_latest_snapshot()
    
    if snapshot_df is None or snapshot_year is None:
        print("⚠️  No snapshots found - processing full tradebook")
        print("   💡 Tip: Run 'python3 generate_snapshots.py' to create snapshots")
        return df, None, None, df
    
    # Filter trades after the snapshot date
    snapshot_date = pd.Timestamp(f'{snapshot_year}-12-31 23:59:59')
    incremental_df = df[df['Date'] > snapshot_date].copy()
    
    if len(incremental_df) == 0:
        print(f"✅ No new trades since snapshot - using snapshot only")
    else:
        print(f"📊 Processing {len(incremental_df)} trades since {snapshot_year}-12-31")
        print(f"   (Skipped {len(df) - len(incremental_df)} historical trades)")
    
    return df, snapshot_df, snapshot_year, incremental_df


def get_currently_held_tickers(df):
    """Get list of tickers that are currently held"""
    ticker_list = df['Ticker'].unique().tolist()
    currently_held_tickers = []

    for ticker in ticker_list:
        ticker_trades = df[df['Ticker'] == ticker]
        buy_qty = ticker_trades[ticker_trades['Type'] == 'BUY']['Qty'].sum()
        sell_qty = ticker_trades[ticker_trades['Type'] == 'SELL']['Qty'].sum()
        current_qty = buy_qty - sell_qty
        
        if current_qty >= 0.02:
            currently_held_tickers.append(ticker)
    
    return currently_held_tickers


def get_market_data(df, currently_held_tickers):
    """Fetch current market prices for held tickers"""
    market_data = {}
    company_names = {}
    previous_close_data = {}
    
    for ticker in currently_held_tickers:
        is_sgb = df[df['Ticker'] == ticker]['Is_SGB'].iloc[0] if 'Is_SGB' in df.columns else False
        
        if is_sgb:
            try:
                price = get_sgb_price(ticker)
                if price:
                    market_data[ticker] = price
                    company_names[ticker] = f"{ticker} (Sovereign Gold Bond)"
                else:
                    try:
                        recent_price = df[df['Ticker'] == ticker]['Price'].dropna().iloc[-1]
                        market_data[ticker] = float(recent_price)
                        company_names[ticker] = f"{ticker} (SGB - fallback)"
                    except Exception:
                        market_data[ticker] = None
                        company_names[ticker] = f"{ticker} (SGB - Price N/A)"
            except Exception as e:
                print(f"⚠️ Error fetching SGB {ticker}: {str(e)}")
                market_data[ticker] = None
                company_names[ticker] = f"{ticker} (SGB - Error)"
        else:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                company_name = (info.get('longName') or 
                              info.get('shortName') or 
                              ticker)
                company_names[ticker] = company_name
                
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
                
                market_data[ticker] = price
                previous_close_data[ticker] = prev_close if prev_close else price
            except Exception as e:
                print(f"⚠️ Could not fetch price for {ticker}: {str(e)}")
                market_data[ticker] = None
                company_names[ticker] = ticker
    
    return market_data, company_names, previous_close_data


def calculate_fifo_avg_price(ticker_trades):
    """
    Calculate average buy price using FIFO (First In First Out) method.
    Sells are matched against earliest buys first, in chronological order.
    Returns the weighted average price of remaining holdings.
    """
    # CRITICAL: Sort trades by date, then by Type (BUY before SELL on same date)
    # This ensures BUYs are processed before SELLs when they occur on the same day
    ticker_trades = ticker_trades.copy()
    ticker_trades['Type_Sort'] = ticker_trades['Type'].map({'BUY': 0, 'SELL': 1})
    ticker_trades = ticker_trades.sort_values(['Date', 'Type_Sort']).reset_index(drop=True)
    
    # Create a list of buy lots (each with qty and price) in chronological order
    buy_lots = []
    
    # Process ALL trades in chronological order
    for _, row in ticker_trades.iterrows():
        if row['Type'] == 'BUY':
            # Add new buy lot
            buy_lots.append({'qty': row['Qty'], 'price': row['Price']})
        elif row['Type'] == 'SELL':
            # Match sell against earliest remaining buy lots (FIFO)
            sell_qty_remaining = row['Qty']
            
            for lot in buy_lots:
                if sell_qty_remaining <= 0:
                    break
                    
                if lot['qty'] > 0:
                    qty_to_reduce = min(lot['qty'], sell_qty_remaining)
                    lot['qty'] -= qty_to_reduce
                    sell_qty_remaining -= qty_to_reduce
    
    # Calculate weighted average of remaining lots
    total_qty = sum(lot['qty'] for lot in buy_lots if lot['qty'] > 0)
    total_value = sum(lot['qty'] * lot['price'] for lot in buy_lots if lot['qty'] > 0)
    
    if total_qty > 0:
        return total_value / total_qty
    else:
        return 0


def apply_incremental_trades(snapshot_df, incremental_df):
    """
    Apply incremental trades to snapshot holdings
    
    Args:
        snapshot_df: Holdings snapshot dataframe
        incremental_df: New trades after snapshot
    
    Returns:
        Dictionary with ticker as key and holding info as value
    """
    # Start with snapshot holdings
    holdings = {}
    for _, row in snapshot_df.iterrows():
        holdings[row['Ticker']] = {
            'qty': row['Qty'],
            'avg_price': row['Avg_Buy_Price'],
            'invested_inr': row['Total_Invested_INR'],
            'realized_profit': row['Realized_Profit_INR'],
            'currency': row['Currency'],
            'fx_rate': row['Exchange_Rate'],
            'is_sgb': row.get('Is_SGB', False),
            'buy_lots': [{'qty': row['Qty'], 'price': row['Avg_Buy_Price']}]  # Treat snapshot as one lot
        }
    
    # Apply incremental trades
    if not incremental_df.empty:
        for ticker in incremental_df['Ticker'].unique():
            ticker_trades = incremental_df[incremental_df['Ticker'] == ticker].sort_values('Date')
            
            # Initialize if new ticker
            if ticker not in holdings:
                first_trade = ticker_trades.iloc[0]
                holdings[ticker] = {
                    'qty': 0.0,
                    'avg_price': 0.0,
                    'invested_inr': 0.0,
                    'realized_profit': 0.0,
                    'currency': first_trade['Currency'],
                    'fx_rate': first_trade['Exchange_Rate'],
                    'is_sgb': first_trade.get('Is_SGB', False),
                    'buy_lots': []
                }
            
            holding = holdings[ticker]
            
            # Process each trade
            for _, trade in ticker_trades.iterrows():
                if trade['Type'] == 'BUY':
                    # Add new buy lot
                    holding['buy_lots'].append({
                        'qty': trade['Qty'],
                        'price': trade['Price']
                    })
                    holding['qty'] += trade['Qty']
                    
                elif trade['Type'] == 'SELL':
                    # Match sell against earliest buy lots (FIFO)
                    sell_qty_remaining = trade['Qty']
                    sell_price = trade['Price']
                    fx_rate = trade['Exchange_Rate']
                    
                    for lot in holding['buy_lots']:
                        if sell_qty_remaining <= 0:
                            break
                        
                        if lot['qty'] > 0:
                            qty_to_match = min(lot['qty'], sell_qty_remaining)
                            
                            # Calculate realized profit
                            sell_revenue = qty_to_match * sell_price * fx_rate
                            sell_cost = qty_to_match * lot['price'] * fx_rate
                            holding['realized_profit'] += (sell_revenue - sell_cost)
                            
                            lot['qty'] -= qty_to_match
                            sell_qty_remaining -= qty_to_match
                    
                    holding['qty'] -= trade['Qty']
            
            # Recalculate average price from remaining lots
            total_qty = sum(lot['qty'] for lot in holding['buy_lots'] if lot['qty'] > 0)
            total_value = sum(lot['qty'] * lot['price'] for lot in holding['buy_lots'] if lot['qty'] > 0)
            
            if total_qty > 0:
                holding['avg_price'] = total_value / total_qty
                holding['invested_inr'] = total_value * holding['fx_rate']
            else:
                holding['avg_price'] = 0.0
                holding['invested_inr'] = 0.0
    
    return holdings


def calculate_portfolio_summary(df=None):
    """
    Calculate complete portfolio summary including all metrics
    Returns a dictionary with all portfolio metrics
    """
    try:
        # Load data if not provided
        if df is None:
            df = load_trade_data()
        
        # Get currently held tickers
        currently_held_tickers = get_currently_held_tickers(df)
        
        if not currently_held_tickers:
            return None
        
        # Get market data
        market_data, company_names, previous_close_data = get_market_data(df, currently_held_tickers)
        
        # Calculate metrics
        ticker_list = df['Ticker'].unique().tolist()
        total_invested_inr = 0.0
        current_value_inr = 0.0
        previous_day_value_inr = 0.0
        total_realized_profit = 0.0
        
        cash_flows = []
        cash_flow_dates = []
        holdings_count = 0
        
        for ticker in ticker_list:
            ticker_trades = df[df['Ticker'] == ticker]
            
            buy_qty = ticker_trades[ticker_trades['Type'] == 'BUY']['Qty'].sum()
            sell_qty = ticker_trades[ticker_trades['Type'] == 'SELL']['Qty'].sum()
            
            buys_only = ticker_trades[ticker_trades['Type'] == 'BUY']
            sells_only = ticker_trades[ticker_trades['Type'] == 'SELL']
            
            fx_rate = ticker_trades['Exchange_Rate'].iloc[0]
            
            # Add to cash flows
            for _, buy in buys_only.iterrows():
                cash_flows.append(-(buy['Qty'] * buy['Price'] * fx_rate))
                cash_flow_dates.append(buy['Date'].date())
            
            for _, sell in sells_only.iterrows():
                cash_flows.append(sell['Qty'] * sell['Price'] * fx_rate)
                cash_flow_dates.append(sell['Date'].date())
            
            # Calculate realized profit
            if not sells_only.empty and not buys_only.empty:
                avg_buy_price = (buys_only['Price'] * buys_only['Qty']).sum() / buy_qty
                
                for _, sell in sells_only.iterrows():
                    sell_revenue = sell['Qty'] * sell['Price'] * fx_rate
                    sell_cost = sell['Qty'] * avg_buy_price * fx_rate
                    realized_profit = sell_revenue - sell_cost
                    total_realized_profit += realized_profit
            
            current_qty = buy_qty - sell_qty
            
            # Process current holdings
            if current_qty >= 0.001 and ticker in currently_held_tickers:
                if ticker in market_data and market_data[ticker] is not None:
                    current_price = market_data[ticker]
                    holdings_count += 1
                else:
                    continue
                
                fx_rate = ticker_trades['Exchange_Rate'].iloc[0]
                buys_only = ticker_trades[ticker_trades['Type'] == 'BUY']
                avg_buy_price = (buys_only['Price'] * buys_only['Qty']).sum() / buy_qty
                
                invested_amt = float(current_qty) * float(avg_buy_price) * float(fx_rate)
                current_amt = float(current_qty) * float(current_price) * float(fx_rate)
                
                prev_close_price = previous_close_data.get(ticker, current_price)
                previous_day_amt = float(current_qty) * float(prev_close_price) * float(fx_rate)
                
                total_invested_inr += invested_amt
                current_value_inr += current_amt
                previous_day_value_inr += previous_day_amt
        
        # Add current portfolio value to cash flows
        if current_value_inr > 0:
            cash_flows.append(current_value_inr)
            cash_flow_dates.append(date.today())
        
        # Calculate XIRR
        try:
            portfolio_xirr = xirr(cash_flow_dates, cash_flows)
            xirr_percentage = portfolio_xirr * 100 if portfolio_xirr else 0
        except:
            xirr_percentage = 0
        
        # Calculate daily change
        daily_change_inr = current_value_inr - previous_day_value_inr
        daily_change_pct = ((current_value_inr - previous_day_value_inr) / previous_day_value_inr) * 100 if previous_day_value_inr > 0 else 0
        
        # Calculate unrealized P&L
        total_unrealized_pl = current_value_inr - total_invested_inr
        unrealized_pl_pct = (total_unrealized_pl / total_invested_inr) * 100 if total_invested_inr > 0 else 0
        
        return {
            'total_invested': total_invested_inr,
            'current_value': current_value_inr,
            'unrealized_pl': total_unrealized_pl,
            'unrealized_pl_pct': unrealized_pl_pct,
            'realized_profit': total_realized_profit,
            'daily_change': daily_change_inr,
            'daily_change_pct': daily_change_pct,
            'xirr': xirr_percentage,
            'holdings_count': holdings_count
        }
        
    except Exception as e:
        print(f"❌ Error calculating portfolio summary: {str(e)}")
        return None


def calculate_detailed_portfolio(df=None, force_full_recalc=False):
    """
    Calculate detailed portfolio holdings with individual stock data
    Uses year-end snapshots for optimization when available
    
    Args:
        df: Optional pre-loaded dataframe
        force_full_recalc: If True, ignore snapshots and process full tradebook
    
    Returns a tuple of (portfolio_rows, summary_metrics, df)
    
    portfolio_rows: List of dictionaries with detailed holdings data
    summary_metrics: Dictionary with portfolio-level metrics
    df: The loaded dataframe (for trade book display)
    """
    try:
        # Load data with snapshot optimization
        if df is None:
            full_df, snapshot_df, snapshot_year, calc_df = load_trade_data_with_snapshot(force_full_recalc)
        else:
            full_df = df
            calc_df = df
            snapshot_df = None
            snapshot_year = None
        
        # Determine which dataframe to use for calculations
        # Use snapshot + incremental if available, otherwise use full tradebook
        use_snapshot = snapshot_df is not None and not force_full_recalc
        
        if use_snapshot:
            # Apply incremental trades to snapshot
            holdings = apply_incremental_trades(snapshot_df, calc_df)
            
            # Get list of currently held tickers
            currently_held_tickers = [ticker for ticker, data in holdings.items() if data['qty'] >= 0.02]
            
            # Calculate cash flows from snapshot + incremental
            cash_flows = []
            cash_flow_dates = []
            total_realized_profit = sum(data['realized_profit'] for data in holdings.values())
            
            # Add cash flows from incremental trades only (snapshot already accounts for history)
            if not calc_df.empty:
                for ticker in calc_df['Ticker'].unique():
                    ticker_trades = calc_df[calc_df['Ticker'] == ticker]
                    fx_rate = ticker_trades['Exchange_Rate'].iloc[0]
                    
                    for _, trade in ticker_trades.iterrows():
                        if trade['Type'] == 'BUY':
                            cash_flows.append(-(trade['Qty'] * trade['Price'] * fx_rate))
                            cash_flow_dates.append(trade['Date'].date())
                        elif trade['Type'] == 'SELL':
                            cash_flows.append(trade['Qty'] * trade['Price'] * fx_rate)
                            cash_flow_dates.append(trade['Date'].date())
        else:
            # Legacy calculation: process full tradebook
            holdings = {}
            currently_held_tickers_set = set(get_currently_held_tickers(calc_df))
            currently_held_tickers = list(currently_held_tickers_set)
            
            cash_flows = []
            cash_flow_dates = []
            total_realized_profit = 0.0
            
            ticker_list = calc_df['Ticker'].unique().tolist()
            
            for ticker in ticker_list:
                ticker_trades = calc_df[calc_df['Ticker'] == ticker]
                
                buy_qty = ticker_trades[ticker_trades['Type'] == 'BUY']['Qty'].sum()
                sell_qty = ticker_trades[ticker_trades['Type'] == 'SELL']['Qty'].sum()
                current_qty = buy_qty - sell_qty
                
                if current_qty < 0.02:
                    continue
                
                buys_only = ticker_trades[ticker_trades['Type'] == 'BUY']
                sells_only = ticker_trades[ticker_trades['Type'] == 'SELL']
                
                fx_rate = ticker_trades['Exchange_Rate'].iloc[0]
                currency = ticker_trades['Currency'].iloc[0]
                is_sgb = ticker_trades['Is_SGB'].iloc[0] if 'Is_SGB' in ticker_trades.columns else False
                
                # Add to cash flows
                for _, buy in buys_only.iterrows():
                    cash_flows.append(-(buy['Qty'] * buy['Price'] * fx_rate))
                    cash_flow_dates.append(buy['Date'].date())
                
                for _, sell in sells_only.iterrows():
                    cash_flows.append(sell['Qty'] * sell['Price'] * fx_rate)
                    cash_flow_dates.append(sell['Date'].date())
                
                # Calculate realized profit using FIFO
                realized_profit = 0.0
                if not sells_only.empty and not buys_only.empty:
                    sorted_trades = ticker_trades.sort_values('Date').reset_index(drop=True)
                    
                    buy_lots = []
                    for _, row in sorted_trades.iterrows():
                        if row['Type'] == 'BUY':
                            buy_lots.append({'qty': row['Qty'], 'price': row['Price']})
                    
                    for _, row in sorted_trades.iterrows():
                        if row['Type'] == 'SELL':
                            sell_qty_remaining = row['Qty']
                            sell_price = row['Price']
                            
                            for lot in buy_lots:
                                if sell_qty_remaining <= 0:
                                    break
                                    
                                if lot['qty'] > 0:
                                    qty_to_match = min(lot['qty'], sell_qty_remaining)
                                    
                                    sell_revenue = qty_to_match * sell_price * fx_rate
                                    sell_cost = qty_to_match * lot['price'] * fx_rate
                                    realized_profit += (sell_revenue - sell_cost)
                                    
                                    lot['qty'] -= qty_to_match
                                    sell_qty_remaining -= qty_to_match
                
                total_realized_profit += realized_profit
                
                # Calculate FIFO average price
                avg_buy_price = calculate_fifo_avg_price(ticker_trades)
                invested_amt_inr = float(current_qty) * float(avg_buy_price) * float(fx_rate)
                
                holdings[ticker] = {
                    'qty': current_qty,
                    'avg_price': avg_buy_price,
                    'invested_inr': invested_amt_inr,
                    'realized_profit': realized_profit,
                    'currency': currency,
                    'fx_rate': fx_rate,
                    'is_sgb': is_sgb
                }
        
        if not currently_held_tickers:
            return [], None, full_df
        
        # Get market data ONCE
        market_data, company_names, previous_close_data = get_market_data(full_df, currently_held_tickers)
        
        # Calculate portfolio metrics
        total_invested_inr = 0.0
        current_value_inr = 0.0
        previous_day_value_inr = 0.0
        holdings_count = 0
        portfolio_rows = []
        
        for ticker in currently_held_tickers:
            if ticker not in holdings:
                continue
            
            holding = holdings[ticker]
            current_qty = holding['qty']
            avg_buy_price = holding['avg_price']
            fx_rate = holding['fx_rate']
            currency = holding['currency']
            
            # Calculate invested amount (always available)
            invested_amt = float(current_qty) * float(avg_buy_price) * float(fx_rate)
            total_invested_inr += invested_amt
            
            # Check if we have current price data
            if ticker not in market_data or market_data[ticker] is None:
                # Missing price - use NaN for current values but still show the holding
                print(f"⚠️ Skipping P/L calculation for {ticker} due to missing price data")
                portfolio_rows.append({
                    "Ticker": ticker,
                    "Name": company_names.get(ticker, ticker),
                    "Qty": round(current_qty, 2),
                    "Avg Buy Price": round(avg_buy_price, 2),
                    "Current Price": float('nan'),
                    "Currency": currency,
                    "Invested Value (INR)": round(invested_amt, 2),
                    "Current Value (INR)": float('nan'),
                    "P&L (INR)": float('nan'),
                    "P/L %": float('nan')
                })
                continue
            
            # We have price data - calculate everything
            current_price = market_data[ticker]
            holdings_count += 1
            
            current_amt = float(current_qty) * float(current_price) * float(fx_rate)
            
            prev_close_price = previous_close_data.get(ticker, current_price)
            previous_day_amt = float(current_qty) * float(prev_close_price) * float(fx_rate)
            
            pl_amt = current_amt - invested_amt
            pl_percentage = ((current_amt - invested_amt) / invested_amt) * 100 if invested_amt > 0 else 0
            
            current_value_inr += current_amt
            previous_day_value_inr += previous_day_amt
            
            # Add to portfolio rows for display
            portfolio_rows.append({
                "Ticker": ticker,
                "Name": company_names.get(ticker, ticker),
                "Qty": round(current_qty, 2),
                "Avg Buy Price": round(avg_buy_price, 2),
                "Current Price": round(current_price, 2),
                "Currency": currency,
                "Invested Value (INR)": round(invested_amt, 2),
                "Current Value (INR)": round(current_amt, 2),
                "P&L (INR)": round(pl_amt, 2),
                "P/L %": round(pl_percentage, 2)
            })
        
        # Add current portfolio value to cash flows
        if current_value_inr > 0:
            cash_flows.append(current_value_inr)
            cash_flow_dates.append(date.today())
        
        # Calculate XIRR
        try:
            portfolio_xirr = xirr(cash_flow_dates, cash_flows)
            xirr_percentage = portfolio_xirr * 100 if portfolio_xirr else 0
        except:
            xirr_percentage = 0
        
        # Calculate daily change
        daily_change_inr = current_value_inr - previous_day_value_inr
        daily_change_pct = ((current_value_inr - previous_day_value_inr) / previous_day_value_inr) * 100 if previous_day_value_inr > 0 else 0
        
        # Calculate unrealized P&L
        total_unrealized_pl = current_value_inr - total_invested_inr
        unrealized_pl_pct = (total_unrealized_pl / total_invested_inr) * 100 if total_invested_inr > 0 else 0
        
        summary_metrics = {
            'total_invested': total_invested_inr,
            'current_value': current_value_inr,
            'unrealized_pl': total_unrealized_pl,
            'unrealized_pl_pct': unrealized_pl_pct,
            'realized_profit': total_realized_profit,
            'daily_change': daily_change_inr,
            'daily_change_pct': daily_change_pct,
            'xirr': xirr_percentage,
            'holdings_count': holdings_count
        }
        
        return portfolio_rows, summary_metrics, full_df
        
    except Exception as e:
        print(f"❌ Error calculating detailed portfolio: {str(e)}")
        import traceback
        traceback.print_exc()
        return [], None, None


def format_summary_message(summary):
    """Format portfolio summary as a Telegram message"""
    if not summary:
        return "❌ Unable to calculate portfolio summary"
    
    # Emoji indicators for positive/negative changes
    daily_emoji = "📈" if summary['daily_change'] >= 0 else "📉"
    unrealized_emoji = "💰" if summary['unrealized_pl'] >= 0 else "⚠️"
    
    message = f"""
📊 *SV's Portfolio Update*
━━━━━━━━━━━━━━━━━━━

💼 *Total Invested:* ₹{format_indian_number(summary['total_invested'])}
💎 *Current Value:* ₹{format_indian_number(summary['current_value'])}

{unrealized_emoji} *Unrealized P&L:* ₹{format_indian_number(summary['unrealized_pl'])} ({summary['unrealized_pl_pct']:.2f}%)
✅ *Realized Profit:* ₹{format_indian_number(summary['realized_profit'])}

{daily_emoji} *Daily Change:* ₹{format_indian_number(summary['daily_change'])} ({summary['daily_change_pct']:.2f}%)

📈 *XIRR:* {summary['xirr']:.2f}%
📦 *Holdings:* {summary['holdings_count']} stocks

━━━━━━━━━━━━━━━━━━━
_Updated: {date.today().strftime('%d %B %Y')}_
"""
    return message
