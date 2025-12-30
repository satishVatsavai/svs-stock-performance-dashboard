# Stock Performance Dashboard

A Streamlit-based portfolio tracker that fetches live stock prices and calculates portfolio performance metrics.

## Features

- **Live Stock Prices**: Fetches real-time prices from Yahoo Finance
- **Multi-Currency Support**: Automatically converts USD to INR using historical exchange rates
- **Portfolio Metrics**:
  - Total Invested Amount
  - Current Portfolio Value
  - Unrealized P&L (Paper gains/losses)
  - Realized Profit (From completed sell trades)
  - XIRR (Extended Internal Rate of Return)
- **Holdings Breakdown**: Detailed view of current holdings
- **Trade Book**: Paginated view of all transactions

## Installation

1. Clone this repository
2. Install required packages:
```bash
pip install streamlit pandas yfinance pyxirr
```

## Usage

1. Update `trades.csv` with your trades
2. Run the dashboard:
```bash
streamlit run performanceDashboard.py
```

## CSV Format

Your `trades.csv` should have the following columns:
- Date (YYYY-MM-DD)
- Ticker (e.g., AAPL, RELIANCE.NS)
- Country (e.g., USA, IND)
- Type (BUY or SELL)
- Qty (Quantity)
- Price (Price per share)
- Currency (USD or INR)

Exchange rates are automatically fetched based on the transaction date.

## Technologies Used

- Streamlit
- pandas
- yfinance
- pyxirr
