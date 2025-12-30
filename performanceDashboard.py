import streamlit as st
import pandas as pd
import yfinance as yf
from pyxirr import xirr
from datetime import date
import glob
import os
import requests
def nse_get_advances_declines(*args, **kwargs):
    """Stub for `nse_get_advances_declines` to avoid importing heavy
    binary dependencies at module import time.

    Installing `nsepython` (and its dependencies like SciPy) is optional;
    this stub allows the dashboard to import and run in minimal
    environments. If full functionality is required, install `nsepython`
    in the project's environment and restart the app.
    """
    print("⚠️ nsepython not available at import time: nse_get_advances_declines stub called")
    return None

# --- PAGE SETUP ---
st.set_page_config(page_title="SV's Portfolio", layout="wide")
st.title("📊 SV's Stock Portfolio")

# --- HELPER FUNCTION: FORMAT NUMBER IN INDIAN STYLE ---
def format_indian_number(number):
    """Format number with Indian numbering system (lakhs and crores)"""
    s = str(int(round(number)))
    if len(s) <= 3:
        return s
    
    # Separate last 3 digits
    last_three = s[-3:]
    remaining = s[:-3]
    
    # Add commas every 2 digits from right to left for remaining digits
    result = ""
    while len(remaining) > 2:
        result = "," + remaining[-2:] + result
        remaining = remaining[:-2]
    
    if remaining:
        result = remaining + result
    
    return result + "," + last_three

# --- HELPER FUNCTION: GET SGB PRICE FROM NSE ---
@st.cache_data(ttl=3600)
def get_sgb_price(ticker):
    """Fetch SGB price from NSE using a lightweight requests call.

    This avoids importing `nsepython` (which pulls heavy binary
    dependencies). We call the NSE quote API directly and extract
    the last/close price if present.
    """
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }

        # NSE sometimes blocks rapid programmatic requests; use a simple
        # requests session and rely on the cache decorator to limit calls.
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

# --- HELPER FUNCTION: GET HISTORICAL EXCHANGE RATE ---
@st.cache_data
def get_exchange_rate(currency, trade_date):
    """Get historical exchange rate for a given currency and date"""
    if currency == 'INR':
        return 1.0
    
    try:
        # Fetch USD/INR rate from Yahoo Finance
        start_date = trade_date - pd.Timedelta(days=7)
        end_date = trade_date + pd.Timedelta(days=1)
        
        fx_data = yf.download('USDINR=X', start=start_date, end=end_date, progress=False)
        
        if not fx_data.empty:
            # Get the closest rate to the trade date and convert to float
            rate = float(fx_data['Close'].iloc[-1].iloc[0]) if hasattr(fx_data['Close'].iloc[-1], 'iloc') else float(fx_data['Close'].iloc[-1])
            return round(rate, 2)
        else:
            # Fallback to a recent rate if historical data not available
            fx_data = yf.Ticker('USDINR=X').history(period='5d')
            if not fx_data.empty:
                rate = float(fx_data['Close'].iloc[-1])
                return round(rate, 2)
    except:
        pass
    
    # Default fallback rate
    return 83.0

# --- STEP 1: LOAD DATA FROM MULTIPLE FILES ---
try:
    # Find all CSV files matching the pattern 'trades*.csv' and any file containing 'sgb'
    trade_files = glob.glob('trades*.csv')
    # Be filename-insensitive for SGB files (e.g., 'SGBs.csv', 'sgbs.csv')
    sgb_files = [f for f in glob.glob('*.csv') if 'sgb' in os.path.basename(f).lower()]

    all_files = trade_files + sgb_files
    
    if not all_files:
        st.error("❌ No trade files found. Please add files named 'trades*.csv' or 'SGBs.csv'")
        st.stop()
    
    # Display which files are being loaded (in terminal)
    print(f"📂 Loading {len(all_files)} file(s): {', '.join(all_files)}")
    
    # Read and combine all trade files
    df_list = []
    for file in all_files:
        try:
            temp_df = pd.read_csv(file, encoding='utf-8', on_bad_lines='skip')
            
            # Skip empty files
            if temp_df.empty:
                print(f"⚠️ Skipping empty file: {file}")
                continue
                
            temp_df['Source_File'] = file  # Track which file each trade came from
            
            # Mark SGB entries (filename-insensitive)
            if 'sgb' in os.path.basename(file).lower():
                temp_df['Is_SGB'] = True
                print(f"✅ Loaded {file} ({len(temp_df)} SGB trades)")
            else:
                temp_df['Is_SGB'] = False
                print(f"✅ Loaded {file} ({len(temp_df)} trades)")
            
            df_list.append(temp_df)
            
        except pd.errors.EmptyDataError:
            print(f"⚠️ Skipping empty file: {file}")
        except Exception as e:
            print(f"⚠️ Error reading {file}: {str(e)}")
    
    if not df_list:
        st.error("❌ Could not load any trade files successfully.")
        st.stop()
    
    # Combine all dataframes into one
    df = pd.concat(df_list, ignore_index=True)
    print(f"✅ Total trades loaded: {len(df)}")
    
    # Check if we have any SGBs
    if 'Is_SGB' in df.columns:
        sgb_count = df['Is_SGB'].sum()
        print(f"📊 SGB trades found: {sgb_count}")
    
    # Normalize the Type column to uppercase (to handle 'Buy'/'BUY', 'Sell'/'SELL')
    df['Type'] = df['Type'].str.upper()
    
    # Convert 'Date' column to actual datetime objects so Python understands them
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Get historical exchange rates for each transaction
    with st.spinner('Fetching historical exchange rates...'):
        df['Exchange_Rate'] = df.apply(
            lambda row: get_exchange_rate(row['Currency'], row['Date']),
            axis=1
        )
