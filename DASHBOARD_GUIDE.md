# Stock Performance Dashboard Guide

## Overview

A Streamlit-based portfolio tracker that displays live stock prices and calculates comprehensive portfolio performance metrics.

## Features

- 📊 **Real-time Portfolio Metrics**
  - Total invested amount
  - Current portfolio value
  - Unrealized P&L (paper gains/losses)
  - Realized profit (from completed sells)
  - Daily change with percentage
  - XIRR (Extended Internal Rate of Return)

- 📈 **Holdings View**
  - Detailed breakdown of current positions
  - Live market prices
  - Per-stock P&L calculations
  - Sortable columns

- 📚 **Trade Book**
  - Complete transaction history
  - Paginated view
  - Date-sorted display

- 🌍 **Multi-Currency Support**
  - Automatic USD to INR conversion
  - Historical exchange rates for each trade
  - Consistent currency display

- ⚡ **Performance Optimized**
  - Smart caching (5-minute TTL)
  - Session state management
  - Rate-limited API calls
  - Handles 50+ holdings efficiently

## Quick Start

### Prerequisites

1. Python 3.8 or higher
2. Your tradebook must be ready (see `TRADEBOOK_GUIDE.md`)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/portfolio-dashboard.git
cd portfolio-dashboard

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
# Build/update your tradebook first
python3 tradebook_builder.py consolidate

# Start the dashboard
streamlit run performanceDashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Dashboard Sections

### 1. Portfolio Summary (Top Section)

**Metrics displayed:**

```
💼 Total Invested: ₹12,50,000
💎 Current Value: ₹15,75,000
💰 Unrealized P&L: ₹3,25,000 (26.00%)
✅ Realized Profit: ₹1,50,000
📈 Daily Change: ₹25,000 (1.61%)
📈 XIRR: 18.50%
📦 Holdings: 15 stocks
```

**Understanding the metrics:**

- **Total Invested**: Sum of all BUY transactions (excluding SELLs)
- **Current Value**: Sum of (quantity × current market price) for all holdings
- **Unrealized P&L**: Current Value - Total Invested (paper gains/losses)
- **Realized Profit**: Profit/loss from completed SELL transactions
- **Daily Change**: Today's movement in portfolio value
- **XIRR**: Annualized return rate considering cash flows and timing
- **Holdings**: Number of unique stocks currently held

### 2. Holdings Tab

**Interactive table showing:**

| Ticker | Company | Qty | Avg Buy | Current | Invested | Value | P&L | P&L % |
|--------|---------|-----|---------|---------|----------|-------|-----|-------|
| RELIANCE.NS | Reliance Ind. | 50 | ₹2,450 | ₹2,648 | ₹1,22,500 | ₹1,32,375 | ₹9,875 | 8.06% |

**Features:**
- ✅ Sortable columns (click headers)
- ✅ Live market prices
- ✅ Color-coded P&L (green for profit, red for loss)
- ✅ Formatted currency values
- ✅ Search/filter capability

**P&L Calculation:**
```
Avg Buy Price = Total Invested / Total Quantity
Current Value = Quantity × Current Market Price
P&L = Current Value - Total Invested
P&L % = (P&L / Total Invested) × 100
```

### 3. Trade Book Tab

**Complete transaction history:**

| Date | Ticker | Type | Qty | Price | Amount | Currency |
|------|--------|------|-----|-------|--------|----------|
| 2025-01-15 | AAPL | BUY | 10 | $150.00 | $1,500 | USD |
| 2025-01-16 | RELIANCE.NS | BUY | 5 | ₹2,450 | ₹12,250 | INR |

**Features:**
- ✅ Paginated (20 records per page)
- ✅ Date-sorted (newest first)
- ✅ All transaction details
- ✅ Exchange rates included

## How It Works

### Data Flow

```
Trade CSV Files → tradebook_builder.py → tradebook.csv
                                            ↓
                                    performanceDashboard.py
                                            ↓
                                    portfolio_calculator.py
                                            ↓
                                    Live Market Prices (Yahoo Finance)
                                            ↓
                                    Calculate Metrics
                                            ↓
                                    Display in Streamlit
```

### Key Components

1. **`performanceDashboard.py`** (Main UI)
   - Streamlit interface
   - Tab management
   - Data display

2. **`portfolio_calculator.py`** (Calculation Engine)
   - Loads tradebook
   - Fetches market prices
   - Calculates all metrics
   - Handles exchange rates

3. **`tradebook.csv`** (Data Source)
   - Consolidated trades
   - Built using `tradebook_builder.py`
   - Read-only for dashboard

### Caching Strategy

**Level 1 - Streamlit Cache:**
```python
@st.cache_data(ttl=300)  # 5 minutes
def load_portfolio_data():
    # Expensive operations cached here
```

**Level 2 - Session State:**
```python
if 'data_loaded' not in st.session_state:
    # Load data only once per session
    st.session_state.data_loaded = True
```

