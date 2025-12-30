#!/usr/bin/env python3
import pandas as pd

# Reload the data to ensure state is fresh
df_2023eq = pd.read_csv("2023EQ.csv")

# Transform
df_transformed = df_2023eq.copy()
df_transformed['Date'] = df_transformed['trade_date']
df_transformed['Ticker'] = df_transformed['symbol'] + '.NS'
df_transformed['Country'] = 'IND'
df_transformed['Type'] = df_transformed['trade_type'].str.upper()
df_transformed['Qty'] = df_transformed['quantity'].astype(int)
df_transformed['Price'] = df_transformed['price']
df_transformed['Currency'] = 'INR'

# Select columns matching trades.csv
cols = ['Date', 'Ticker', 'Country', 'Type', 'Qty', 'Price', 'Currency']
df_final = df_transformed[cols]

# Verify counts
input_rows = len(df_2023eq)
output_rows = len(df_final)

print(f"Input rows: {input_rows}")
print(f"Output rows: {output_rows}")

# Save
output_filename = 'massaged_2023EQ_full.csv'
df_final.to_csv(output_filename, index=False)
print(f"Saved {output_rows} rows to {output_filename}")