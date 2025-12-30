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
  - Daily Change with percentage
  - XIRR (Extended Internal Rate of Return)
- **Holdings Breakdown**: Detailed view of current holdings
- **Trade Book**: Paginated view of all transactions
- **📱 Telegram Notifications**: Get portfolio updates 3 times a day on Telegram (optional)

## Installation

1. Clone this repository
2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Dashboard

1. Update your trade CSV files (see CSV Format below)
2. Run the dashboard:
```bash
streamlit run performanceDashboard.py
```

### Setting Up Telegram Notifications (Optional)

To receive automated portfolio summaries on Telegram 3 times a day:

1. Follow the detailed setup guide in [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)
2. Quick start:
```bash
./start_notifier.sh
```

The notifier will send updates at:
- 9:00 AM (Morning update)
- 2:00 PM (Afternoon update)
- 6:00 PM (Evening update)

You can customize these times in your `.env` file.

## CSV Format

Your trade CSV files should have the following columns:
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
- python-telegram-bot (for notifications)
- schedule (for automated updates)
