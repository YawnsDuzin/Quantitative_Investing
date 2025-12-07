"""
US Stock Data Collector
Collects stock data from US markets (NYSE, NASDAQ)
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from tqdm import tqdm
import time
import os
import ssl
import certifi

# Set SSL certificate path for yfinance/curl_cffi
cert_path = certifi.where()
os.environ['SSL_CERT_FILE'] = cert_path
os.environ['REQUESTS_CA_BUNDLE'] = cert_path
os.environ['CURL_CA_BUNDLE'] = cert_path

# Disable curl_cffi to use requests backend
os.environ['YF_USE_CURL'] = 'false'

try:
    import yfinance as yf
    # Configure yfinance
    yf.set_tz_cache_location(os.path.join(os.path.dirname(__file__), '.yf_cache'))
except ImportError:
    print("Warning: yfinance not installed")
    print("Install with: pip install yfinance")

# Also try FinanceDataReader as backup
try:
    import FinanceDataReader as fdr
    FDR_AVAILABLE = True
    print(f"[US Stock Collector] FinanceDataReader loaded successfully (version: {getattr(fdr, '__version__', 'unknown')})")
except ImportError as e:
    FDR_AVAILABLE = False
    print(f"[US Stock Collector] FinanceDataReader not available: {e}")

from ..utils.logger import get_logger
from ..utils.database import get_db
from ..utils.helpers import get_date_range

logger = get_logger(__name__)


class USStockCollector:
    """
    Collector for US stock market data
    """

    def __init__(self):
        """Initialize US stock collector"""
        self.db = get_db()
        logger.info("US Stock Collector initialized")

    def get_stock_info(self, symbol: str, max_retries: int = 2) -> Dict:
        """
        Get stock information

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            max_retries: Maximum retry attempts for rate limiting

        Returns:
            Dictionary with stock info
        """
        for attempt in range(max_retries):
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                return {
                    'symbol': symbol,
                    'name': info.get('longName', symbol),
                    'market': info.get('exchange', 'Unknown'),
                    'sector': info.get('sector', None),
                    'industry': info.get('industry', None),
                    'market_cap': info.get('marketCap', None),
                    'currency': info.get('currency', 'USD')
                }

            except Exception as e:
                error_msg = str(e)
                # Check for rate limiting (429 error)
                if '429' in error_msg or 'Too Many Requests' in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # Exponential backoff: 5s, 10s
                        logger.warning(f"[{symbol}] Rate limited, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                logger.error(f"Error fetching info for {symbol}: {error_msg}")
                return {'symbol': symbol, 'name': symbol}

        return {'symbol': symbol, 'name': symbol}

    def get_price_data(self,
                      symbol: str,
                      start_date: Union[str, datetime] = None,
                      end_date: Union[str, datetime] = None,
                      interval: str = '1d',
                      max_retries: int = 3) -> pd.DataFrame:
        """
        Get OHLCV price data for a single stock

        Args:
            symbol: Stock ticker symbol
            start_date: Start date
            end_date: End date
            interval: Data interval ('1d', '1wk', '1mo')
            max_retries: Maximum number of retry attempts

        Returns:
            DataFrame with OHLCV data
        """
        start_date, end_date = get_date_range(start_date, end_date)

        df = pd.DataFrame()

        # Try FinanceDataReader first (more reliable for some regions)
        if FDR_AVAILABLE:
            for attempt in range(max_retries):
                try:
                    logger.debug(f"[{symbol}] Trying FDR (attempt {attempt + 1}/{max_retries})...")
                    df = fdr.DataReader(symbol, start_date, end_date)
                    if df is not None and not df.empty:
                        df = df.reset_index()
                        df.columns = df.columns.str.lower()

                        # FDR returns date as index, after reset_index it becomes 'index' column
                        if 'index' in df.columns:
                            df = df.rename(columns={'index': 'date'})

                        # Rename 'change' to avoid conflicts
                        if 'change' in df.columns:
                            df = df.drop(columns=['change'])

                        # Keep only needed columns
                        columns_to_keep = ['date', 'open', 'high', 'low', 'close', 'volume', 'adj close']
                        df = df[[col for col in columns_to_keep if col in df.columns]]

                        # Rename adj close
                        if 'adj close' in df.columns:
                            df = df.rename(columns={'adj close': 'adj_close'})

                        df['symbol'] = symbol
                        df['market'] = 'US'
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.sort_values('date').reset_index(drop=True)

                        logger.info(f"[{symbol}] SUCCESS via FDR: {len(df)} records")
                        return df
                    else:
                        logger.warning(f"[{symbol}] FDR returned empty data")
                except Exception as e:
                    logger.warning(f"[{symbol}] FDR attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Wait before retry

        # Fallback to yfinance with retry
        logger.debug(f"[{symbol}] Trying yfinance (FDR failed or unavailable)...")
        for attempt in range(max_retries):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    auto_adjust=False
                )

                if df.empty:
                    logger.warning(f"[{symbol}] yfinance returned empty (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
                        continue
                    return pd.DataFrame()

                # Reset index to make date a column
                df = df.reset_index()

                # Rename columns to lowercase
                column_mapping = {
                    'Date': 'date',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume',
                    'Adj Close': 'adj_close'
                }
                df = df.rename(columns=column_mapping)

                # Select only needed columns
                columns_to_keep = ['date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
                df = df[[col for col in columns_to_keep if col in df.columns]]

                # Add symbol and market columns
                df['symbol'] = symbol
                df['market'] = 'US'  # Default to US, don't make another API call

                # Ensure date is datetime
                df['date'] = pd.to_datetime(df['date'])

                # Sort by date
                df = df.sort_values('date').reset_index(drop=True)

                logger.info(f"[{symbol}] SUCCESS via yfinance: {len(df)} records")
                return df

            except Exception as e:
                logger.error(f"[{symbol}] yfinance attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry

        logger.error(f"[{symbol}] All data sources failed after {max_retries} attempts")
        return pd.DataFrame()

    def get_fundamental_data(self, symbol: str) -> Dict:
        """
        Get fundamental data for a stock

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with fundamental metrics
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            fundamentals = {
                'symbol': symbol,
                'date': datetime.now().date(),
                'market_cap': info.get('marketCap'),
                'per': info.get('trailingPE'),
                'pbr': info.get('priceToBook'),
                'eps': info.get('trailingEps'),
                'roe': info.get('returnOnEquity'),
                'debt_ratio': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'revenue': info.get('totalRevenue'),
                'operating_income': info.get('operatingIncome'),
                'net_income': info.get('netIncomeToCommon'),
                'dividend_yield': info.get('dividendYield'),
                'beta': info.get('beta')
            }

            return fundamentals

        except Exception as e:
            logger.error(f"Error fetching fundamental data for {symbol}: {str(e)}")
            return {'symbol': symbol}

    def get_sp500_tickers(self) -> List[str]:
        """
        Get list of S&P 500 ticker symbols

        Returns:
            List of ticker symbols
        """
        tickers = []

        # Method 1: Try Wikipedia
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            sp500_table = tables[0]
            tickers = sp500_table['Symbol'].tolist()
            tickers = [ticker.replace('.', '-') for ticker in tickers]
            logger.info(f"Found {len(tickers)} S&P 500 stocks from Wikipedia")
            return tickers
        except Exception as e:
            logger.warning(f"Wikipedia failed: {str(e)}")

        # Method 2: Try datahub.io
        try:
            url = 'https://datahub.io/core/s-and-p-500-companies/r/constituents.csv'
            df = pd.read_csv(url)
            if 'Symbol' in df.columns:
                tickers = df['Symbol'].tolist()
                tickers = [ticker.replace('.', '-') for ticker in tickers]
                logger.info(f"Found {len(tickers)} S&P 500 stocks from datahub.io")
                return tickers
        except Exception as e:
            logger.warning(f"datahub.io failed: {str(e)}")

        # Method 3: Try slickcharts.com
        try:
            import requests
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            url = 'https://www.slickcharts.com/sp500'
            response = requests.get(url, headers=headers, timeout=10)
            tables = pd.read_html(response.text)
            for table in tables:
                if 'Symbol' in table.columns:
                    tickers = table['Symbol'].tolist()
                    tickers = [ticker.replace('.', '-') for ticker in tickers]
                    logger.info(f"Found {len(tickers)} S&P 500 stocks from slickcharts")
                    return tickers
        except Exception as e:
            logger.warning(f"slickcharts failed: {str(e)}")

        # Fallback: Expanded list of major stocks
        logger.error("All S&P 500 sources failed, using fallback list")
        return [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'BRK-B', 'JPM', 'V',
            'JNJ', 'UNH', 'HD', 'PG', 'MA', 'XOM', 'CVX', 'LLY', 'ABBV', 'MRK',
            'KO', 'PEP', 'COST', 'AVGO', 'TMO', 'WMT', 'MCD', 'CSCO', 'ACN', 'ABT',
            'DHR', 'NKE', 'ADBE', 'CRM', 'TXN', 'PM', 'VZ', 'NEE', 'CMCSA', 'INTC',
            'NFLX', 'AMD', 'QCOM', 'UPS', 'T', 'HON', 'LOW', 'MS', 'BA', 'GS'
        ]

    def get_nasdaq100_tickers(self) -> List[str]:
        """
        Get list of NASDAQ 100 ticker symbols

        Returns:
            List of ticker symbols
        """
        # Method 1: Try Wikipedia
        try:
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            tables = pd.read_html(url)
            for table in tables:
                if 'Ticker' in table.columns:
                    tickers = table['Ticker'].tolist()
                    logger.info(f"Found {len(tickers)} NASDAQ 100 stocks from Wikipedia")
                    return tickers
        except Exception as e:
            logger.warning(f"Wikipedia NASDAQ 100 failed: {str(e)}")

        # Method 2: Try slickcharts.com
        try:
            import requests
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            url = 'https://www.slickcharts.com/nasdaq100'
            response = requests.get(url, headers=headers, timeout=10)
            tables = pd.read_html(response.text)
            for table in tables:
                if 'Symbol' in table.columns:
                    tickers = table['Symbol'].tolist()
                    logger.info(f"Found {len(tickers)} NASDAQ 100 stocks from slickcharts")
                    return tickers
        except Exception as e:
            logger.warning(f"slickcharts NASDAQ 100 failed: {str(e)}")

        # Fallback: Expanded NASDAQ 100 list
        logger.error("All NASDAQ 100 sources failed, using fallback list")
        return [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA', 'AVGO', 'COST',
            'NFLX', 'ADBE', 'PEP', 'CSCO', 'AMD', 'CMCSA', 'INTC', 'TMUS', 'TXN', 'QCOM',
            'AMGN', 'INTU', 'AMAT', 'ISRG', 'HON', 'BKNG', 'SBUX', 'VRTX', 'GILD', 'MDLZ',
            'ADP', 'REGN', 'ADI', 'LRCX', 'PYPL', 'MU', 'SNPS', 'PANW', 'KLAC', 'CDNS',
            'MELI', 'MAR', 'ORLY', 'ASML', 'ABNB', 'CTAS', 'MNST', 'FTNT', 'CHTR', 'MRVL'
        ]

    def collect_multiple_stocks(self,
                               symbols: List[str],
                               start_date: Union[str, datetime] = None,
                               end_date: Union[str, datetime] = None,
                               save_to_db: bool = True,
                               delay: float = 0.1) -> pd.DataFrame:
        """
        Collect price data for multiple stocks

        Args:
            symbols: List of stock ticker symbols
            start_date: Start date
            end_date: End date
            save_to_db: Save to database
            delay: Delay between requests (seconds) to avoid rate limiting

        Returns:
            Combined DataFrame
        """
        logger.info(f"Collecting data for {len(symbols)} stocks")

        all_data = []

        for symbol in tqdm(symbols, desc="Collecting stock data"):
            df = self.get_price_data(symbol, start_date, end_date)

            if not df.empty:
                all_data.append(df)

            # Add delay to avoid rate limiting
            time.sleep(delay)

        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)

            if save_to_db:
                self.db.save_stock_prices(combined_df, if_exists='append')

            logger.info(f"Collected {len(combined_df)} total records")
            return combined_df
        else:
            logger.warning("No data collected")
            return pd.DataFrame()

    def update_stock_list(self, index: str = "SP500") -> None:
        """
        Update stock list in database

        Args:
            index: Stock index ("SP500" or "NASDAQ100")
        """
        if index == "SP500":
            tickers = self.get_sp500_tickers()
        elif index == "NASDAQ100":
            tickers = self.get_nasdaq100_tickers()
        else:
            logger.error(f"Unknown index: {index}")
            return

        stock_info_list = []

        for ticker in tqdm(tickers, desc=f"Collecting {index} info"):
            info = self.get_stock_info(ticker)
            info['last_updated'] = datetime.now()
            stock_info_list.append(info)
            time.sleep(0.1)  # Avoid rate limiting

        if stock_info_list:
            df = pd.DataFrame(stock_info_list)
            self.db.save_stock_info(df, if_exists='append')
            logger.info(f"Updated {index} stock list: {len(df)} stocks")

    def download_bulk_data(self,
                          symbols: List[str],
                          start_date: Union[str, datetime] = None,
                          end_date: Union[str, datetime] = None) -> pd.DataFrame:
        """
        Download data for multiple stocks using yfinance bulk download
        (faster than individual downloads)

        Args:
            symbols: List of ticker symbols
            start_date: Start date
            end_date: End date

        Returns:
            Combined DataFrame
        """
        start_date, end_date = get_date_range(start_date, end_date)

        try:
            # Use yfinance bulk download (faster)
            data = yf.download(
                symbols,
                start=start_date,
                end=end_date,
                group_by='ticker',
                auto_adjust=False,
                threads=True
            )

            if data.empty:
                logger.warning("No data downloaded")
                return pd.DataFrame()

            # Process the multi-index dataframe
            all_dfs = []

            for symbol in symbols:
                try:
                    if len(symbols) == 1:
                        df = data.copy()
                    else:
                        df = data[symbol].copy()

                    if df.empty:
                        continue

                    df = df.reset_index()
                    df = df.rename(columns={
                        'Date': 'date',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume',
                        'Adj Close': 'adj_close'
                    })

                    df['symbol'] = symbol
                    df['market'] = 'US'

                    all_dfs.append(df)

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {str(e)}")
                    continue

            if all_dfs:
                combined_df = pd.concat(all_dfs, ignore_index=True)
                logger.info(f"Downloaded {len(combined_df)} records for {len(all_dfs)} stocks")
                return combined_df
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error in bulk download: {str(e)}")
            return pd.DataFrame()


def main():
    """Example usage"""
    collector = USStockCollector()

    # Get major tech stocks
    tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

    # Collect last 1 year of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Use bulk download (faster)
    df = collector.download_bulk_data(
        tech_stocks,
        start_date=start_date,
        end_date=end_date
    )

    print(f"Collected {len(df)} records")
    print(df.head())

    # Save to database
    if not df.empty:
        db = get_db()
        db.save_stock_prices(df, if_exists='append')
        print("Data saved to database")


if __name__ == "__main__":
    main()
