#!/usr/bin/env python3
"""
Test script to verify Year_End_Price functionality in snapshots
"""

import pandas as pd

def test_snapshot_prices():
    """Check which snapshots have Year_End_Price data"""
    print("=" * 70)
    print("🔍 CHECKING YEAR_END_PRICE IN SNAPSHOTS")
    print("=" * 70)
    print()
    
    for year in [2022, 2023, 2024, 2025]:
        snapshot_file = f'archivesCSV/holdings_snapshot_{year}.csv'
        try:
            df = pd.read_csv(snapshot_file)
            
            # Check if Year_End_Price column exists
            if 'Year_End_Price' in df.columns:
                total_holdings = len(df)
                with_prices = df['Year_End_Price'].notna().sum()
                without_prices = total_holdings - with_prices
                
                print(f"📅 Year {year}:")
                print(f"   Total Holdings: {total_holdings}")
                print(f"   ✅ With Year_End_Price: {with_prices}")
                print(f"   ⚠️  Without Year_End_Price: {without_prices}")
                
                if with_prices > 0:
                    # Show sample prices
                    sample = df[df['Year_End_Price'].notna()].head(3)
                    print(f"   📊 Sample prices:")
                    for _, row in sample.iterrows():
                        print(f"      {row['Ticker']}: {row.get('Currency', 'INR')} {row['Year_End_Price']:.2f}")
                print()
            else:
                print(f"❌ Year {year}: Year_End_Price column NOT FOUND")
                print(f"   💡 Run: python3 generate_snapshots.py")
                print()
        except FileNotFoundError:
            print(f"❌ Year {year}: Snapshot file not found")
            print()
        except Exception as e:
            print(f"❌ Year {year}: Error reading snapshot - {e}")
            print()

if __name__ == '__main__':
    print()
    test_snapshot_prices()
