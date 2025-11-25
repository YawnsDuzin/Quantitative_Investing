#!/usr/bin/env python3
"""
Comprehensive Stock Data Collector
Collects ALL Korean (KOSPI, KOSDAQ) and US (NYSE, NASDAQ) stock data

Features:
- Progress saving/resuming (can restart from where it stopped)
- Batch processing to avoid rate limiting
- Error handling with retry logic
- Detailed logging and progress tracking
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from tqdm import tqdm

# Import project modules
from src.data_collection.kr_stock_collector import KoreanStockCollector
from src.data_collection.us_stock_collector import USStockCollector
from src.utils.database import get_db
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CollectionProgress:
    """Track collection progress for resume capability"""
    market: str
    total_symbols: int
    completed_symbols: List[str]
    failed_symbols: List[str]
    current_batch: int
    total_batches: int
    start_time: str
    last_update: str
    status: str  # 'in_progress', 'completed', 'failed'

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'CollectionProgress':
        return cls(**data)


class FullStockCollector:
    """
    Comprehensive collector for all Korean and US stocks
    """

    def __init__(self,
                 data_dir: str = None,
                 batch_size_kr: int = 50,
                 batch_size_us: int = 100,
                 years: int = 3,
                 delay_kr: float = 0.5,
                 delay_us: float = 0.1):
        """
        Initialize the full stock collector

        Args:
            data_dir: Directory to store progress files
            batch_size_kr: Number of Korean stocks per batch
            batch_size_us: Number of US stocks per batch (for bulk download)
            years: Number of years of historical data to collect
            delay_kr: Delay between Korean stock requests (seconds)
            delay_us: Delay between US stock requests (seconds)
        """
        self.data_dir = Path(data_dir or project_root / 'data' / 'collection_progress')
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.batch_size_kr = batch_size_kr
        self.batch_size_us = batch_size_us
        self.years = years
        self.delay_kr = delay_kr
        self.delay_us = delay_us

        # Initialize collectors
        self.kr_collector = KoreanStockCollector(use_pykrx=True)
        self.us_collector = USStockCollector()
        self.db = get_db()

        # Date range
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=365 * years)

        logger.info(f"Full Stock Collector initialized")
        logger.info(f"Date range: {self.start_date.date()} to {self.end_date.date()}")
        logger.info(f"Batch sizes - KR: {batch_size_kr}, US: {batch_size_us}")

    def _get_progress_file(self, market: str) -> Path:
        """Get progress file path for a market"""
        return self.data_dir / f"progress_{market.lower()}.json"

    def _save_progress(self, progress: CollectionProgress) -> None:
        """Save collection progress to file"""
        progress.last_update = datetime.now().isoformat()
        file_path = self._get_progress_file(progress.market)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(progress.to_dict(), f, ensure_ascii=False, indent=2)

    def _load_progress(self, market: str) -> Optional[CollectionProgress]:
        """Load collection progress from file"""
        file_path = self._get_progress_file(market)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return CollectionProgress.from_dict(data)
        return None

    def _get_all_korean_symbols(self) -> List[Dict]:
        """Get all Korean stock symbols with market info"""
        logger.info("Fetching Korean stock list...")

        stock_list = self.kr_collector.get_stock_list(market="ALL")

        if stock_list.empty:
            logger.error("Failed to fetch Korean stock list")
            return []

        symbols = stock_list.to_dict('records')
        logger.info(f"Found {len(symbols)} Korean stocks")

        return symbols

    def _get_all_us_symbols(self) -> List[str]:
        """Get all US stock symbols"""
        logger.info("Fetching US stock list...")

        all_symbols = set()

        # Get S&P 500
        try:
            sp500 = self.us_collector.get_sp500_tickers()
            all_symbols.update(sp500)
            logger.info(f"S&P 500: {len(sp500)} stocks")
        except Exception as e:
            logger.error(f"Error fetching S&P 500: {e}")

        # Get NASDAQ 100
        try:
            nasdaq100 = self.us_collector.get_nasdaq100_tickers()
            all_symbols.update(nasdaq100)
            logger.info(f"NASDAQ 100: {len(nasdaq100)} stocks")
        except Exception as e:
            logger.error(f"Error fetching NASDAQ 100: {e}")

        # Try to get full NYSE/NASDAQ lists via yfinance screener
        try:
            import yfinance as yf

            # Get additional symbols from popular exchanges
            # Note: yfinance doesn't provide full exchange lists directly
            # We'll use a combination of indices and popular ETF holdings

            # Russell 1000 components (via Wikipedia)
            try:
                url = 'https://en.wikipedia.org/wiki/Russell_1000_Index'
                tables = pd.read_html(url)
                for table in tables:
                    if 'Ticker' in table.columns:
                        tickers = table['Ticker'].dropna().tolist()
                        all_symbols.update(tickers)
                        logger.info(f"Russell 1000: Added {len(tickers)} stocks")
                        break
                    elif 'Symbol' in table.columns:
                        tickers = table['Symbol'].dropna().tolist()
                        all_symbols.update(tickers)
                        logger.info(f"Russell 1000: Added {len(tickers)} stocks")
                        break
            except Exception as e:
                logger.warning(f"Could not fetch Russell 1000: {e}")

            # Russell 2000 components (small caps)
            try:
                url = 'https://en.wikipedia.org/wiki/Russell_2000_Index'
                tables = pd.read_html(url)
                for table in tables:
                    if 'Ticker' in table.columns:
                        tickers = table['Ticker'].dropna().tolist()
                        all_symbols.update(tickers)
                        logger.info(f"Russell 2000: Added {len(tickers)} stocks")
                        break
            except:
                pass

        except Exception as e:
            logger.warning(f"Error fetching additional US symbols: {e}")

        # Clean symbols
        cleaned_symbols = []
        for sym in all_symbols:
            if isinstance(sym, str) and sym.strip():
                # Replace . with - (yfinance format)
                cleaned = sym.strip().replace('.', '-').upper()
                if cleaned and len(cleaned) <= 5:  # Filter out invalid tickers
                    cleaned_symbols.append(cleaned)

        logger.info(f"Total US symbols: {len(cleaned_symbols)}")
        return sorted(list(set(cleaned_symbols)))

    def collect_korean_stocks(self, resume: bool = True) -> Dict:
        """
        Collect all Korean stock data

        Args:
            resume: Resume from previous progress if available

        Returns:
            Collection statistics
        """
        logger.info("="*60)
        logger.info("Starting Korean Stock Collection")
        logger.info("="*60)

        # Get all symbols
        all_stocks = self._get_all_korean_symbols()
        if not all_stocks:
            return {'status': 'failed', 'error': 'No stocks found'}

        all_symbols = [s['symbol'] for s in all_stocks]

        # Load or create progress
        progress = None
        if resume:
            progress = self._load_progress('korean')

        if progress and progress.status == 'in_progress':
            logger.info(f"Resuming from previous progress: {len(progress.completed_symbols)} completed")
            remaining_symbols = [s for s in all_symbols if s not in progress.completed_symbols]
        else:
            remaining_symbols = all_symbols
            progress = CollectionProgress(
                market='korean',
                total_symbols=len(all_symbols),
                completed_symbols=[],
                failed_symbols=[],
                current_batch=0,
                total_batches=(len(all_symbols) + self.batch_size_kr - 1) // self.batch_size_kr,
                start_time=datetime.now().isoformat(),
                last_update=datetime.now().isoformat(),
                status='in_progress'
            )

        # Save stock info to database
        stock_df = pd.DataFrame(all_stocks)
        stock_df['last_updated'] = datetime.now()
        self.db.save_stock_info(stock_df, if_exists='replace')
        logger.info("Saved Korean stock info to database")

        # Collect data in batches
        total_records = 0

        # Create batches
        batches = [remaining_symbols[i:i + self.batch_size_kr]
                   for i in range(0, len(remaining_symbols), self.batch_size_kr)]

        logger.info(f"Processing {len(remaining_symbols)} remaining stocks in {len(batches)} batches")

        for batch_idx, batch in enumerate(batches):
            logger.info(f"\n--- Batch {batch_idx + 1}/{len(batches)} ({len(batch)} stocks) ---")

            batch_data = []

            for symbol in tqdm(batch, desc=f"Batch {batch_idx + 1}"):
                try:
                    df = self.kr_collector.get_price_data(
                        symbol,
                        start_date=self.start_date,
                        end_date=self.end_date
                    )

                    if not df.empty:
                        batch_data.append(df)
                        progress.completed_symbols.append(symbol)
                        total_records += len(df)
                    else:
                        progress.failed_symbols.append(symbol)

                except Exception as e:
                    logger.error(f"Error collecting {symbol}: {e}")
                    progress.failed_symbols.append(symbol)

                # Small delay to avoid rate limiting
                time.sleep(self.delay_kr)

            # Save batch to database
            if batch_data:
                try:
                    combined_df = pd.concat(batch_data, ignore_index=True)
                    self.db.save_stock_prices(combined_df, if_exists='append')
                    logger.info(f"Batch {batch_idx + 1}: Saved {len(combined_df)} records")
                except Exception as e:
                    logger.error(f"Error saving batch to database: {e}")

            # Update progress
            progress.current_batch = batch_idx + 1
            self._save_progress(progress)

            # Longer delay between batches
            if batch_idx < len(batches) - 1:
                time.sleep(2)

        # Mark as completed
        progress.status = 'completed'
        self._save_progress(progress)

        stats = {
            'status': 'completed',
            'total_symbols': len(all_symbols),
            'completed': len(progress.completed_symbols),
            'failed': len(progress.failed_symbols),
            'total_records': total_records,
            'failed_symbols': progress.failed_symbols[:20]  # First 20 failed
        }

        logger.info("\n" + "="*60)
        logger.info("Korean Stock Collection Complete")
        logger.info(f"Total: {stats['total_symbols']}, Success: {stats['completed']}, Failed: {stats['failed']}")
        logger.info("="*60)

        return stats

    def collect_us_stocks(self, resume: bool = True) -> Dict:
        """
        Collect all US stock data

        Args:
            resume: Resume from previous progress if available

        Returns:
            Collection statistics
        """
        logger.info("="*60)
        logger.info("Starting US Stock Collection")
        logger.info("="*60)

        # Get all symbols
        all_symbols = self._get_all_us_symbols()
        if not all_symbols:
            return {'status': 'failed', 'error': 'No stocks found'}

        # Load or create progress
        progress = None
        if resume:
            progress = self._load_progress('us')

        if progress and progress.status == 'in_progress':
            logger.info(f"Resuming from previous progress: {len(progress.completed_symbols)} completed")
            remaining_symbols = [s for s in all_symbols if s not in progress.completed_symbols]
        else:
            remaining_symbols = all_symbols
            progress = CollectionProgress(
                market='us',
                total_symbols=len(all_symbols),
                completed_symbols=[],
                failed_symbols=[],
                current_batch=0,
                total_batches=(len(all_symbols) + self.batch_size_us - 1) // self.batch_size_us,
                start_time=datetime.now().isoformat(),
                last_update=datetime.now().isoformat(),
                status='in_progress'
            )

        # Collect data in batches using bulk download
        total_records = 0

        # Create batches
        batches = [remaining_symbols[i:i + self.batch_size_us]
                   for i in range(0, len(remaining_symbols), self.batch_size_us)]

        logger.info(f"Processing {len(remaining_symbols)} remaining stocks in {len(batches)} batches")

        for batch_idx, batch in enumerate(batches):
            logger.info(f"\n--- Batch {batch_idx + 1}/{len(batches)} ({len(batch)} stocks) ---")

            try:
                # Use bulk download for efficiency
                df = self.us_collector.download_bulk_data(
                    symbols=batch,
                    start_date=self.start_date,
                    end_date=self.end_date
                )

                if not df.empty:
                    # Save to database
                    self.db.save_stock_prices(df, if_exists='append')
                    total_records += len(df)

                    # Track which symbols were successful
                    successful_symbols = df['symbol'].unique().tolist()
                    progress.completed_symbols.extend(successful_symbols)

                    # Track failed symbols
                    failed_in_batch = [s for s in batch if s not in successful_symbols]
                    progress.failed_symbols.extend(failed_in_batch)

                    logger.info(f"Batch {batch_idx + 1}: Saved {len(df)} records for {len(successful_symbols)} stocks")
                else:
                    progress.failed_symbols.extend(batch)
                    logger.warning(f"Batch {batch_idx + 1}: No data retrieved")

            except Exception as e:
                logger.error(f"Error in batch {batch_idx + 1}: {e}")
                progress.failed_symbols.extend(batch)

            # Update progress
            progress.current_batch = batch_idx + 1
            self._save_progress(progress)

            # Delay between batches
            if batch_idx < len(batches) - 1:
                time.sleep(3)

        # Collect stock info for successful symbols
        logger.info("\nCollecting stock info...")
        stock_info_list = []
        for symbol in tqdm(progress.completed_symbols[:500], desc="Stock info"):  # Limit to avoid too many requests
            try:
                info = self.us_collector.get_stock_info(symbol)
                info['last_updated'] = datetime.now()
                stock_info_list.append(info)
                time.sleep(0.05)
            except:
                pass

        if stock_info_list:
            stock_df = pd.DataFrame(stock_info_list)
            self.db.save_stock_info(stock_df, if_exists='append')
            logger.info(f"Saved {len(stock_info_list)} stock info records")

        # Mark as completed
        progress.status = 'completed'
        self._save_progress(progress)

        stats = {
            'status': 'completed',
            'total_symbols': len(all_symbols),
            'completed': len(progress.completed_symbols),
            'failed': len(progress.failed_symbols),
            'total_records': total_records,
            'failed_symbols': progress.failed_symbols[:20]
        }

        logger.info("\n" + "="*60)
        logger.info("US Stock Collection Complete")
        logger.info(f"Total: {stats['total_symbols']}, Success: {stats['completed']}, Failed: {stats['failed']}")
        logger.info("="*60)

        return stats

    def collect_all(self, markets: List[str] = None, resume: bool = True) -> Dict:
        """
        Collect data from all markets

        Args:
            markets: List of markets to collect ('korean', 'us') or None for all
            resume: Resume from previous progress

        Returns:
            Combined collection statistics
        """
        if markets is None:
            markets = ['korean', 'us']

        results = {}

        overall_start = datetime.now()

        if 'korean' in markets:
            results['korean'] = self.collect_korean_stocks(resume=resume)

        if 'us' in markets:
            results['us'] = self.collect_us_stocks(resume=resume)

        overall_end = datetime.now()

        # Summary
        logger.info("\n" + "="*60)
        logger.info("COLLECTION COMPLETE - SUMMARY")
        logger.info("="*60)
        logger.info(f"Total time: {overall_end - overall_start}")

        for market, stats in results.items():
            logger.info(f"\n{market.upper()}:")
            logger.info(f"  Status: {stats.get('status', 'unknown')}")
            logger.info(f"  Symbols: {stats.get('completed', 0)}/{stats.get('total_symbols', 0)}")
            logger.info(f"  Records: {stats.get('total_records', 0)}")
            if stats.get('failed_symbols'):
                logger.info(f"  Failed (sample): {stats['failed_symbols'][:5]}")

        return results

    def get_collection_status(self) -> Dict:
        """Get current collection status for all markets"""
        status = {}

        for market in ['korean', 'us']:
            progress = self._load_progress(market)
            if progress:
                status[market] = {
                    'status': progress.status,
                    'completed': len(progress.completed_symbols),
                    'failed': len(progress.failed_symbols),
                    'total': progress.total_symbols,
                    'progress': f"{len(progress.completed_symbols)}/{progress.total_symbols}",
                    'last_update': progress.last_update
                }
            else:
                status[market] = {'status': 'not_started'}

        return status


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Collect ALL Korean and US stock data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python collect_all_stocks.py                    # Collect all markets
  python collect_all_stocks.py --market korean    # Korean stocks only
  python collect_all_stocks.py --market us        # US stocks only
  python collect_all_stocks.py --no-resume        # Start fresh (ignore previous progress)
  python collect_all_stocks.py --status           # Check collection status
  python collect_all_stocks.py --years 5          # Collect 5 years of data
        """
    )

    parser.add_argument('--market', type=str, choices=['korean', 'us', 'all'],
                        default='all', help='Market to collect (default: all)')
    parser.add_argument('--no-resume', action='store_true',
                        help='Start fresh, ignore previous progress')
    parser.add_argument('--status', action='store_true',
                        help='Show collection status and exit')
    parser.add_argument('--years', type=int, default=3,
                        help='Years of historical data (default: 3)')
    parser.add_argument('--batch-kr', type=int, default=50,
                        help='Batch size for Korean stocks (default: 50)')
    parser.add_argument('--batch-us', type=int, default=100,
                        help='Batch size for US stocks (default: 100)')

    args = parser.parse_args()

    # Initialize collector
    collector = FullStockCollector(
        years=args.years,
        batch_size_kr=args.batch_kr,
        batch_size_us=args.batch_us
    )

    # Check status only
    if args.status:
        status = collector.get_collection_status()
        print("\n=== Collection Status ===")
        for market, info in status.items():
            print(f"\n{market.upper()}:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        return

    # Determine markets to collect
    markets = None
    if args.market != 'all':
        markets = [args.market]

    # Run collection
    resume = not args.no_resume

    print("\n" + "="*60)
    print("FULL STOCK DATA COLLECTION")
    print("="*60)
    print(f"Markets: {markets or 'all'}")
    print(f"Years: {args.years}")
    print(f"Resume: {resume}")
    print("="*60 + "\n")

    results = collector.collect_all(markets=markets, resume=resume)

    # Print final summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    for market, stats in results.items():
        print(f"\n{market.upper()}:")
        print(f"  Total Symbols: {stats.get('total_symbols', 0)}")
        print(f"  Completed: {stats.get('completed', 0)}")
        print(f"  Failed: {stats.get('failed', 0)}")
        print(f"  Total Records: {stats.get('total_records', 0)}")


if __name__ == "__main__":
    main()
