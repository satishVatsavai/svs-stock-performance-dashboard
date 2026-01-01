#!/usr/bin/env python3
"""
Sort tradebook.csv by date to ensure chronological order for FIFO calculations.
This makes it easier to append new trades and ensures consistent processing.
"""
import pandas as pd
import shutil
from datetime import datetime

def sort_tradebook():
    """Sort tradebook.csv by Date (newest first), with SELLs before BUYs on same date"""
    tradebook_file = 'tradebook.csv'
    backup_file = f'tradebook_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    print("=" * 80)
    print("Sorting tradebook.csv by Date (Reverse Chronological)")
    print("=" * 80)
    
    # Create backup
    print(f"\n📋 Creating backup: {backup_file}")
    shutil.copy2(tradebook_file, backup_file)
    print(f"   ✅ Backup created successfully")
    
    # Load tradebook
    print(f"\n📂 Loading {tradebook_file}...")
    df = pd.read_csv(tradebook_file)
    print(f"   Loaded {len(df)} trades")
    
    # Convert Date to datetime for sorting
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Create a sort key: SELL=0, BUY=1 (so SELLs come before BUYs on same date when descending)
    # This ensures that when we reverse for FIFO calculation, BUYs will be before SELLs
    df['Type_Sort'] = df['Type'].map({'SELL': 0, 'BUY': 1})
    
    # Sort by Date (descending - newest first), then by Type
    print(f"\n🔄 Sorting trades by date (newest first, SELLs before BUYs on same date)...")
    df_sorted = df.sort_values(['Date', 'Type_Sort'], ascending=[False, True]).reset_index(drop=True)
    
    # Remove the temporary sort column
    df_sorted = df_sorted.drop('Type_Sort', axis=1)
    
    # Format date back to string for CSV
    df_sorted['Date'] = df_sorted['Date'].dt.strftime('%Y-%m-%d')
    
    # Save sorted tradebook
    print(f"\n💾 Saving sorted tradebook...")
    df_sorted.to_csv(tradebook_file, index=False)
    
    print(f"\n✅ Tradebook sorted successfully!")
    print(f"\n📊 Summary:")
    print(f"   Total trades: {len(df_sorted)}")
    print(f"   Date range: {df_sorted['Date'].iloc[0]} (newest) to {df_sorted['Date'].iloc[-1]} (oldest)")
    print(f"   Backup saved as: {backup_file}")
    
    print("\n💡 Sort order:")
    print("   1. By Date (newest first - descending)")
    print("   2. SELLs before BUYs on same date")
    print("   3. Add new trades at the TOP of the file")
    
    print("\n" + "=" * 80)
    print("✅ Done! Your tradebook is now sorted (newest first).")
    print("   New trades can be appended at the TOP of the file.")
    print("=" * 80)

if __name__ == "__main__":
    try:
        sort_tradebook()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)