**Benefits:**
- ✅ Fast tab switching (no reloading)
- ✅ Reduced API calls to Yahoo Finance
- ✅ Better user experience
- ✅ Lower chance of rate limiting

## Market Data & Rate Limiting

### Data Source

- **Primary**: Yahoo Finance via `yfinance` library
- **Tickers**: Auto-detected from tradebook
- **Update Frequency**: Every 5 minutes (via cache)

### Rate Limiting Protection

To prevent "429 Too Many Requests" errors:

1. **Base Delay**: 1 second between each ticker
2. **Exponential Backoff**: 2s → 4s → 8s for retries
3. **Special 429 Handling**: 5s → 10s → 15s when rate limited
4. **Maximum Retries**: 3 attempts per ticker

**Performance impact:**
- For 32 tickers: ~32-40 seconds (first load)
- Subsequent loads: instant (cached)
- Success rate: >95%

### Console Output

During market data fetch, you'll see:
```
[1/32] Fetching AAPL... ✅
[2/32] Fetching RELIANCE.NS... ✅
[3/32] Fetching QQQM... ⏳ (retry 1, waiting 2s)
[4/32] Fetching QQQM... ✅
...
✅ Market data fetch complete: 31/32 successful
```

## Deploying to Streamlit Cloud

### Prerequisites

1. **Updated tradebook**: Run `python3 tradebook_builder.py consolidate`
2. **GitHub repository**: Code must be in a GitHub repo
3. **Streamlit Cloud account**: Sign up at [streamlit.io/cloud](https://streamlit.io/cloud)

### Step-by-Step Deployment

#### 1. Prepare Your Repository

```bash
# Ensure tradebook is updated
python3 tradebook_builder.py consolidate

# Test locally
streamlit run performanceDashboard.py

# Commit everything
git add tradebook.csv tradebook_processed_files.json
git add performanceDashboard.py portfolio_calculator.py requirements.txt
git commit -m "Prepare for deployment"
git push origin main
```

#### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your repository
4. Set main file: `performanceDashboard.py`
5. Click "Deploy"

#### 3. Monitor Deployment

Watch the logs for:
```
✅ Dependencies installed
✅ Tradebook loaded
✅ Market data fetched
✅ App running
```

### Updating Deployed App

```bash
# Add new trades to your CSV files
nano trades2025EquityKite.csv

# Update tradebook
python3 tradebook_builder.py consolidate

# Test locally
streamlit run performanceDashboard.py

# Commit and push
git add tradebook.csv tradebook_processed_files.json
git commit -m "Add trades for January 2025"
git push

# Streamlit Cloud auto-deploys on push
```

### Deployment Best Practices

✅ **Do:**
- Test locally before deploying
- Commit both `tradebook.csv` and `tradebook_processed_files.json`
- Monitor logs after deployment
- Update during low-usage hours
- Keep dependencies minimal

❌ **Don't:**
- Deploy with errors/warnings
- Include `.env` files (use Streamlit secrets instead)
- Skip local testing
- Deploy incomplete tradebook
- Forget to update processing history

## Troubleshooting

### Dashboard Won't Load

**Check:**
1. Is `tradebook.csv` present?
2. Run: `python3 tradebook_builder.py status`
3. Verify file format: `head tradebook.csv`

**Solution:**
```bash
python3 tradebook_builder.py consolidate
streamlit run performanceDashboard.py
```

### Holdings Not Displaying

**Causes:**
- No current holdings (all stocks sold)
- Market data fetch failed
- Rate limiting (429 errors)

**Solution:**
1. Check console for "429 Too Many Requests"
2. Wait 5 minutes and refresh
3. Verify internet connection
4. Check tickers are valid

### Incorrect P&L Calculations

**Common causes:**
1. **Missing trades**: Update tradebook
2. **Wrong exchange rates**: Rebuild tradebook
3. **Stale market data**: Clear cache (press 'C' in dashboard)

**Verification:**
```bash
# Check total trades
python3 tradebook_builder.py status

# Rebuild if needed
python3 tradebook_builder.py rebuild

# Test calculations
streamlit run performanceDashboard.py
```

### Daily Change Shows $0

**Cause:** Dashboard loaded outside market hours or first load

**Explanation:**
- Daily change requires previous close price
- First load has no reference point
- Updates after first market data fetch

### XIRR Shows "N/A"

**Causes:**
- Only one transaction date
- All transactions on same day
- No realized transactions

**Solution:**
- XIRR requires multiple cash flows over time
- Add more transactions across different dates

### 429 Rate Limit Errors

**Symptoms:**
```
❌ Failed after 3 attempts: 429 Client Error: Too Many Requests
```

**Solutions:**

**Temporary:**
- Wait 5-10 minutes
- Refresh dashboard (cache will help)

**Permanent:**
1. Increase cache TTL in `performanceDashboard.py`:
   ```python
   @st.cache_data(ttl=900)  # 15 minutes instead of 5
   ```

2. For large portfolios (50+ tickers):
   ```python
   @st.cache_data(ttl=1800)  # 30 minutes
   ```

### Streamlit Cloud Deployment Fails

**Check logs for:**

**"Module not found" errors:**
```bash
# Update requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

**"File not found: tradebook.csv":**
```bash
# Ensure tradebook is committed
git add tradebook.csv
git commit -m "Add tradebook"
git push
```

**Memory errors:**
- Streamlit Cloud has memory limits
- Reduce cache size or TTL
- Optimize data loading

## Performance Optimization

### For Small Portfolios (< 20 holdings)

Default settings work well:
```python
@st.cache_data(ttl=300)  # 5 minutes
```

### For Medium Portfolios (20-50 holdings)

Increase cache duration:
```python
@st.cache_data(ttl=600)  # 10 minutes
```

### For Large Portfolios (50+ holdings)

Aggressive caching:
```python
@st.cache_data(ttl=1800)  # 30 minutes
```

Consider batching:
```python
# In portfolio_calculator.py
# Process tickers in batches to reduce memory
```

## Advanced Features

### Custom Time Zones

Edit `performanceDashboard.py`:
```python
import pytz
IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST)
```

### Export Data

Add download buttons:
```python
st.download_button(
    "Download Holdings",
    portfolio_df.to_csv(index=False),
    "holdings.csv",
    "text/csv"
)
```

### Custom Metrics

Add to `portfolio_calculator.py`:
```python
def calculate_sharpe_ratio(returns, risk_free_rate=0.05):
    # Your implementation
    pass
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `C` | Clear cache |
| `R` | Rerun app |
| `/` | Focus search |

