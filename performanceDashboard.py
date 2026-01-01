import streamlit as st
import pandas as pd
from datetime import date
from portfolio_calculator import calculate_detailed_portfolio, format_indian_number, calculate_xirr_per_year

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

@st.cache_data(ttl=300)  # Cache for 5 minutes (300 seconds)
def load_portfolio_data(force_recalc=False):
    """Load and calculate portfolio data with caching to avoid repeated API calls"""
    return calculate_detailed_portfolio(force_full_recalc=force_recalc)

@st.cache_data(ttl=3600)  # Cache for 1 hour (3600 seconds)
def load_yearly_xirr_data():
    """Load per-year XIRR data with caching"""
    return calculate_xirr_per_year()

# --- PAGE SETUP ---
st.set_page_config(page_title="SV's Portfolio", layout="wide")

# Add refresh and force recalc buttons in the header
col_title, col_recalc, col_refresh = st.columns([5, 1, 1])
with col_title:
    st.title("📊 SV's Stock Portfolio")
with col_recalc:
    if st.button("🔄 Full Recalc", help="Force full recalculation (ignore snapshots)"):
        st.cache_data.clear()
        st.session_state['force_recalc'] = True
        st.rerun()
with col_refresh:
    if st.button("💰 Refresh Prices", help="Fetch latest stock prices"):
        st.cache_data.clear()
        st.session_state.pop('force_recalc', None)
        st.rerun()

