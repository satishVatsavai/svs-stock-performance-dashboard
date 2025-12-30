#!/usr/bin/env python3
"""Convert Mutual Fund tradebook export into the local trades format.

Reads a MF export CSV (default: tradebook-BU5086-MF-2022.csv) and
produces `massaged_MF_trades.csv` with columns:
  Date,Ticker,Country,Type,Qty,Price,Currency

It attempts to resolve each fund `symbol` (scheme name) to a Yahoo
Finance symbol by calling Yahoo's search endpoint. If no suitable
symbol is found, it falls back to using the ISIN as the ticker.
"""
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
import pandas as pd


def yahoo_search_symbol(query):
    """Search Yahoo Finance and return list of quotes (may be empty).
    Uses the unofficial search endpoint `query2.finance.yahoo.com`.
    """
    url = "https://query2.finance.yahoo.com/v1/finance/search?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            return data.get("quotes", [])
    except Exception:
        return []


def resolve_ticker(name, isin=None):
    """Try to resolve a friendly fund `name` to a Yahoo symbol.
    Preference order:
      - first quote with quoteType indicating a fund/mutual fund
      - quote where exchange contains 'BSE'/'NSE' or symbol ends with '.BO'/.NS
      - first quote returned
    If none found, return ISIN (if provided) or original name.
    """
    quotes = yahoo_search_symbol(name)
    time.sleep(0.35)
    if not quotes:
        return isin or name

    # Prefer fund/ETF types
    for q in quotes:
        qt = q.get("quoteType", "").upper()
        if "FUND" in qt or qt == "MUTUALFUND" or qt == "ETF":
            return q.get("symbol")

    # Prefer exchange that looks like Indian (BSE/NSE) or symbol suffix
    for q in quotes:
        exch = (q.get("exchange") or "").upper()
        sym = q.get("symbol") or ""
        if any(x in exch for x in ("BSE", "NSE", "NS")) or sym.endswith(('.NS', '.BO', '.BSE')):
            return sym

    # Fallback to first quote symbol
    return quotes[0].get("symbol") or (isin or name)


def convert(input_path: Path, output_path: Path):
    df = pd.read_csv(input_path)

    # Expect the export to have at least these columns based on sample:
    # symbol (scheme name), isin, trade_date, trade_type, quantity, price
    src_cols = df.columns.tolist()
    required = ["symbol", "isin", "trade_date", "trade_type", "quantity", "price"]
    missing = [c for c in required if c not in src_cols]
    if missing:
        raise SystemExit(f"Missing expected columns in {input_path}: {missing}")

    # Resolve all unique tickers (scheme names)
    mapping = {}
    unique_names = df['symbol'].unique()
    print(f"Resolving {len(unique_names)} unique fund names via Yahoo search...")
    for i, name in enumerate(unique_names, 1):
        isin = df.loc[df['symbol'] == name, 'isin'].iloc[0] if 'isin' in df.columns else None
        ticker = resolve_ticker(name, isin=isin)
        mapping[name] = ticker
        print(f"[{i}/{len(unique_names)}] {name} -> {ticker}")

    # Build final DataFrame with desired columns
    out = pd.DataFrame()
    out['Date'] = pd.to_datetime(df['trade_date']).dt.date
    out['Ticker'] = df['symbol'].map(mapping)
    out['Country'] = 'IND'
    out['Type'] = df['trade_type'].str.upper()
    out['Qty'] = df['quantity']
    out['Price'] = df['price']
    out['Currency'] = 'INR'

    out.to_csv(output_path, index=False)
    print(f"Saved {len(out)} rows to {output_path}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Convert MF tradebook(s) to local format')
    parser.add_argument('inputs', nargs='*', help='Input CSV files to convert. If empty, all files matching "trades*MF*.csv" will be processed')
    args = parser.parse_args()

    files = args.inputs or [str(p) for p in Path('.').glob('trades*MF*.csv')]
    if not files:
        print('No input files provided and no files matching pattern "trades*MF*.csv" found in current directory.')
        raise SystemExit(1)

    for f in files:
        in_file = Path(f)
        if not in_file.exists():
            print(f"Skipping missing file: {in_file}")
            continue

        out_file = in_file.with_name('massaged_' + in_file.name)
        mapping_file = in_file.with_name('mapping_' + in_file.stem + '.csv')

        try:
            # Convert and get mapping via resolution step
            df = pd.read_csv(in_file)
            required = ["symbol", "isin", "trade_date", "trade_type", "quantity", "price"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                print(f"Skipping {in_file}: missing columns {missing}")
                continue

            unique_names = df['symbol'].unique()
            mapping = {}
            print(f"Resolving {len(unique_names)} unique fund names in {in_file}...")
            for i, name in enumerate(unique_names, 1):
                isin = df.loc[df['symbol'] == name, 'isin'].iloc[0] if 'isin' in df.columns else None
                ticker = resolve_ticker(name, isin=isin)
                mapping[name] = ticker
                print(f"[{i}/{len(unique_names)}] {name} -> {ticker}")

            out = pd.DataFrame()
            out['Date'] = pd.to_datetime(df['trade_date']).dt.date
            out['Ticker'] = df['symbol'].map(mapping)
            out['Country'] = 'IND'
            out['Type'] = df['trade_type'].str.upper()
            out['Qty'] = df['quantity']
            out['Price'] = df['price']
            out['Currency'] = 'INR'

            out.to_csv(out_file, index=False)
            print(f"Saved {len(out)} rows to {out_file}")

            # Save mapping for manual review
            with open(mapping_file, 'w', newline='', encoding='utf-8') as mf:
                writer = csv.writer(mf)
                writer.writerow(['SchemeName', 'ResolvedTicker'])
                for k, v in mapping.items():
                    writer.writerow([k, v])
            print(f"Saved mapping to {mapping_file}")

        except Exception as e:
            print(f"Error processing {in_file}: {e}")
