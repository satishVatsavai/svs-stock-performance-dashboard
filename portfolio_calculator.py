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
from datetime import date
import glob
import os
import requests
from dotenv import load_dotenv
from tradebook_builder import load_or_create_tradebook

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
                    print(f"✅ Fetched SGB {ticker} from NSE @ {price_f}")
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
    """Load and combine all trade data from tradebook.csv (with automatic updates from new files)"""
    # Use the tradebook manager to load trades efficiently
    # Exchange rates are already calculated and stored in the tradebook
    df = load_or_create_tradebook()
    
    # Apply standard transformations
    df['Type'] = df['Type'].str.upper()
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Exchange_Rate is already in the tradebook, no need to recalculate!
    # If for some reason it's missing, fill with default
    if 'Exchange_Rate' not in df.columns:
        print("⚠️ Exchange_Rate column missing, adding defaults...")
        df['Exchange_Rate'] = df.apply(
            lambda row: get_exchange_rate(row['Currency'], row['Date']),
            axis=1
        )
    
    return df


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


def calculate_detailed_portfolio(df=None):
    """
    Calculate detailed portfolio holdings with individual stock data
    Returns a tuple of (portfolio_rows, summary_metrics, df)
    
    portfolio_rows: List of dictionaries with detailed holdings data
    summary_metrics: Dictionary with portfolio-level metrics
    df: The loaded dataframe (for trade book display)
    """
    try:
        # Load data if not provided
        if df is None:
            df = load_trade_data()
        
        # Get currently held tickers
        currently_held_tickers = get_currently_held_tickers(df)
        
        if not currently_held_tickers:
            return [], None, df
        
        # Get market data ONCE (shared between summary and detailed calculations)
        market_data, company_names, previous_close_data = get_market_data(df, currently_held_tickers)
        
        # Calculate metrics (similar to calculate_portfolio_summary but reusing market_data)
        ticker_list = df['Ticker'].unique().tolist()
        total_invested_inr = 0.0
        current_value_inr = 0.0
        previous_day_value_inr = 0.0
        total_realized_profit = 0.0
        
        cash_flows = []
        cash_flow_dates = []
        holdings_count = 0
        portfolio_rows = []
        
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
                currency = ticker_trades['Currency'].iloc[0]
                buys_only = ticker_trades[ticker_trades['Type'] == 'BUY']
                avg_buy_price = (buys_only['Price'] * buys_only['Qty']).sum() / buy_qty
                
                invested_amt = float(current_qty) * float(avg_buy_price) * float(fx_rate)
                current_amt = float(current_qty) * float(current_price) * float(fx_rate)
                
                prev_close_price = previous_close_data.get(ticker, current_price)
                previous_day_amt = float(current_qty) * float(prev_close_price) * float(fx_rate)
                
                pl_amt = current_amt - invested_amt
                pl_percentage = ((current_amt - invested_amt) / invested_amt) * 100 if invested_amt > 0 else 0
                
                total_invested_inr += invested_amt
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
        
        return portfolio_rows, summary_metrics, df
        
    except Exception as e:
        print(f"❌ Error calculating detailed portfolio: {str(e)}")
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