# --- STEP 1: LOAD AND CALCULATE PORTFOLIO ---
try:
    # Check if force recalc is requested
    force_recalc = st.session_state.get('force_recalc', False)
    
    with st.spinner('Loading portfolio data and fetching live prices...'):
        # Use the cached function to avoid refetching on every page change
        portfolio_rows, summary_metrics, df = load_portfolio_data(force_recalc)
        
        # Clear force recalc flag after use
        if force_recalc:
            st.session_state.pop('force_recalc', None)
    
    if not portfolio_rows or not summary_metrics or df is None:
        st.error("❌ No portfolio data available. Please check your CSV files.")
        st.stop()
    
    # --- STEP 2: DISPLAY METRICS ---
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Invested", f"₹{format_indian_number(summary_metrics['total_invested'])}")
    col2.metric("Current Value", f"₹{format_indian_number(summary_metrics['current_value'])}")
    col3.metric("Unrealized P&L", f"₹{format_indian_number(summary_metrics['unrealized_pl'])}")
    col4.metric("Realized Profit", f"₹{format_indian_number(summary_metrics['realized_profit'])}")
    col5.metric("Daily Change", 
                f"₹{format_indian_number(summary_metrics['daily_change'])}", 
                delta=f"{summary_metrics['daily_change_pct']:.2f}%")
    col6.metric("XIRR", f"{summary_metrics['xirr']:.2f}%")
    
    st.markdown("---")
    
    # --- STEP 3: CREATE TABS ---
    tab1, tab2, tab3 = st.tabs(["📈 Portfolio Overview", "📅 Per-Year XIRR", "📖 Trade Book"])
    
    # --- TAB 1: PORTFOLIO OVERVIEW ---
    with tab1:
        st.subheader("Holdings Breakdown")
        
        # Create DataFrame from portfolio rows
        portfolio_df = pd.DataFrame(portfolio_rows)
        
        # Define a function to highlight rows where P/L% is between 5% and 10%
        def highlight_pl_range(row):
            pl_value = row["P/L %"]
            # Skip highlighting if P/L% is NaN (missing price data)
            if pd.isna(pl_value):
                return ['background-color: #FFA500; color: white'] * len(row)  # Orange for missing data
            elif 5 <= pl_value <= 10:
                return ['background-color: #006400; color: white'] * len(row)
            else:
                return [''] * len(row)
        
        # Apply styling and format numeric columns
        styled_df = portfolio_df.style.apply(highlight_pl_range, axis=1).format({
            "Qty": "{:.2f}",
            "Avg Buy Price": "{:.2f}",
            "Current Price": lambda x: "N/A" if pd.isna(x) else f"{x:.2f}",
            "Invested Value (INR)": "{:.2f}",
            "Current Value (INR)": lambda x: "N/A" if pd.isna(x) else f"{x:.2f}",
            "P&L (INR)": lambda x: "N/A" if pd.isna(x) else f"{x:.2f}",
            "P/L %": lambda x: "N/A" if pd.isna(x) else f"{x:.2f}"
        })
        
        # Calculate dynamic height: header (38px) + rows (35px each) + padding (10px)
        table_height = min(38 + (len(portfolio_df) * 35) + 10, 2000)
        st.dataframe(styled_df, width="stretch", height=table_height, hide_index=True)
        
        # Add a note about missing data
        missing_count = portfolio_df["Current Price"].isna().sum()
        if missing_count > 0:
            st.warning(f"⚠️ {missing_count} holding(s) with missing price data (highlighted in orange). P/L and XIRR calculations exclude these holdings.")
    
    # --- TAB 2: PER-YEAR XIRR ---
    with tab2:
        st.subheader("📅 Per-Year XIRR Performance")
        
        with st.spinner('Calculating per-year XIRR...'):
            yearly_data = load_yearly_xirr_data()
        
        if not yearly_data:
            st.warning("⚠️ No yearly XIRR data available. Run `python3 archivesPY/generate_snapshots.py` to create snapshots.")
        else:
            # Display summary metrics
            st.markdown("### 📊 Cumulative XIRR Summary")
            st.info("**Note:** Each year shows cumulative return from your FIRST investment up to that year-end, NOT the isolated return for that year.")
            
            # Create columns for key metrics
            latest = yearly_data[-1]
            earliest = yearly_data[0]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current XIRR", f"{latest['xirr']:.2f}%", 
                       delta=f"{latest['xirr'] - earliest['xirr']:+.2f}% from {earliest['year']}")
            col2.metric("Total Invested", f"₹{format_indian_number(latest['total_invested'])}")
            col3.metric("Portfolio Value", f"₹{format_indian_number(latest['year_end_value'])}")
            col4.metric("Total Returns", f"₹{format_indian_number(latest['total_returns'])}")
            
            st.markdown("---")
            
            # Create a detailed table
            st.markdown("### 📈 Year-by-Year Breakdown")
            
            table_data = []
            for data in yearly_data:
                year = data['year']
                xirr_val = data['xirr']
                invested = data['total_invested']
                returns = data['total_returns']
                value = data['year_end_value']
                holdings = data['holdings_count']
                trades = data['cash_flows_count']
                period_days = data.get('period_days', 0)
                period_years = period_days / 365.25
                first_date = data.get('first_investment_date', 'N/A')
                
                # Calculate absolute gain
                abs_gain = value - invested + returns
                
                # Emoji for performance
                if xirr_val >= 20:
                    emoji = "🚀"
                elif xirr_val >= 15:
                    emoji = "📈"
                elif xirr_val >= 10:
                    emoji = "✅"
                elif xirr_val >= 0:
                    emoji = "➡️"
                else:
                    emoji = "📉"
                
                table_data.append({
                    "Status": emoji,
                    "Year": year,
                    "XIRR %": f"{xirr_val:.2f}%",
                    "Period (Years)": f"{period_years:.1f}",
                    "From Date": first_date,
                    "Total Invested": f"₹{format_indian_number(invested)}",
                    "Total Returns": f"₹{format_indian_number(returns)}",
                    "Portfolio Value": f"₹{format_indian_number(value)}",
                    "Absolute Gain": f"₹{format_indian_number(abs_gain)}",
                    "Holdings": holdings,
                    "Transactions": trades
                })
            
            xirr_df = pd.DataFrame(table_data)
            
            # Style the dataframe
            def highlight_xirr(row):
                xirr_str = row["XIRR %"]
                try:
                    xirr_val = float(xirr_str.replace('%', ''))
                    if xirr_val >= 20:
                        return ['background-color: #006400; color: white'] * len(row)  # Dark green
                    elif xirr_val >= 15:
                        return ['background-color: #228B22; color: white'] * len(row)  # Forest green
                    elif xirr_val >= 10:
                        return ['background-color: #32CD32; color: white'] * len(row)  # Lime green
                    elif xirr_val >= 5:
                        return ['background-color: #90EE90; color: black'] * len(row)  # Light green
                    elif xirr_val >= 0:
                        return ['background-color: #FFFFE0; color: black'] * len(row)  # Light yellow
                    else:
                        return ['background-color: #FFB6C1; color: black'] * len(row)  # Light red
                except:
                    return [''] * len(row)
            
            styled_xirr_df = xirr_df.style.apply(highlight_xirr, axis=1)
            st.dataframe(styled_xirr_df, width='stretch', hide_index=True)
            
            # Show year-over-year changes
            if len(yearly_data) > 1:
                st.markdown("---")
                st.markdown("### 📊 Year-over-Year XIRR Changes")
                
                yoy_data = []
                for i in range(1, len(yearly_data)):
                    prev = yearly_data[i-1]
                    curr = yearly_data[i]
                    xirr_change = curr['xirr'] - prev['xirr']
                    change_emoji = "📈" if xirr_change >= 0 else "📉"
                    
                    yoy_data.append({
                        "Trend": change_emoji,
                        "Period": f"{prev['year']} → {curr['year']}",
                        "Previous XIRR": f"{prev['xirr']:.2f}%",
                        "Current XIRR": f"{curr['xirr']:.2f}%",
                        "Change": f"{xirr_change:+.2f}%",
                        "Invested Change": f"₹{format_indian_number(curr['total_invested'] - prev['total_invested'])}",
                        "Value Change": f"₹{format_indian_number(curr['year_end_value'] - prev['year_end_value'])}"
                    })
                
                yoy_df = pd.DataFrame(yoy_data)
                
                # Style year-over-year changes
                def highlight_yoy(row):
                    change_str = row["Change"]
                    try:
                        change_val = float(change_str.replace('%', '').replace('+', ''))
                        if change_val > 0:
                            return ['background-color: #90EE90; color: black'] * len(row)  # Light green
                        elif change_val < 0:
                            return ['background-color: #FFB6C1; color: black'] * len(row)  # Light red
                        else:
                            return [''] * len(row)
                    except:
                        return [''] * len(row)
                
                styled_yoy_df = yoy_df.style.apply(highlight_yoy, axis=1)
                st.dataframe(styled_yoy_df, width='stretch', hide_index=True)
            
            # Add download button for the data
            st.markdown("---")
            import json
            json_data = json.dumps(yearly_data, indent=2)
            st.download_button(
                label="📥 Download Raw Data (JSON)",
                data=json_data,
                file_name=f"yearly_xirr_{date.today().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
            
            # Add explanatory note
            with st.expander("ℹ️ How to interpret this data"):
                st.markdown("""
                **Cumulative XIRR:**
                - Shows the annualized return from your **first investment** (inception) up to each year-end
                - This is NOT the isolated return for just that year
                - Example: If 2024 XIRR is 15.68%, it means your entire portfolio from inception to Dec 31, 2024 grew at 15.68% annually
                
                **Year-over-Year Changes:**
                - Shows how your cumulative XIRR improved or declined between years
                - Positive change = Better overall portfolio performance
                - Negative change = Portfolio growth rate slowed down
                
                **Price Sources:**
                - Year_End_Price: Actual market price stored in snapshot
                - tempCurrentPrices.csv: Cached prices from previous fetches
                - Book Value: Cost basis used when market price unavailable (may underestimate XIRR)
                
                **To improve accuracy:**
                - Run `python3 archivesPY/generate_snapshots.py` to regenerate snapshots with year-end prices
                """)
    
    # --- TAB 3: TRADEBOOK ---
    with tab3:
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
        
        # Remove internal columns
        columns_to_drop = ['Is_SGB', 'Source_File', 'Country', 'Exchange_Rate']
        page_data = page_data.drop(columns=[col for col in columns_to_drop if col in page_data.columns])
        
        st.dataframe(page_data, width='stretch', height=3540, hide_index=True)
        
        st.caption(f"Showing trades {start_idx + 1} to {end_idx} of {total_trades} total trades")

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.stop()