## Understanding XIRR

**What is XIRR?**
- Extended Internal Rate of Return
- Annualized return rate
- Accounts for timing of cash flows
- Industry-standard metric

**Formula:**
```
NPV = Σ (Cash Flow / (1 + XIRR)^(days/365))
```

**Example:**
```
Jan 1: Invested ₹1,00,000 (outflow: -1,00,000)
Jun 1: Current value ₹1,10,000 (inflow: +1,10,000)
XIRR = 21.0% (annualized)
```

**Interpretation:**
- > 15%: Excellent
- 10-15%: Good
- 5-10%: Moderate
- < 5%: Below average
- Negative: Loss

## Data Privacy

### Local Installation

- ✅ All data stays on your machine
- ✅ No data sent to external services (except Yahoo Finance for prices)
- ✅ Trade data never leaves your system

### Streamlit Cloud

- ⚠️ Trade data in your GitHub repo (public or private)
- ✅ Use private repository for confidential data
- ⚠️ Market data fetched from Yahoo Finance
- ✅ No analytics or tracking in the app

**Best practices:**
- Use private GitHub repository
- Don't include personal identifiable information in trades
- Regularly review access to your repo

## Quick Reference

### Common Commands

```bash
# Update tradebook
python3 tradebook_builder.py consolidate

# Check status
python3 tradebook_builder.py status

# Run dashboard
streamlit run performanceDashboard.py

# Clear cache
# Press 'C' in the dashboard, or:
# Menu → Settings → Clear cache
```

### File Locations

| File | Purpose |
|------|---------|
| `performanceDashboard.py` | Main dashboard UI |
| `portfolio_calculator.py` | Calculation engine |
| `tradebook.csv` | Consolidated trades |
| `tradebook_builder.py` | Tradebook builder CLI |
| `requirements.txt` | Python dependencies |

### Port Configuration

Default: `http://localhost:8501`

Custom port:
```bash
streamlit run performanceDashboard.py --server.port 8502
```

### Memory Usage

Typical usage:
- Small portfolio (10 stocks): ~50 MB
- Medium portfolio (30 stocks): ~100 MB
- Large portfolio (100 stocks): ~200 MB

## Support & Updates

### Getting Help

1. Check this guide first
2. Review error messages in console
3. Test with `python3 tradebook_builder.py status`
4. Verify data with sample calculations

### Keeping Updated

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart dashboard
streamlit run performanceDashboard.py
```

## Limitations

### Current Limitations

- **Market data**: Depends on Yahoo Finance availability
- **Rate limiting**: 429 errors possible with large portfolios
- **Exchange rates**: Historical rates may have gaps
- **Ticker changes**: Manual update needed if ticker changes
- **Delisted stocks**: May not have current prices

### Future Enhancements

Potential improvements:
- Multiple data source fallbacks
- Custom price overrides
- Portfolio comparison
- Historical performance charts
- Tax reports
- Dividend tracking

---

**Related Documentation:**
- `TRADEBOOK_GUIDE.md` - Building and managing your tradebook
- `TELEGRAM_GUIDE.md` - Setting up automated notifications
- `README.md` - Project overview

**Support:** For issues or questions, check the console logs first, then review this guide's troubleshooting section.
