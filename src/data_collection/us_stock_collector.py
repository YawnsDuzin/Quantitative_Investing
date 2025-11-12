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

try:
    import yfinance as yf
except ImportError:
    print("Warning: yfinance not installed")
    print("Install with: pip install yfinance")

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

    def get_stock_info(self, symbol: str) -> Dict:
        """
        Get stock information

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Dictionary with stock info
        """
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
            logger.error(f"Error fetching info for {symbol}: {str(e)}")
            return {'symbol': symbol, 'name': symbol}

    def get_price_data(self,
                      symbol: str,
                      start_date: Union[str, datetime] = None,
                      end_date: Union[str, datetime] = None,
                      interval: str = '1d') -> pd.DataFrame:
        """
        Get OHLCV price data for a single stock

        Args:
            symbol: Stock ticker symbol
            start_date: Start date
            end_date: End date
            interval: Data interval ('1d', '1wk', '1mo')

        Returns:
            DataFrame with OHLCV data
        """
        start_date, end_date = get_date_range(start_date, end_date)

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=False
            )

            if df.empty:
                logger.warning(f"No data found for {symbol}")
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

            # Get market info
            try:
                info = yf.Ticker(symbol).info
                df['market'] = info.get('exchange', 'Unknown')
            except:
                df['market'] = 'Unknown'

            # Ensure date is datetime
            df['date'] = pd.to_datetime(df['date'])

            # Sort by date
            df = df.sort_values('date').reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {str(e)}")
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
        try:
            # Download S&P 500 list from Wikipedia
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            sp500_table = tables[0]
            tickers = sp500_table['Symbol'].tolist()

            # Clean tickers (replace . with -)
            tickers = [ticker.replace('.', '-') for ticker in tickers]

            logger.info(f"Found {len(tickers)} S&P 500 stocks")
            return tickers

        except Exception as e:
            logger.error(f"Error fetching S&P 500 list: {str(e)}")
            return []

    def get_nasdaq100_tickers(self) -> List[str]:
        """
        Get list of NASDAQ 100 ticker symbols

        Returns:
            List of ticker symbols
        """
        try:
            # Download NASDAQ 100 list from Wikipedia
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            tables = pd.read_html(url)
            nasdaq_table = tables[4]  # The table with tickers
            tickers = nasdaq_table['Ticker'].tolist()

            logger.info(f"Found {len(tickers)} NASDAQ 100 stocks")
            return tickers

        except Exception as e:
            logger.error(f"Error fetching NASDAQ 100 list: {str(e)}")
            return []

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
