"""
Portfolio Summary Calculator Module
Extracts portfolio calculation logic for reuse in dashboard and Telegram notifications
"""
import warnings
import logging
import os
# Suppress urllib3 SSL warning for macOS with LibreSSL
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')
# Suppress yfinance warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Suppress yfinance logger messages
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Check if logging is enabled via environment variable
ENABLE_LOGGING = os.environ.get('ENABLE_LOGGING', 'false').lower() in ('true', '1', 'yes')

def log(message):
    """Print log message only if logging is enabled"""
    if ENABLE_LOGGING:
        print(message)

import pandas as pd
from pyxirr import xirr
from datetime import date, datetime
import glob
import requests
from dotenv import load_dotenv
import time

# Import price fetching functions from centralized module
from price_fetcher import (
    fetch_price_with_fallback,
    load_backup_prices,
    save_backup_prices,
    fetch_sgb_price
)

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


def get_exchange_rate(currency, trade_date):
    """
    Get exchange rate for a given currency and date.
    
    Note: Exchange rates are pre-calculated and stored in tradebook.csv.
    This function is only used during tradebook building (archivesPY/tradebook_builder.py).
    
    For normal dashboard operation, rates are read directly from the Exchange_Rate column.
    """
    if currency == 'INR':
        return 1.0
    
    # Prompt user for the exchange rate
    log(f"\n💱 Exchange rate needed for {currency} on {trade_date.strftime('%Y-%m-%d')}")
    log(f"   Please look up the historical rate and enter it below.")
    log(f"   (You can find historical rates at: https://www.xe.com/currency-charts/)")
    
    while True:
        try:
            rate_input = input(f"   Enter USD to INR rate for {trade_date.strftime('%Y-%m-%d')}: ").strip()
            rate = float(rate_input)
            if rate > 0:
                log(f"✅ Using exchange rate: 1 USD = {rate} INR")
                return round(rate, 2)
            else:
                log("❌ Rate must be a positive number. Please try again.")
        except ValueError:
            log("❌ Invalid input. Please enter a numeric value (e.g., 83.50)")
        except KeyboardInterrupt:
            log("\n⚠️  Interrupted. Using fallback rate from .env")
            fallback_rate = float(os.getenv('FALLBACK_USD_INR_RATE', '83.0'))
            log(f"⚠️ Using fallback exchange rate from .env: 1 USD = {fallback_rate} INR")
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
    
    log(f"📂 Loading {tradebook_file}...")
    df = pd.read_csv(tradebook_file)
    log(f"   Loaded {len(df)} trades")
    
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
    Find and load the most recent holdings snapshot along with its cash flows
    
    Returns:
        tuple: (snapshot_df, snapshot_year, cash_flows, cash_flow_dates) 
               or (None, None, None, None) if no snapshots found
    """
    # Find all snapshot files
    snapshot_pattern = os.path.join(snapshot_dir, 'holdings_snapshot_*.csv')
    snapshot_files = glob.glob(snapshot_pattern)
    
    if not snapshot_files:
        return None, None, None, None
    
    # Extract years and find the latest
    snapshots_with_years = []
    for file in snapshot_files:
        try:
            year = int(file.split('_')[-1].replace('.csv', ''))
            snapshots_with_years.append((file, year))
        except ValueError:
            continue
    
    if not snapshots_with_years:
        return None, None, None, None
    
    # Get the latest snapshot
    latest_file, latest_year = max(snapshots_with_years, key=lambda x: x[1])
    
    log(f"📸 Loading snapshot: {os.path.basename(latest_file)}")
    snapshot_df = pd.read_csv(latest_file)
    log(f"   Snapshot date: {latest_year}-12-31")
    log(f"   Holdings in snapshot: {len(snapshot_df)} tickers")
    
    # Load corresponding cash flows
    import json
    cash_flows_file = os.path.join(snapshot_dir, f'cashflows_snapshot_{latest_year}.json')
    cash_flows = []
    cash_flow_dates = []
    
    if os.path.exists(cash_flows_file):
        try:
            with open(cash_flows_file, 'r') as f:
                cash_flows_data = json.load(f)
                cash_flows = cash_flows_data.get('cash_flows', [])
                cash_flow_dates_str = cash_flows_data.get('cash_flow_dates', [])
                # Convert date strings back to date objects
                cash_flow_dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in cash_flow_dates_str]
                log(f"   Cash flows loaded: {len(cash_flows)} transactions")
        except Exception as e:
            log(f"⚠️  Warning: Could not load cash flows from {cash_flows_file}: {e}")
            log(f"   Will calculate XIRR from full tradebook instead")
    else:
        log(f"⚠️  Cash flows file not found: {cash_flows_file}")
        log(f"   💡 Tip: Run 'python3 archivesPY/generate_snapshots.py' to regenerate with cash flows")
    
    return snapshot_df, latest_year, cash_flows, cash_flow_dates


def load_trade_data_with_snapshot(force_full_recalc=False):
    """
    Load trade data, using snapshots for optimization if available
    
    Args:
        force_full_recalc: If True, ignore snapshots and process full tradebook
    
    Returns:
        tuple: (df, snapshot_df, snapshot_year, incremental_df, cash_flows, cash_flow_dates)
            - df: Full tradebook dataframe (for display purposes)
            - snapshot_df: Holdings snapshot dataframe (or None)
            - snapshot_year: Year of the snapshot (or None)
            - incremental_df: Trades after snapshot (or full df if no snapshot)
            - cash_flows: Historical cash flows from snapshot (or None)
            - cash_flow_dates: Historical cash flow dates from snapshot (or None)
    """
    # Load full tradebook (always needed for display)
    df = load_trade_data()
    
    # Check if we should use snapshots
    if force_full_recalc:
        log("🔄 Force recalculation enabled - processing full tradebook")
        return df, None, None, df, None, None
    
    # Try to load latest snapshot (with cash flows)
    snapshot_df, snapshot_year, cash_flows, cash_flow_dates = get_latest_snapshot()
    
    if snapshot_df is None or snapshot_year is None:
        log("⚠️  No snapshots found - processing full tradebook")
        log("   💡 Tip: Run 'python3 archivesPY/generate_snapshots.py' to create snapshots")
        return df, None, None, df, None, None
    
    # Filter trades after the snapshot date
    snapshot_date = pd.Timestamp(f'{snapshot_year}-12-31 23:59:59')
    incremental_df = df[df['Date'] > snapshot_date].copy()
    
    if len(incremental_df) == 0:
        log(f"✅ No new trades since snapshot - using snapshot only")
    else:
        log(f"📊 Processing {len(incremental_df)} trades since {snapshot_year}-12-31")
        log(f"   (Skipped {len(df) - len(incremental_df)} historical trades)")
    
    return df, snapshot_df, snapshot_year, incremental_df, cash_flows, cash_flow_dates


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
    """Fetch current market prices for held tickers and cache them in archivesCSV/backupPrices.csv"""
    market_data = {}
    company_names = {}
    previous_close_data = {}
    
    # Load backup prices as fallback
    backup_prices, prev_backup_prices = load_backup_prices()
    
    # Track price sources for logging
    yahoo_success = []
    nse_success = []
    cached_used = []
    not_available = []
    
    for ticker in currently_held_tickers:
        is_sgb = df[df['Ticker'] == ticker]['Is_SGB'].iloc[0] if 'Is_SGB' in df.columns else False
        
        # Use the new unified price fetching function
        price, company_name, prev_close, source = fetch_price_with_fallback(ticker, is_sgb)
        
        if price is not None:
            market_data[ticker] = price
            company_names[ticker] = company_name
            previous_close_data[ticker] = prev_close
            
            # Track source for logging
            if source == 'yfinance':
                yahoo_success.append(ticker)
            elif source == 'nse':
                nse_success.append(ticker)
            elif source == 'cached':
                cached_used.append(ticker)
        else:
            # Price not available anywhere
            market_data[ticker] = None
            company_names[ticker] = company_name
            previous_close_data[ticker] = None
            not_available.append(ticker)
    
    # Detailed logging of price sources
    log("")
    log("📊 PRICE SOURCE SUMMARY")
    log("-" * 70)
    
    total_tickers = len(currently_held_tickers)
    
    if yahoo_success:
        log(f"✅ Yahoo Finance: {len(yahoo_success)}/{total_tickers} tickers")
        for ticker in yahoo_success[:5]:  # Show first 5
            log(f"   • {ticker}")
        if len(yahoo_success) > 5:
            log(f"   ... and {len(yahoo_success) - 5} more")
    
    if nse_success:
        log(f"✅ NSE API (SGBs): {len(nse_success)}/{total_tickers} tickers")
        for ticker in nse_success:
            log(f"   • {ticker}")
    
    if cached_used:
        log(f"💾 Cached (archivesCSV/backupPrices.csv): {len(cached_used)}/{total_tickers} tickers")
        for ticker in cached_used[:5]:  # Show first 5
            log(f"   • {ticker}")
        if len(cached_used) > 5:
            log(f"   ... and {len(cached_used) - 5} more")
    
    if not_available:
        log(f"❌ Not Available: {len(not_available)}/{total_tickers} tickers")
        for ticker in not_available:
            log(f"   • {ticker}")
    
    yahoo_failures = len(cached_used) + len(not_available)
    if yahoo_failures > 3:
        log(f"⚠️  Yahoo Finance rate limit hit {yahoo_failures} times")
    
    log("-" * 70)
    log("")
    
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
            
            # Calculate realized profit using FIFO (for ALL tickers, even fully sold)
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
                                total_realized_profit += (sell_revenue - sell_cost)
                                lot['qty'] -= qty_to_match
                                sell_qty_remaining -= qty_to_match
            
            current_qty = buy_qty - sell_qty
            
            # Process current holdings (for invested amount and current value)
            if current_qty >= 0.001 and ticker in currently_held_tickers:
                if ticker in market_data and market_data[ticker] is not None:
                    current_price = market_data[ticker]
                    holdings_count += 1
                else:
                    continue
                
                # Use FIFO for average price calculation
                avg_buy_price = calculate_fifo_avg_price(ticker_trades)
                
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
        else:
            log(f"⚠️  Current portfolio value is 0 - cannot calculate XIRR without end value")
        
        # Calculate XIRR
        try:
            if len(cash_flows) >= 2 and len(cash_flow_dates) >= 2 and current_value_inr > 0:
                portfolio_xirr = xirr(cash_flow_dates, cash_flows)
                if portfolio_xirr and portfolio_xirr != 0:
                    xirr_percentage = portfolio_xirr * 100
                    log(f"📈 XIRR calculated: {xirr_percentage:.2f}% (from {len(cash_flows)-1} transactions)")
                else:
                    log(f"⚠️ XIRR calculation returned {portfolio_xirr}")
                    xirr_percentage = 0
            else:
                if current_value_inr <= 0:
                    log(f"⚠️ Cannot calculate XIRR: current portfolio value is 0")
                else:
                    log(f"⚠️ Insufficient cash flows for XIRR: {len(cash_flows)} flows, {len(cash_flow_dates)} dates")
                xirr_percentage = 0
        except Exception as e:
            log(f"⚠️ XIRR calculation error: {str(e)}")
            import traceback
            if ENABLE_LOGGING:
                traceback.print_exc()
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
        log(f"❌ Error calculating portfolio summary: {str(e)}")
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
            full_df, snapshot_df, snapshot_year, calc_df, snapshot_cash_flows, snapshot_cash_flow_dates = load_trade_data_with_snapshot(force_full_recalc)
        else:
            full_df = df
            calc_df = df
            snapshot_df = None
            snapshot_year = None
            snapshot_cash_flows = None
            snapshot_cash_flow_dates = None
        
        # Determine which dataframe to use for calculations
        # Use snapshot + incremental if available, otherwise use full tradebook
        use_snapshot = snapshot_df is not None and not force_full_recalc
        
        # Initialize cash flows
        cash_flows = []
        cash_flow_dates = []
        total_realized_profit = 0.0
        
        if use_snapshot:
            # Apply incremental trades to snapshot
            holdings = apply_incremental_trades(snapshot_df, calc_df)
            
            # Get list of currently held tickers
            currently_held_tickers = [ticker for ticker, data in holdings.items() if data['qty'] >= 0.02]
            
            # Calculate total realized profit from snapshot + incremental
            # IMPORTANT: Snapshot only includes realized profit for tickers with remaining holdings
            # We need to add realized profit from fully sold tickers
            total_realized_profit_from_holdings = sum(data['realized_profit'] for data in holdings.values())
            
            # Calculate realized profit from fully sold tickers (not in snapshot)
            realized_profit_from_fully_sold = 0.0
            all_tickers = full_df['Ticker'].unique()
            
            for ticker in all_tickers:
                # Skip tickers that are still held (already counted above)
                if ticker in holdings:
                    continue
                
                # This ticker is fully sold - calculate its realized profit
                ticker_trades = full_df[full_df['Ticker'] == ticker].sort_values('Date')
                
                buy_qty = ticker_trades[ticker_trades['Type'] == 'BUY']['Qty'].sum()
                sell_qty = ticker_trades[ticker_trades['Type'] == 'SELL']['Qty'].sum()
                
                # Verify it's fully sold
                if buy_qty - sell_qty >= 0.001 or sell_qty == 0:
                    continue
                
                # Calculate realized profit using FIFO
                fx_rate = ticker_trades['Exchange_Rate'].iloc[0]
                buy_lots = []
                
                for _, row in ticker_trades.iterrows():
                    if row['Type'] == 'BUY':
                        buy_lots.append({'qty': row['Qty'], 'price': row['Price']})
                
                for _, row in ticker_trades.iterrows():
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
                                realized_profit_from_fully_sold += (sell_revenue - sell_cost)
                                lot['qty'] -= qty_to_match
                                sell_qty_remaining -= qty_to_match
            
            total_realized_profit = total_realized_profit_from_holdings + realized_profit_from_fully_sold
            
            log(f"💰 Realized Profit Breakdown:")
            log(f"   From holdings (snapshot): ₹{total_realized_profit_from_holdings:,.2f}")
            log(f"   From fully sold: ₹{realized_profit_from_fully_sold:,.2f}")
            log(f"   Total: ₹{total_realized_profit:,.2f}")
            
            # Use cash flows from snapshot if available
            if snapshot_cash_flows and snapshot_cash_flow_dates:
                log("💰 Using cached cash flows from snapshot for XIRR")
                cash_flows = list(snapshot_cash_flows)
                cash_flow_dates = list(snapshot_cash_flow_dates)
                log(f"   Snapshot cash flows: {len(cash_flows)} transactions")
                log(f"   Date range: {min(cash_flow_dates)} to {max(cash_flow_dates)}")
                log(f"   Total cash out (investments): ₹{sum(cf for cf in cash_flows if cf < 0):,.2f}")
                log(f"   Total cash in (returns): ₹{sum(cf for cf in cash_flows if cf > 0):,.2f}")
                
                # Add incremental cash flows (trades after snapshot)
                incremental_count = 0
                if not calc_df.empty:
                    for ticker in calc_df['Ticker'].unique():
                        ticker_trades = calc_df[calc_df['Ticker'] == ticker]
                        fx_rate = ticker_trades['Exchange_Rate'].iloc[0]
                        
                        for _, trade in ticker_trades.iterrows():
                            if trade['Type'] == 'BUY':
                                cash_flows.append(-(trade['Qty'] * trade['Price'] * fx_rate))
                                cash_flow_dates.append(trade['Date'].date())
                                incremental_count += 1
                            elif trade['Type'] == 'SELL':
                                cash_flows.append(trade['Qty'] * trade['Price'] * fx_rate)
                                cash_flow_dates.append(trade['Date'].date())
                                incremental_count += 1
                    if incremental_count > 0:
                        log(f"   Added {incremental_count} incremental cash flows")
            else:
                # Fallback: Calculate from full tradebook if cash flows not in snapshot
                log("⚠️  Snapshot doesn't have cash flows - calculating from full tradebook")
                for ticker in full_df['Ticker'].unique():
                    ticker_trades = full_df[full_df['Ticker'] == ticker]
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
            
            ticker_list = calc_df['Ticker'].unique().tolist()
            
            for ticker in ticker_list:
                ticker_trades = calc_df[calc_df['Ticker'] == ticker]
                
                buy_qty = ticker_trades[ticker_trades['Type'] == 'BUY']['Qty'].sum()
                sell_qty = ticker_trades[ticker_trades['Type'] == 'SELL']['Qty'].sum()
                current_qty = buy_qty - sell_qty
                
                buys_only = ticker_trades[ticker_trades['Type'] == 'BUY']
                sells_only = ticker_trades[ticker_trades['Type'] == 'SELL']
                
                fx_rate = ticker_trades['Exchange_Rate'].iloc[0]
                currency = ticker_trades['Currency'].iloc[0]
                is_sgb = ticker_trades['Is_SGB'].iloc[0] if 'Is_SGB' in ticker_trades.columns else False
                
                # Calculate realized profit using FIFO (for ALL tickers, even fully sold)
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
                
                # Add realized profit to total (even if ticker is fully sold)
                total_realized_profit += realized_profit
                
                # Skip adding to holdings if fully sold
                if current_qty < 0.02:
                    continue
                
                # Add to cash flows (only for current holdings for XIRR calculation)
                for _, buy in buys_only.iterrows():
                    cash_flows.append(-(buy['Qty'] * buy['Price'] * fx_rate))
                    cash_flow_dates.append(buy['Date'].date())
                
                for _, sell in sells_only.iterrows():
                    cash_flows.append(sell['Qty'] * sell['Price'] * fx_rate)
                    cash_flow_dates.append(sell['Date'].date())
                
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
                log(f"⚠️ Skipping P/L calculation for {ticker} due to missing price data")
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
        else:
            log(f"⚠️  Current portfolio value is 0 - cannot calculate XIRR without end value")
        
        # Calculate XIRR
        try:
            if len(cash_flows) >= 2 and len(cash_flow_dates) >= 2 and current_value_inr > 0:
                portfolio_xirr = xirr(cash_flow_dates, cash_flows)
                if portfolio_xirr and portfolio_xirr != 0:
                    xirr_percentage = portfolio_xirr * 100
                    log(f"📈 XIRR calculated: {xirr_percentage:.2f}% (from {len(cash_flows)-1} transactions)")
                else:
                    log(f"⚠️ XIRR calculation returned {portfolio_xirr}")
                    xirr_percentage = 0
            else:
                if current_value_inr <= 0:
                    log(f"⚠️ Cannot calculate XIRR: current portfolio value is 0")
                else:
                    log(f"⚠️ Insufficient cash flows for XIRR: {len(cash_flows)} flows, {len(cash_flow_dates)} dates")
                xirr_percentage = 0
        except Exception as e:
            log(f"⚠️ XIRR calculation error: {str(e)}")
            import traceback
            if ENABLE_LOGGING:
                traceback.print_exc()
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
        log(f"❌ Error calculating detailed portfolio: {str(e)}")
        import traceback
        if ENABLE_LOGGING:
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
