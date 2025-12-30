import streamlit as st
import pandas as pd
from datetime import date
from portfolio_calculator import calculate_detailed_portfolio, format_indian_number

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

# --- STEP 1: LOAD AND CALCULATE PORTFOLIO ---
try:
    with st.spinner('Loading portfolio data and fetching live prices...'):
        # Use the shared calculation function from portfolio_calculator
        portfolio_rows, summary_metrics, df = calculate_detailed_portfolio()
    
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
    tab1, tab2 = st.tabs(["📈 Portfolio Overview", "📖 Trade Book"])
    
    # --- TAB 1: PORTFOLIO OVERVIEW ---
    with tab1:
        st.subheader("Holdings Breakdown")
        
        # Create DataFrame from portfolio rows
        portfolio_df = pd.DataFrame(portfolio_rows)
        
        # Define a function to highlight rows where P/L% is between 5% and 10%
        def highlight_pl_range(row):
            pl_value = row["P/L %"]
            if 5 <= pl_value <= 10:
                return ['background-color: #006400; color: white'] * len(row)
            else:
                return [''] * len(row)
        
        # Apply styling and format numeric columns
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