"""
Korean Stock Data Collector
Collects stock data from Korean markets (KOSPI, KOSDAQ)
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from tqdm import tqdm

try:
    import FinanceDataReader as fdr
    from pykrx import stock
except ImportError:
    print("Warning: FinanceDataReader or pykrx not installed")
    print("Install with: pip install finance-datareader pykrx")

from ..utils.logger import get_logger
from ..utils.database import get_db
from ..utils.helpers import get_date_range

logger = get_logger(__name__)


class KoreanStockCollector:
    """
    Collector for Korean stock market data
    """

    def __init__(self, use_pykrx: bool = True):
        """
        Initialize Korean stock collector

        Args:
            use_pykrx: Use pykrx library (more reliable) instead of FinanceDataReader
        """
        self.use_pykrx = use_pykrx
        self.db = get_db()
        logger.info("Korean Stock Collector initialized")

    def get_stock_list(self, market: str = "ALL") -> pd.DataFrame:
        """
        Get list of Korean stocks

        Args:
            market: Market type - "KOSPI", "KOSDAQ", or "ALL"

        Returns:
            DataFrame with stock information
        """
        logger.info(f"Fetching stock list for market: {market}")

        if self.use_pykrx:
            today = datetime.now().strftime("%Y%m%d")
            stock_list = []

            if market in ["KOSPI", "ALL"]:
                kospi = stock.get_market_ticker_list(today, market="KOSPI")
                for ticker in kospi:
                    try:
                        name = stock.get_market_ticker_name(ticker)
                        stock_list.append({
                            'symbol': ticker,
                            'name': name,
                            'market': 'KOSPI'
                        })
                    except:
                        continue

            if market in ["KOSDAQ", "ALL"]:
                kosdaq = stock.get_market_ticker_list(today, market="KOSDAQ")
                for ticker in kosdaq:
                    try:
                        name = stock.get_market_ticker_name(ticker)
                        stock_list.append({
                            'symbol': ticker,
                            'name': name,
                            'market': 'KOSDAQ'
                        })
                    except:
                        continue

            df = pd.DataFrame(stock_list)
        else:
            # Use FinanceDataReader
            if market == "KOSPI":
                df = fdr.StockListing('KOSPI')
            elif market == "KOSDAQ":
                df = fdr.StockListing('KOSDAQ')
            else:  # ALL
                kospi = fdr.StockListing('KOSPI')
                kosdaq = fdr.StockListing('KOSDAQ')
                df = pd.concat([kospi, kosdaq], ignore_index=True)

            # Rename columns to match our schema
            if 'Code' in df.columns:
                df = df.rename(columns={'Code': 'symbol', 'Name': 'name', 'Market': 'market'})

        logger.info(f"Found {len(df)} stocks")
        return df

    def get_price_data(self,
                      symbol: str,
                      start_date: Union[str, datetime] = None,
                      end_date: Union[str, datetime] = None) -> pd.DataFrame:
        """
        Get OHLCV price data for a single stock

        Args:
            symbol: Stock symbol (e.g., '005930' for Samsung)
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with OHLCV data
        """
        start_date, end_date = get_date_range(start_date, end_date)

        try:
            if self.use_pykrx:
                df = stock.get_market_ohlcv_by_date(
                    start_date.strftime("%Y%m%d"),
                    end_date.strftime("%Y%m%d"),
                    symbol
                )

                # pykrx returns columns in Korean, rename them
                df = df.rename(columns={
                    '시가': 'open',
                    '고가': 'high',
                    '저가': 'low',
                    '종가': 'close',
                    '거래량': 'volume'
                })

                # Reset index to make date a column
                df = df.reset_index()
                df = df.rename(columns={'날짜': 'date'})

                # Keep only the columns we need (remove 등락률, 거래대금, etc.)
                columns_to_keep = ['date', 'open', 'high', 'low', 'close', 'volume']
                df = df[[col for col in columns_to_keep if col in df.columns]]

            else:
                # Use FinanceDataReader
                df = fdr.DataReader(symbol, start_date, end_date)
                df = df.reset_index()

                # Rename columns to lowercase
                df.columns = df.columns.str.lower()

            # Add symbol and market columns
            df['symbol'] = symbol
            df['market'] = self._get_market_for_symbol(symbol)

            # Ensure date is datetime
            df['date'] = pd.to_datetime(df['date'])

            # Sort by date
            df = df.sort_values('date').reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_fundamental_data(self,
                            symbol: str,
                            start_date: Union[str, datetime] = None,
                            end_date: Union[str, datetime] = None) -> pd.DataFrame:
        """
        Get fundamental data (PER, PBR, etc.) for a stock

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with fundamental data
        """
        start_date, end_date = get_date_range(start_date, end_date)

        try:
            if self.use_pykrx:
                df = stock.get_market_fundamental_by_date(
                    start_date.strftime("%Y%m%d"),
                    end_date.strftime("%Y%m%d"),
                    symbol
                )

                # Rename columns
                df = df.rename(columns={
                    'BPS': 'bps',
                    'PER': 'per',
                    'PBR': 'pbr',
                    'EPS': 'eps',
                    'DIV': 'dividend_yield',
                    'DPS': 'dps'
                })

                df = df.reset_index()
                df = df.rename(columns={'날짜': 'date'})
                df['symbol'] = symbol

                return df
            else:
                logger.warning("Fundamental data not available with FinanceDataReader")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching fundamental data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_market_cap(self,
                      symbol: str,
                      start_date: Union[str, datetime] = None,
                      end_date: Union[str, datetime] = None) -> pd.DataFrame:
        """
        Get market capitalization data

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with market cap data
        """
        start_date, end_date = get_date_range(start_date, end_date)

        try:
            if self.use_pykrx:
                df = stock.get_market_cap_by_date(
                    start_date.strftime("%Y%m%d"),
                    end_date.strftime("%Y%m%d"),
                    symbol
                )

                df = df.rename(columns={
                    '시가총액': 'market_cap',
                    '거래량': 'volume',
                    '거래대금': 'trading_value',
                    '상장주식수': 'listed_shares'
                })

                df = df.reset_index()
                df = df.rename(columns={'날짜': 'date'})
                df['symbol'] = symbol

                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching market cap for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_sector_mapping(self, market: str = "KOSPI") -> Dict[str, str]:
        """
        Get sector mapping for all stocks in a market.
        Maps stock symbols to their sector names.

        Args:
            market: Market type - "KOSPI" or "KOSDAQ"

        Returns:
            Dictionary mapping symbol to sector name
        """
        if not self.use_pykrx:
            logger.warning("Sector mapping requires pykrx")
            return {}

        try:
            today = datetime.now().strftime("%Y%m%d")
            sector_mapping = {}

            # Get all sector indices for the market
            sectors = stock.get_index_ticker_list(today, market=market)

            # Skip the first few indices (broad market indices)
            # and focus on industry-specific ones
            for sector_code in sectors:
                try:
                    sector_name = stock.get_index_ticker_name(sector_code)
                    # Get stocks in this sector
                    components = stock.get_index_portfolio_deposit_file(sector_code, today)

                    for symbol in components:
                        # Only set if not already mapped (first match = most specific)
                        if symbol not in sector_mapping:
                            sector_mapping[symbol] = sector_name
                except Exception:
                    continue

            logger.info(f"Built sector mapping for {len(sector_mapping)} stocks in {market}")
            return sector_mapping

        except Exception as e:
            logger.error(f"Error building sector mapping: {str(e)}")
            return {}

    def get_stock_sector(self, symbol: str, market: str = "KOSPI") -> Optional[str]:
        """
        Get sector for a single stock.

        Args:
            symbol: Stock symbol
            market: Market type

        Returns:
            Sector name or None
        """
        if not self.use_pykrx:
            return None

        try:
            today = datetime.now().strftime("%Y%m%d")
            sectors = stock.get_index_ticker_list(today, market=market)

            for sector_code in sectors:
                try:
                    components = stock.get_index_portfolio_deposit_file(sector_code, today)
                    if symbol in components:
                        return stock.get_index_ticker_name(sector_code)
                except Exception:
                    continue

            return None

        except Exception as e:
            logger.error(f"Error getting sector for {symbol}: {str(e)}")
            return None

    def collect_multiple_stocks(self,
                               symbols: List[str],
                               start_date: Union[str, datetime] = None,
                               end_date: Union[str, datetime] = None,
                               save_to_db: bool = True) -> pd.DataFrame:
        """
        Collect price data for multiple stocks

        Args:
            symbols: List of stock symbols
            start_date: Start date
            end_date: End date
            save_to_db: Save to database

        Returns:
            Combined DataFrame
        """
        logger.info(f"Collecting data for {len(symbols)} stocks")

        all_data = []

        for symbol in tqdm(symbols, desc="Collecting stock data"):
            df = self.get_price_data(symbol, start_date, end_date)

            if not df.empty:
                all_data.append(df)

        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)

            if save_to_db:
                self.db.save_stock_prices(combined_df, if_exists='append')

            logger.info(f"Collected {len(combined_df)} total records")
            return combined_df
        else:
            logger.warning("No data collected")
            return pd.DataFrame()

    def update_stock_list(self, market: str = "ALL") -> None:
        """
        Update stock list in database

        Args:
            market: Market type
        """
        stock_list = self.get_stock_list(market)

        if not stock_list.empty:
            stock_list['last_updated'] = datetime.now()
            self.db.save_stock_info(stock_list, if_exists='replace')
            logger.info(f"Updated stock list: {len(stock_list)} stocks")

    def _get_market_for_symbol(self, symbol: str) -> str:
        """
        Determine market (KOSPI/KOSDAQ) for a symbol

        Args:
            symbol: Stock symbol

        Returns:
            Market name
        """
        try:
            if self.use_pykrx:
                today = datetime.now().strftime("%Y%m%d")
                kospi_list = stock.get_market_ticker_list(today, market="KOSPI")
                if symbol in kospi_list:
                    return "KOSPI"
                else:
                    return "KOSDAQ"
            else:
                return "Unknown"
        except:
            return "Unknown"


def main():
    """Example usage"""
    collector = KoreanStockCollector(use_pykrx=True)

    # Update stock list
    collector.update_stock_list(market="ALL")

    # Get major stocks (e.g., Samsung, SK Hynix, Naver)
    major_stocks = ['005930', '000660', '035420']

    # Collect last 1 year of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    df = collector.collect_multiple_stocks(
        major_stocks,
        start_date=start_date,
        end_date=end_date,
        save_to_db=True
    )

    print(f"Collected {len(df)} records")
    print(df.head())


if __name__ == "__main__":
    main()
