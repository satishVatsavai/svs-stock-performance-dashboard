#!/usr/bin/env python3
"""
Display current holdings with FIFO-calculated average buy price and units
"""

import pandas as pd
from portfolio_calculator import calculate_fifo_avg_price

def show_holdings():
    # Load tradebook
    df = pd.read_csv('tradebook.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Get unique tickers
    tickers = df['Ticker'].unique()
    
    holdings = []
    
    for ticker in tickers:
        ticker_trades = df[df['Ticker'] == ticker].copy()
        
        # Calculate totals
        total_buy = ticker_trades[ticker_trades['Type'] == 'BUY']['Qty'].sum()
        total_sell = ticker_trades[ticker_trades['Type'] == 'SELL']['Qty'].sum()
        net_qty = total_buy - total_sell
        
        # Only show if there are holdings
        if net_qty > 0:
            # Calculate FIFO average price
            avg_price = calculate_fifo_avg_price(ticker_trades)
            
            # Get currency
            currency = ticker_trades.iloc[0]['Currency']
            
            holdings.append({
                'Ticker': ticker,
                'Units': net_qty,
                'Avg Buy Price': avg_price,
                'Currency': currency,
                'Total Value': net_qty * avg_price
            })
    
    # Create DataFrame and sort by ticker
    holdings_df = pd.DataFrame(holdings)
    holdings_df = holdings_df.sort_values('Ticker')
    
    # Display
    print("\n" + "="*100)
    print("CURRENT HOLDINGS - FIFO METHOD")
    print("="*100)
    print(f"\nTotal Holdings: {len(holdings_df)} stocks\n")
    
    # Format output
    print(f"{'Ticker':<15} {'Units':>10} {'Avg Buy Price':>15} {'Currency':>10} {'Total Value':>18}")
    print("-"*100)
    
    for _, row in holdings_df.iterrows():
        ticker = row['Ticker']
        units = f"{row['Units']:,.0f}"
        avg_price = f"{row['Avg Buy Price']:,.2f}"
        currency = row['Currency']
        total_value = f"{row['Total Value']:,.2f}"
        
        print(f"{ticker:<15} {units:>10} {avg_price:>15} {currency:>10} {total_value:>18}")
    
    print("-"*100)
    
    # Calculate totals by currency
    print("\nTOTAL VALUE BY CURRENCY:")
    currency_totals = holdings_df.groupby('Currency')['Total Value'].sum()
    for currency, total in currency_totals.items():
        print(f"  {currency}: {total:,.2f}")
    
    print("\n" + "="*100)
    
    # Export to CSV for easy comparison
    holdings_df.to_csv('current_holdings_fifo.csv', index=False)
    print("\n✓ Holdings exported to: current_holdings_fifo.csv")
    print("\n")

if __name__ == "__main__":
    show_holdings()
