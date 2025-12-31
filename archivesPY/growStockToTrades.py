#!/usr/bin/env python3
"""Convert growStock2022To2025.csv into trades-format CSV.

Reads `growStock2022To2025.csv` and writes `trades2024EquityKite.csv` with columns:
  Date,Ticker,Country,Type,Qty,Price,Currency

Price is computed as `Value / Quantity` when Value appears to be total trade value.
Ticker suffix is set based on `Exchange` (NSE -> .NS, BSE -> .BO).
"""
from pathlib import Path
import pandas as pd
import sys


def clean_symbol(sym: str) -> str:
    if pd.isna(sym):
        return sym
    s = str(sym).strip()
    # Remove stray characters often present in exports
    s = s.replace('$', '').replace(' ', '')
    return s.upper()


def suffix_for_exchange(exchange: str) -> str:
    if pd.isna(exchange):
        return '.NS'
    e = str(exchange).upper()
    if 'NSE' in e:
        return '.NS'
    if 'BSE' in e:
        return '.BO'
    return '.NS'


def convert(input_path: Path, output_path: Path, overwrite=True):
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)

    # Expected columns: Stock name,Symbol,ISIN,Type,Quantity,Value,Exchange,Exchange Order Id,Execution date and time,Order status
    # Normalize columns
    cols = df.columns.tolist()
    # Ensure Execution date/time column exists
    date_col = None
    for c in cols:
        if 'Execution' in c or 'execution' in c or 'Execution date' in c:
            date_col = c
            break
    if date_col is None and 'Execution date and time' in cols:
        date_col = 'Execution date and time'

    if date_col is None:
        print('Could not find execution date column in input CSV')
        sys.exit(1)

    out = pd.DataFrame()
    # Parse date -> YYYY-MM-DD
    out['Date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')

    # Symbol -> add exchange suffix
    df['Symbol_clean'] = df.get('Symbol', df.get('symbol', pd.Series(['']*len(df)))).apply(clean_symbol)
    df['Exchange_clean'] = df.get('Exchange', df.get('exchange', pd.Series(['']*len(df))))
    out['Ticker'] = df.apply(lambda r: (r['Symbol_clean'] + suffix_for_exchange(r['Exchange_clean'])) if pd.notna(r['Symbol_clean']) else r.get('ISIN', ''), axis=1)

    out['Country'] = 'IND'
    out['Type'] = df.get('Type', df.get('type', pd.Series(['']*len(df)))).str.upper()

    # Qty from Quantity column
    qty_col = 'Quantity' if 'Quantity' in df.columns else ('quantity' if 'quantity' in df.columns else None)
    if qty_col is None:
        print('Could not find Quantity column')
        sys.exit(1)
    out['Qty'] = pd.to_numeric(df[qty_col].astype(str).str.replace(',',''), errors='coerce')

    # Price: prefer per-unit if provided, else compute Value/Quantity
    if 'Value' in df.columns:
        val = pd.to_numeric(df['Value'].astype(str).str.replace(',',''), errors='coerce')
        out['Price'] = (val / out['Qty']).round(6)
    else:
        out['Price'] = pd.NA

    out['Currency'] = 'INR'

    # Write output (overwrite if requested)
    if output_path.exists() and not overwrite:
        print(f"Output exists and overwrite=False: {output_path}")
        return

    out.to_csv(output_path, index=False)
    print(f"Saved {len(out)} rows to {output_path}")


if __name__ == '__main__':
    inp = Path('growStock2022To2025.csv')
    outp = Path('trades2022To2025EquityGrow.csv')
    convert(inp, outp, overwrite=True)
