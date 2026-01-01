"""
Holdings Snapshot Generator
Creates year-end snapshots of portfolio holdings for faster calculation
Includes cash flows for XIRR calculation
"""
import pandas as pd
from datetime import datetime, date
import os
import json


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


def generate_snapshot_for_year(df, year, output_dir='archivesCSV'):
    """
    Generate a holdings snapshot as of December 31st of the given year
    
    Args:
        df: Full tradebook dataframe
        year: Year to generate snapshot for (e.g., 2022, 2023, etc.)
        output_dir: Directory to save snapshot files
    
    Returns:
        Path to the created snapshot file
    """
    # Filter trades up to and including December 31st of the year
    cutoff_date = pd.Timestamp(f'{year}-12-31 23:59:59')
    df_filtered = df[df['Date'] <= cutoff_date].copy()
    
    if df_filtered.empty:
        print(f"⚠️  No trades found up to {year}-12-31. Skipping snapshot.")
        return None
    
    print(f"📅 Generating snapshot for year {year}...")
    print(f"   Processing {len(df_filtered)} trades up to {year}-12-31")
    
    # Get unique tickers
    ticker_list = df_filtered['Ticker'].unique().tolist()
    
    snapshot_data = []
    holdings_count = 0
    total_realized_profit = 0.0
    
    # Collect ALL cash flows up to this year (for XIRR calculation)
    all_cash_flows = []
    all_cash_flow_dates = []
    
    for ticker in ticker_list:
        ticker_trades = df_filtered[df_filtered['Ticker'] == ticker]
        
        # Calculate buy and sell quantities
        buy_qty = ticker_trades[ticker_trades['Type'] == 'BUY']['Qty'].sum()
        sell_qty = ticker_trades[ticker_trades['Type'] == 'SELL']['Qty'].sum()
        current_qty = buy_qty - sell_qty
        
        # Get currency and exchange rate (use the most recent one for this ticker)
        currency = ticker_trades['Currency'].iloc[-1]
        fx_rate = ticker_trades['Exchange_Rate'].iloc[-1]
        
        # Add this ticker's cash flows to the total
        for _, trade in ticker_trades.iterrows():
            if trade['Type'] == 'BUY':
                cash_flow = -(trade['Qty'] * trade['Price'] * trade['Exchange_Rate'])
                all_cash_flows.append(cash_flow)
                all_cash_flow_dates.append(trade['Date'].strftime('%Y-%m-%d'))
            elif trade['Type'] == 'SELL':
                cash_flow = trade['Qty'] * trade['Price'] * trade['Exchange_Rate']
                all_cash_flows.append(cash_flow)
                all_cash_flow_dates.append(trade['Date'].strftime('%Y-%m-%d'))
        
        # Only include if there are holdings at year-end
        if current_qty < 0.001:
            continue
        
        holdings_count += 1
        
        # Calculate FIFO average buy price of remaining holdings
        avg_buy_price = calculate_fifo_avg_price(ticker_trades)
        
        # Calculate total invested amount (in INR)
        invested_amt_inr = float(current_qty) * float(avg_buy_price) * float(fx_rate)
        
        # Calculate realized profit for this ticker (using FIFO)
        realized_profit = 0.0
        buys_only = ticker_trades[ticker_trades['Type'] == 'BUY']
        sells_only = ticker_trades[ticker_trades['Type'] == 'SELL']
        
        if not sells_only.empty and not buys_only.empty:
            # Sort trades by date for FIFO
            sorted_trades = ticker_trades.sort_values('Date').reset_index(drop=True)
            
            # Track buy lots for FIFO matching
            buy_lots = []
            for _, row in sorted_trades.iterrows():
                if row['Type'] == 'BUY':
                    buy_lots.append({'qty': row['Qty'], 'price': row['Price']})
            
            # Match sells against buys using FIFO
            for _, row in sorted_trades.iterrows():
                if row['Type'] == 'SELL':
                    sell_qty_remaining = row['Qty']
                    sell_price = row['Price']
                    
                    # Match this sell against buy lots in FIFO order
                    for lot in buy_lots:
                        if sell_qty_remaining <= 0:
                            break
                            
                        if lot['qty'] > 0:
                            qty_to_match = min(lot['qty'], sell_qty_remaining)
                            
                            # Calculate realized profit for this portion
                            sell_revenue = qty_to_match * sell_price * fx_rate
                            sell_cost = qty_to_match * lot['price'] * fx_rate
                            profit = sell_revenue - sell_cost
                            realized_profit += profit
                            
                            lot['qty'] -= qty_to_match
                            sell_qty_remaining -= qty_to_match
        
        total_realized_profit += realized_profit
        
        # Check if it's an SGB
        is_sgb = ticker_trades['Is_SGB'].iloc[-1] if 'Is_SGB' in ticker_trades.columns else False
        
        snapshot_data.append({
            'Ticker': ticker,
            'Qty': round(current_qty, 6),
            'Avg_Buy_Price': round(avg_buy_price, 6),
            'Total_Invested_INR': round(invested_amt_inr, 2),
            'Realized_Profit_INR': round(realized_profit, 2),
            'Currency': currency,
            'Exchange_Rate': round(fx_rate, 2),
            'Is_SGB': is_sgb
        })
    
    if not snapshot_data:
        print(f"⚠️  No holdings found as of {year}-12-31. Skipping snapshot.")
        return None
    
    # Create DataFrame
    snapshot_df = pd.DataFrame(snapshot_data)
    
    # Sort by ticker for easier viewing
    snapshot_df = snapshot_df.sort_values('Ticker').reset_index(drop=True)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save holdings to CSV
    output_file = os.path.join(output_dir, f'holdings_snapshot_{year}.csv')
    snapshot_df.to_csv(output_file, index=False)
    
    # Save cash flows to separate JSON file (for XIRR calculation)
    cash_flows_file = os.path.join(output_dir, f'cashflows_snapshot_{year}.json')
    cash_flows_data = {
        'year': year,
        'cutoff_date': f'{year}-12-31',
        'cash_flows': all_cash_flows,
        'cash_flow_dates': all_cash_flow_dates,
        'trade_count': len(df_filtered)
    }
    
    with open(cash_flows_file, 'w') as f:
        json.dump(cash_flows_data, f, indent=2)
    
    print(f"✅ Snapshot created: {output_file}")
    print(f"   Cash flows saved: {cash_flows_file}")
    print(f"   Holdings: {holdings_count} tickers")
    print(f"   Cash flows: {len(all_cash_flows)} transactions")
    print(f"   Total Invested: ₹{snapshot_df['Total_Invested_INR'].sum():,.2f}")
    print(f"   Total Realized Profit: ₹{total_realized_profit:,.2f}")
    print()
    
    return output_file


