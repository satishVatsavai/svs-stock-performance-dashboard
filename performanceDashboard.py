import streamlit as st
import pandas as pd
import yfinance as yf
from pyxirr import xirr
from datetime import date
import glob
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="SV's Portfolio", layout="wide")
st.title("📊 SV's Stock Portfolio")

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
    # Find all CSV files matching the pattern 'trades*.csv'
    trade_files = glob.glob('trades*.csv')
    
    if not trade_files:
        st.error("❌ No trade files found. Please add files named 'trades*.csv' (e.g., trades.csv, trades2024.csv, etc.)")
        st.stop()
    
    # Display which files are being loaded
    st.info(f"📂 Loading {len(trade_files)} file(s): {', '.join(trade_files)}")
    
    # Read and combine all trade files
    df_list = []
    for file in trade_files:
        try:
            temp_df = pd.read_csv(file, encoding='utf-8', on_bad_lines='skip')
            temp_df['Source_File'] = file  # Track which file each trade came from
            df_list.append(temp_df)
            st.success(f"✅ Loaded {file} ({len(temp_df)} trades)")
        except Exception as e:
            st.warning(f"⚠️ Error reading {file}: {str(e)}")
    
    if not df_list:
        st.error("❌ Could not load any trade files successfully.")
        st.stop()
    
    # Combine all dataframes into one
    df = pd.concat(df_list, ignore_index=True)
    
    # Convert 'Date' column to actual datetime objects so Python understands them
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Get historical exchange rates for each transaction
    with st.spinner('Fetching historical exchange rates...'):
        df['Exchange_Rate'] = df.apply(
            lambda row: get_exchange_rate(row['Currency'], row['Date']),
            axis=1
        )
    
    st.success(f"✅ Total trades loaded: {len(df)}")
except Exception as e:
    st.error(f"❌ Error reading CSV files: {str(e)}")
    st.stop()

# --- STEP 2: GET LIVE PRICES ---
# Get list of unique tickers to fetch from Yahoo Finance
ticker_list = df['Ticker'].unique().tolist()

if ticker_list:
    with st.spinner('Fetching live prices and company names from Yahoo Finance...'):
        market_data = {}
        company_names = {}
        for ticker in ticker_list:
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
            except Exception as e:
                st.warning(f"⚠️ Could not fetch price for {ticker}: {str(e)}")
                market_data[ticker] = None
                company_names[ticker] = ticker
    
    # --- STEP 3: CALCULATE HOLDINGS AND REALIZED PROFIT ---
    portfolio_rows = []
    total_invested_inr = 0.0
    current_value_inr = 0.0
    total_realized_profit = 0.0
    
    # Prepare cash flows for XIRR calculation
    cash_flows = []
    cash_flow_dates = []

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
        
        # Only process if we actually hold the stock
        if current_qty > 0:
            # Get latest price from our Yahoo download
            if ticker in market_data and market_data[ticker] is not None:
                current_price = market_data[ticker]
            else:
                st.warning(f"⚠️ Could not fetch price for {ticker}, skipping...")
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
            
            # Add to totals
            total_invested_inr += invested_amt
            current_value_inr += current_amt

            # Add to our list for the table
            portfolio_rows.append({
                "Ticker": ticker,
                "Name": company_names.get(ticker, ticker),
                "Qty": current_qty,
                "Avg Buy Price": round(avg_buy_price, 2),
                "Current Price": round(current_price, 2),
                "Currency": currency,
                "Invested (INR)": round(invested_amt, 2),
                "Current Value (INR)": round(current_amt, 2),
                "P&L (INR)": round(current_amt - invested_amt, 2)
            })
    
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
    col1.metric("Total Invested", f"₹{total_invested_inr:,.0f}")
    col2.metric("Current Value", f"₹{current_value_inr:,.0f}")
    
    # Calculate total unrealized P&L
    total_unrealized_pl = current_value_inr - total_invested_inr
    col3.metric("Unrealized P&L", f"₹{total_unrealized_pl:,.0f}", delta=f"{total_unrealized_pl:,.0f}")
    
    # Show realized profit from sells
    col4.metric("Realized Profit", f"₹{total_realized_profit:,.0f}", delta=f"{total_realized_profit:,.0f}")
    
    # Show XIRR
    col5.metric("XIRR", f"{xirr_percentage:.2f}%")

    st.markdown("---")
    
    # Detailed Dataframe
    st.subheader("Holdings Breakdown")
    st.dataframe(pd.DataFrame(portfolio_rows))
    
    st.markdown("---")
    
    # --- TRADEBOOK SECTION WITH PAGINATION ---
    st.subheader("📖 Trade Book")
    
    # Sort trades by date (most recent first)
    df_sorted = df.sort_values('Date', ascending=False)
    
    # Pagination settings
    rows_per_page = 10
    total_trades = len(df_sorted)
    total_pages = (total_trades - 1) // rows_per_page + 1
    
    # Page selector
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 1
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous") and st.session_state.page_number > 1:
            st.session_state.page_number -= 1
    
    with col2:
        st.markdown(f"<h4 style='text-align: center;'>Page {st.session_state.page_number} of {total_pages}</h4>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next ➡️") and st.session_state.page_number < total_pages:
            st.session_state.page_number += 1
    
    # Calculate start and end indices for current page
    start_idx = (st.session_state.page_number - 1) * rows_per_page
    end_idx = min(start_idx + rows_per_page, total_trades)
    
    # Display paginated trades
    page_data = df_sorted.iloc[start_idx:end_idx].copy()
    page_data['Date'] = page_data['Date'].dt.strftime('%Y-%m-%d')
    st.dataframe(page_data, use_container_width=True)
    
    st.caption(f"Showing trades {start_idx + 1} to {end_idx} of {total_trades} total trades")

else:
    st.warning("No tickers found in CSV.")