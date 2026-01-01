#!/usr/bin/env python3
"""
Rebuild All - Complete Portfolio Data Reconstruction

This script performs a complete rebuild of:
1. Tradebook (from all CSV files)
2. Holdings snapshots (for all years)

Perfect for:
- After fixing historical trade data
- After major data corrections
- When you want to start fresh
- Periodic data validation

Does NOT:
- Fetch current prices (fast operation!)
- Modify source CSV files (safe to re-run)
- Require internet connection (uses historical data only)
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_step(step_num, total_steps, text):
    """Print a formatted step"""
    print(f"📋 Step {step_num}/{total_steps}: {text}")

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"   Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            # Indent output for better readability
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stderr:
            print(f"   {e.stderr}")
        return False

def main():
    print_header("🔄 COMPLETE PORTFOLIO DATA REBUILD")
    
    # Verify we're in the right directory
    if not os.path.exists('portfolio_calculator.py'):
        print("❌ Error: Must run from project root directory")
        print("   (the directory containing portfolio_calculator.py)")
        sys.exit(1)
    
    # Verify required directories exist
    if not os.path.exists('archivesCSV'):
        print("❌ Error: archivesCSV directory not found")
        sys.exit(1)
    
    if not os.path.exists('archivesPY/tradebook_builder.py'):
        print("❌ Error: archivesPY/tradebook_builder.py not found")
        sys.exit(1)
    
    # Check for trade files
    csv_dir = Path('archivesCSV')
    trade_files = list(csv_dir.glob('trades*.csv')) + list(csv_dir.glob('SGBs.csv'))
    
    if not trade_files:
        print("❌ Error: No trade CSV files found in archivesCSV/")
        print("   Looking for: trades*.csv or SGBs.csv")
        sys.exit(1)
    
    print(f"✅ Found {len(trade_files)} trade file(s) to process:")
    for f in sorted(trade_files):
        size_kb = f.stat().st_size / 1024
        print(f"   - {f.name} ({size_kb:.1f} KB)")
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This will:")
    print("   1. Delete tradebook.csv and tradebook_processed_files.json")
    print("   2. Rebuild tradebook from all trades*.csv files")
    print("   3. Delete old holdings snapshots")
    print("   4. Regenerate holdings snapshots (2022-2025)")
    print()
    
    # Show stats
    csv_files = [f for f in os.listdir('archivesCSV') if f.startswith('trades') and f.endswith('.csv')]
    total_trades = 0
    for file in csv_files:
        with open(os.path.join('archivesCSV', file), 'r') as f:
            total_trades += sum(1 for line in f) - 1  # Subtract header

    print(f"   - {len(csv_files)} trade file(s) found: {', '.join(csv_files)}")
    print(f"   - Total trades across all files: {total_trades:,}")
    
    response = input("\n   Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\n❌ Rebuild cancelled by user")
        sys.exit(0)
    
    total_steps = 4
    success = True
    
    # Step 1: Clean up existing files
    print_header("STEP 1: CLEANUP")
    print_step(1, total_steps, "Removing old tradebook and processing history")
    
    files_to_remove = [
        'archivesCSV/tradebook.csv',
        'archivesCSV/tradebook_processed_files.json'
    ]
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"   ✅ Removed: {file_path}")
        else:
            print(f"   ℹ️  Not found (OK): {file_path}")
    
    # Step 2: Rebuild tradebook
    print_header("STEP 2: REBUILD TRADEBOOK")
    print_step(2, total_steps, "Processing all trade CSV files")
    
    os.chdir('archivesCSV')
    success = run_command(
        'python3 ../archivesPY/tradebook_builder.py rebuild',
        "Building consolidated tradebook"
    )
    os.chdir('..')
    
    if not success:
        print("\n❌ Tradebook rebuild failed!")
        sys.exit(1)
    
    # Verify tradebook was created
    tradebook_path = 'archivesCSV/tradebook.csv'
    if not os.path.exists(tradebook_path):
        print("   ❌ Error: Tradebook was not created!")
        return False
    
    # Count trades
    with open(tradebook_path, 'r') as f:
        trade_count = sum(1 for line in f) - 1  # Subtract header
    
    print(f"   ✅ Successfully rebuilt tradebook with {trade_count:,} trades")
    
    # Step 3: Clean up old snapshots
    print_header("STEP 3: CLEANUP OLD SNAPSHOTS")
    print_step(3, total_steps, "Removing old holdings snapshots")
    
    snapshot_files = list(csv_dir.glob('holdings_snapshot_*.csv'))
    if snapshot_files:
        for snapshot in snapshot_files:
            os.remove(snapshot)
            print(f"   ✅ Removed: {snapshot.name}")
    else:
        print("   ℹ️  No old snapshots found")
    
    # Step 4: Regenerate snapshots
    print_header("STEP 4: REGENERATE SNAPSHOTS")
    print_step(4, total_steps, "Creating holdings snapshots for all years")
    
    success = run_command(
        'python3 archivesPY/generate_snapshots.py',
        "Generating snapshots from tradebook"
    )
    
    if not success:
        print("\n⚠️  Snapshot generation had issues, but tradebook is ready")
        print("   You can try running: python3 archivesPY/generate_snapshots.py")
    
    # Final summary
    print_header("✅ REBUILD COMPLETE!")
    
    # Check what we created
    new_snapshots = sorted(csv_dir.glob('holdings_snapshot_*.csv'))
    
    print("📊 Summary:")
    print(f"   Tradebook: {trade_count:,} trades")
    print(f"   Snapshots: {len(new_snapshots)} files created")
    
    if new_snapshots:
        print("\n   Snapshot files:")
        for snapshot in new_snapshots:
            print(f"   - {snapshot.name}")
    
    print("\n🎯 Next Steps:")
    print("   1. Verify data: python3 archivesPY/generate_snapshots.py verify archivesCSV/holdings_snapshot_2025.csv")
    print("   2. View dashboard: streamlit run performanceDashboard.py")
    
    print("\n✨ Your portfolio data has been completely rebuilt!")
    print("   All operations used historical data only (no API calls)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Rebuild cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