def generate_all_snapshots(tradebook_file='archivesCSV/tradebook.csv', start_year=2022, end_year=2025):
    """
    Generate snapshots for all years from start_year to end_year
    
    Args:
        tradebook_file: Path to the tradebook CSV file
        start_year: First year to generate snapshot for
        end_year: Last year to generate snapshot for (inclusive)
    """
    print("=" * 60)
    print("📸 HOLDINGS SNAPSHOT GENERATOR")
    print("=" * 60)
    print()
    
    # Load the full tradebook
    if not os.path.exists(tradebook_file):
        print(f"❌ Error: {tradebook_file} not found!")
        return
    
    print(f"📂 Loading {tradebook_file}...")
    df = pd.read_csv(tradebook_file)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Type'] = df['Type'].str.upper()
    
    print(f"   Loaded {len(df)} total trades")
    print(f"   Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    print()
    
    # Generate snapshots for each year
    snapshot_files = []
    for year in range(start_year, end_year + 1):
        snapshot_file = generate_snapshot_for_year(df, year)
        if snapshot_file:
            snapshot_files.append(snapshot_file)
    
    print("=" * 60)
    print(f"✅ Generated {len(snapshot_files)} snapshot(s)")
    print("=" * 60)
    
    if snapshot_files:
        print("\n📋 Created snapshots:")
        for file in snapshot_files:
            print(f"   • {file}")
        print("\n💡 Tip: portfolio_calculator.py will now use these snapshots")
        print("   to speed up calculations. Only trades after the latest")
        print("   snapshot will be processed in real-time!")


def verify_snapshot(snapshot_file):
    """
    Load and display summary of a snapshot file
    
    Args:
        snapshot_file: Path to snapshot CSV file
    """
    if not os.path.exists(snapshot_file):
        print(f"❌ Snapshot file not found: {snapshot_file}")
        return
    
    df = pd.read_csv(snapshot_file)
    year = snapshot_file.split('_')[-1].replace('.csv', '')
    
    print(f"\n📊 Snapshot Summary for {year}:")
    print(f"   Holdings: {len(df)} tickers")
    print(f"   Total Invested: ₹{df['Total_Invested_INR'].sum():,.2f}")
    print(f"   Total Realized Profit: ₹{df['Realized_Profit_INR'].sum():,.2f}")
    print(f"\n   Top 5 holdings by value:")
    
    top5 = df.nlargest(5, 'Total_Invested_INR')
    for _, row in top5.iterrows():
        print(f"      {row['Ticker']:12} {row['Qty']:8.2f} shares  ₹{row['Total_Invested_INR']:12,.2f}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'verify' and len(sys.argv) > 2:
            # Verify a specific snapshot
            verify_snapshot(sys.argv[2])
        elif command == 'single' and len(sys.argv) > 2:
            # Generate snapshot for a single year
            year = int(sys.argv[2])
            df = pd.read_csv('archivesCSV/tradebook.csv')
            df['Date'] = pd.to_datetime(df['Date'])
            df['Type'] = df['Type'].str.upper()
            generate_snapshot_for_year(df, year)
        else:
            print("Usage:")
            print("  python3 generate_snapshots.py              # Generate all snapshots (2022-2025)")
            print("  python3 generate_snapshots.py single 2024  # Generate snapshot for specific year")
            print("  python3 generate_snapshots.py verify archivesCSV/holdings_snapshot_2024.csv")
    else:
        # Default: generate all snapshots
        generate_all_snapshots()