except Exception as e:
    st.error(f"❌ Error reading CSV files: {str(e)}")
    st.stop()

# --- STEP 2: CALCULATE CURRENT HOLDINGS ---
# First, determine which tickers we currently hold
ticker_list = df['Ticker'].unique().tolist()
currently_held_tickers = []

for ticker in ticker_list:
    ticker_trades = df[df['Ticker'] == ticker]
    buy_qty = ticker_trades[ticker_trades['Type'] == 'BUY']['Qty'].sum()
    sell_qty = ticker_trades[ticker_trades['Type'] == 'SELL']['Qty'].sum()
    current_qty = buy_qty - sell_qty
    
    # Only include tickers with meaningful holdings (>= 0.02)
    if current_qty >= 0.02:
        currently_held_tickers.append(ticker)
        print(f"✅ Holding {ticker}: {current_qty:.4f} shares")
    else:
        print(f"⏭️ Skipping {ticker}: {current_qty:.4f} shares (below threshold)")

print(f"📊 Currently holding {len(currently_held_tickers)} out of {len(ticker_list)} tickers (ignoring fractional shares < 0.001)")

# --- STEP 3: GET LIVE PRICES FOR HELD STOCKS ONLY ---
if currently_held_tickers:
    with st.spinner('Fetching live prices and company names from Yahoo Finance and NSE...'):
        market_data = {}
        company_names = {}
        for ticker in currently_held_tickers:
            # Check if this is an SGB
            is_sgb = df[df['Ticker'] == ticker]['Is_SGB'].iloc[0] if 'Is_SGB' in df.columns else False
            
            if is_sgb:
                # Fetch SGB price from NSE
                try:
                    price = get_sgb_price(ticker)
                    if price:
                        market_data[ticker] = price
                        company_names[ticker] = f"{ticker} (Sovereign Gold Bond)"
                        print(f"✅ Fetched SGB {ticker} @ {price}")
                    else:
                            # Fallback: try to use the most recent trade price as an approximation
                            try:
                                recent_price = df[df['Ticker'] == ticker]['Price'].dropna().iloc[-1]
                                market_data[ticker] = float(recent_price)
                                company_names[ticker] = f"{ticker} (SGB - fallback to last trade price)"
                                print(f"⚠️ Could not fetch live SGB price for {ticker}; using last trade price {recent_price} as fallback")
                            except Exception:
                                market_data[ticker] = None
                                company_names[ticker] = f"{ticker} (SGB - Price Not Available)"
                                print(f"⚠️ Could not fetch price for SGB {ticker}")
                except Exception as e:
                    print(f"⚠️ Error fetching SGB {ticker}: {str(e)}")
                    market_data[ticker] = None
                    company_names[ticker] = f"{ticker} (SGB - Error)"
            else:
                # Fetch regular stock price from Yahoo Finance
                try:
                    # Use Ticker object for more reliable price fetching
                    stock = yf.Ticker(ticker)
                    # Get info which contains previousClose (last traded price)
                    info = stock.info
                    
                    # Get company name
                    company_name = (info.get('longName') or 
                                  info.get('shortName') or 
                                  ticker)
                    company_names[ticker] = company_name
                    
                    # Try multiple fields to get the most recent price
                    price = (info.get('currentPrice') or 
                            info.get('regularMarketPrice') or 
                            info.get('previousClose') or
                            info.get('regularMarketPreviousClose'))
                    
                    if price is None:
                        # Fallback: get historical data
                        hist = stock.history(period="1mo")
                        if not hist.empty:
                            price = hist['Close'].iloc[-1]
                    
                    market_data[ticker] = price
                    print(f"✅ Fetched {ticker}: {company_name} @ {price}")
                except Exception as e:
                    print(f"⚠️ Could not fetch price for {ticker}: {str(e)}")
                    market_data[ticker] = None
                    company_names[ticker] = ticker
    
    # --- STEP 4: CALCULATE HOLDINGS AND REALIZED PROFIT ---
    portfolio_rows = []
    total_invested_inr = 0.0
    current_value_inr = 0.0
    total_realized_profit = 0.0
    
    # Prepare cash flows for XIRR calculation
    cash_flows = []
    cash_flow_dates = []

    # Process ALL tickers for cash flows and realized profit calculation
    for ticker in ticker_list:
        # Filter the main table to get only trades for this specific stock
        ticker_trades = df[df['Ticker'] == ticker]
        
        # Calculate Total Buys and Sells
        buy_qty = ticker_trades[ticker_trades['Type'] == 'BUY']['Qty'].sum()
        sell_qty = ticker_trades[ticker_trades['Type'] == 'SELL']['Qty'].sum()
        
        # Calculate realized profit from sells
        buys_only = ticker_trades[ticker_trades['Type'] == 'BUY']
        sells_only = ticker_trades[ticker_trades['Type'] == 'SELL']
        
        # Get the exchange rate
        fx_rate = ticker_trades['Exchange_Rate'].iloc[0]
        
        # Add BUY transactions to cash flows (negative = money out)
        for _, buy in buys_only.iterrows():
            cash_flows.append(-(buy['Qty'] * buy['Price'] * fx_rate))
            cash_flow_dates.append(buy['Date'].date())
        
        # Add SELL transactions to cash flows (positive = money in)
        for _, sell in sells_only.iterrows():
            cash_flows.append(sell['Qty'] * sell['Price'] * fx_rate)
            cash_flow_dates.append(sell['Date'].date())
        
        if not sells_only.empty and not buys_only.empty:
            # Calculate average buy price
            avg_buy_price = (buys_only['Price'] * buys_only['Qty']).sum() / buy_qty
            
            # Calculate realized profit from all sells
            for _, sell in sells_only.iterrows():
                sell_revenue = sell['Qty'] * sell['Price'] * fx_rate
                sell_cost = sell['Qty'] * avg_buy_price * fx_rate
                realized_profit = sell_revenue - sell_cost
                total_realized_profit += realized_profit
        
        current_qty = buy_qty - sell_qty
        
        # Only process holdings for tickers we currently hold
        if current_qty >= 0.001 and ticker in currently_held_tickers:
            print(f"🔍 Processing {ticker} for holdings display: qty={current_qty:.4f}")
            
            # Get latest price from our Yahoo download
            if ticker in market_data and market_data[ticker] is not None:
                current_price = market_data[ticker]
                print(f"  ✅ Got price for {ticker}: {current_price}")
            else:
                print(f"  ⚠️ Could not fetch price for {ticker}, skipping...")
                continue
            
            # Get the exchange rate (taking the first one found for this ticker)
            fx_rate = ticker_trades['Exchange_Rate'].iloc[0]
            currency = ticker_trades['Currency'].iloc[0]

            # Calculate Average Buy Price
            # Formula: (Sum of all Buy Prices * Qty) / Total Qty Bought
            buys_only = ticker_trades[ticker_trades['Type'] == 'BUY']
            avg_buy_price = (buys_only['Price'] * buys_only['Qty']).sum() / buy_qty

            # Invested Amount (Qty * Avg Cost)
            invested_amt = float(current_qty) * float(avg_buy_price) * float(fx_rate)
            
            # Current Value (Qty * Current Market Price)
            current_amt = float(current_qty) * float(current_price) * float(fx_rate)
            
            # Calculate P/L
            pl_amt = current_amt - invested_amt
            
            # Calculate P/L percentage
            pl_percentage = ((current_amt - invested_amt) / invested_amt) * 100 if invested_amt > 0 else 0
            
            # Add to totals
            total_invested_inr += invested_amt
            current_value_inr += current_amt

            # Add to our list for the table (with 2 decimal point rounding)
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
            print(f"  ✅ Added {ticker} to portfolio display")
    
    # Add current portfolio value as final cash flow (positive = current value)
    if current_value_inr > 0:
        cash_flows.append(current_value_inr)
        cash_flow_dates.append(date.today())
    
    # Calculate XIRR
    try:
        portfolio_xirr = xirr(cash_flow_dates, cash_flows)
        xirr_percentage = portfolio_xirr * 100 if portfolio_xirr else 0
    except:
        xirr_percentage = 0

    # --- STEP 4: VISUALIZE ---
    # Top level metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Invested", f"₹{format_indian_number(total_invested_inr)}")
    col2.metric("Current Value", f"₹{format_indian_number(current_value_inr)}")
    
    # Calculate total unrealized P&L
    total_unrealized_pl = current_value_inr - total_invested_inr
    col3.metric("Unrealized P&L", f"₹{format_indian_number(total_unrealized_pl)}", delta=f"{format_indian_number(total_unrealized_pl)}")
    
    # Show realized profit from sells
    col4.metric("Realized Profit", f"₹{format_indian_number(total_realized_profit)}", delta=f"{format_indian_number(total_realized_profit)}")
    
    # Show XIRR
    col5.metric("XIRR", f"{xirr_percentage:.2f}%")

    st.markdown("---")
    
    # Create tabs for Portfolio and Trade Book
    tab1, tab2 = st.tabs(["📈 Portfolio Overview", "📖 Trade Book"])
    
    # --- TAB 1: PORTFOLIO OVERVIEW ---
    with tab1:
        st.subheader("Holdings Breakdown")
        
        # Create DataFrame from portfolio rows
        portfolio_df = pd.DataFrame(portfolio_rows)
        
        # Define a function to highlight rows where P/L% is between 5% and 10%
        def highlight_pl_range(row):
            # Extract the P/L% value (it's already a float)
            pl_value = row["P/L %"]
            
            # Check if P/L% is between 5 and 10
            if 5 <= pl_value <= 10:
                return ['background-color: #006400; color: white'] * len(row)  # Dark green with white text
            else:
                return [''] * len(row)
        
        # Apply styling and format numeric columns to 2 decimal places
        styled_df = portfolio_df.style.apply(highlight_pl_range, axis=1).format({
            "Qty": "{:.2f}",
            "Avg Buy Price": "{:.2f}",
            "Current Price": "{:.2f}",
            "Invested Value (INR)": "{:.2f}",
            "Current Value (INR)": "{:.2f}",
            "P&L (INR)": "{:.2f}",
            "P/L %": "{:.2f}"
        })
        st.dataframe(styled_df, height=900, hide_index=True)
    
    # --- TAB 2: TRADEBOOK ---
    with tab2:
        st.subheader("📖 Trade Book")
        
        # Sort trades by date (most recent first)
        df_sorted = df.sort_values('Date', ascending=False)
        
        # Pagination settings
        rows_per_page = 100
        total_trades = len(df_sorted)
        total_pages = (total_trades - 1) // rows_per_page + 1
        
        # Page selector
        if 'page_number' not in st.session_state:
            st.session_state.page_number = 1
        
        col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
        
        with col1:
            if st.button("⬅️ Previous") and st.session_state.page_number > 1:
                st.session_state.page_number -= 1
        
        with col2:
            st.markdown(f"<h4 style='text-align: center;'>Page {st.session_state.page_number} of {total_pages}</h4>", unsafe_allow_html=True)
        
        with col3:
            if st.button("Next ➡️") and st.session_state.page_number < total_pages:
                st.session_state.page_number += 1
        
        with col4:
            # Direct page jump
            jump_to_page = st.number_input(
                "Jump to page:",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.page_number,
                step=1,
                key="page_jump"
            )
            if jump_to_page != st.session_state.page_number:
                st.session_state.page_number = jump_to_page
                st.rerun()
        
        # Calculate start and end indices for current page
        start_idx = (st.session_state.page_number - 1) * rows_per_page
        end_idx = min(start_idx + rows_per_page, total_trades)
        
        # Display paginated trades
        page_data = df_sorted.iloc[start_idx:end_idx].copy()
        page_data['Date'] = page_data['Date'].dt.strftime('%Y-%m-%d')
        
        # Remove internal columns that shouldn't be displayed
        columns_to_drop = ['Is_SGB', 'Source_File', 'Country', 'Exchange_Rate']
        page_data = page_data.drop(columns=[col for col in columns_to_drop if col in page_data.columns])
        
        st.dataframe(page_data, use_container_width=True, height=3540, hide_index=True)
        
        st.caption(f"Showing trades {start_idx + 1} to {end_idx} of {total_trades} total trades")

else:
    st.warning("No tickers found in CSV.")