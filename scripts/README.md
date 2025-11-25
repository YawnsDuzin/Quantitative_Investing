# Stock Data Collection Scripts

This directory contains scripts for collecting stock market data from Korean and US markets.

## collect_all_stocks.py

A comprehensive script for collecting **ALL** stock data from Korean (KOSPI, KOSDAQ) and US (NYSE, NASDAQ) markets.

### Features

- **Batch Processing**: Processes stocks in configurable batches to avoid API rate limiting
- **Resume Capability**: Saves progress to files, allowing you to restart from where you left off
- **Error Handling**: Tracks failed symbols and continues with remaining stocks
- **Progress Tracking**: Real-time progress display with tqdm
- **Flexible Configuration**: Customize years of data, batch sizes, and target markets

### Prerequisites

Install required packages:

```bash
pip install pykrx finance-datareader yfinance pandas sqlalchemy tqdm python-dotenv pyyaml lxml html5lib
```

### Usage

#### Basic Usage (Collect All Markets)

```bash
cd /path/to/Quantitative_Investing
python scripts/collect_all_stocks.py
```

#### Korean Stocks Only

```bash
python scripts/collect_all_stocks.py --market korean
```

#### US Stocks Only

```bash
python scripts/collect_all_stocks.py --market us
```

#### Custom Options

```bash
# Collect 5 years of data
python scripts/collect_all_stocks.py --years 5

# Start fresh (ignore previous progress)
python scripts/collect_all_stocks.py --no-resume

# Custom batch sizes
python scripts/collect_all_stocks.py --batch-kr 100 --batch-us 200

# Check collection status
python scripts/collect_all_stocks.py --status
```

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--market` | `all` | Market to collect: `korean`, `us`, or `all` |
| `--years` | `3` | Years of historical data to collect |
| `--batch-kr` | `50` | Batch size for Korean stocks |
| `--batch-us` | `100` | Batch size for US stocks (uses bulk download) |
| `--no-resume` | `False` | Start fresh, ignore previous progress |
| `--status` | `False` | Show collection status and exit |

### Data Sources

#### Korean Stocks
- **Primary**: `pykrx` - Korea Exchange official data
- **Fallback**: `FinanceDataReader` - Alternative Korean market data

#### US Stocks
- **Primary**: `yfinance` - Yahoo Finance API
- Stock lists from Wikipedia (S&P 500, NASDAQ 100, Russell indices)

### Output

Data is saved to SQLite database at: `data/database/quant_investing.db`

Tables:
- `stock_prices`: OHLCV price data
- `stock_info`: Company information (name, market, sector)
- `stock_fundamentals`: Financial metrics (PER, PBR, etc.)

### Progress Files

Progress is saved to: `data/collection_progress/`
- `progress_korean.json`: Korean market collection status
- `progress_us.json`: US market collection status

These files allow the script to resume from where it stopped.

### Estimated Time

| Market | Stocks | Estimated Time |
|--------|--------|----------------|
| Korean (KOSPI + KOSDAQ) | ~2,300 | 30-60 minutes |
| US (All indices) | ~3,000+ | 30-60 minutes |
| **Total** | ~5,300+ | **1-2 hours** |

*Times may vary based on network speed and API response times*

### Troubleshooting

#### API Rate Limiting
If you encounter rate limiting errors:
1. Increase delay between requests (modify script)
2. Reduce batch size
3. Wait and resume later (progress is saved)

#### Missing Data
Some stocks may fail due to:
- Delisted stocks
- API temporary errors
- Invalid ticker symbols

Failed symbols are logged and can be retried later.

#### Network Errors
The script has retry logic for network failures. If issues persist:
1. Check internet connection
2. Try running `--status` to see current progress
3. Resume with default options

### Example Output

```
============================================================
FULL STOCK DATA COLLECTION
============================================================
Markets: all
Years: 3
Resume: True
============================================================

Starting Korean Stock Collection...
Found 2,345 Korean stocks
Processing 2,345 remaining stocks in 47 batches

Batch 1/47: 100%|██████████| 50/50 [00:45<00:00]
Batch 1: Saved 12,500 records
...

FINAL RESULTS
============================================================
KOREAN:
  Total Symbols: 2,345
  Completed: 2,300
  Failed: 45
  Total Records: 575,000

US:
  Total Symbols: 3,200
  Completed: 3,150
  Failed: 50
  Total Records: 787,500
```

### Integration with Main Project

After collection, you can use the data with the quantitative investing framework:

```python
from src.utils.database import get_db

db = get_db()

# Get all Korean stock prices
kr_prices = db.get_stock_prices(market='KOSPI')

# Get specific stock
samsung = db.get_stock_prices(symbol='005930')

# Get US stocks
us_prices = db.get_stock_prices(market='US')
```
