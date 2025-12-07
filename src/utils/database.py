"""
Database utilities for Quantitative Investing System
"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config_loader import get_config
from .logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Database manager for storing and retrieving stock data
    """

    def __init__(self, db_config: Dict[str, Any] = None):
        """
        Initialize database manager

        Args:
            db_config: Database configuration dictionary
        """
        if db_config is None:
            config = get_config()
            db_config = config.get_database_config()

        self.db_type = db_config.get('type', 'sqlite')
        self.engine: Optional[Engine] = None

        # Create engine based on database type
        if self.db_type == 'sqlite':
            db_path = db_config.get('path', 'data/database/quant_investing.db')
            db_path = Path(db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection_string = f"sqlite:///{db_path}"

        elif self.db_type == 'postgresql':
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 5432)
            database = db_config.get('name', 'quant_investing')
            user = db_config.get('user', 'postgres')
            password = db_config.get('password', '')
            self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        elif self.db_type == 'mysql':
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 3306)
            database = db_config.get('name', 'quant_investing')
            user = db_config.get('user', 'root')
            password = db_config.get('password', '')
            self.connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

        self.engine = create_engine(self.connection_string)
        logger.info(f"Database engine created: {self.db_type}")

        # Initialize database schema
        self._initialize_schema()

    def _initialize_schema(self):
        """Initialize database schema (create tables if not exist)"""
        schema_sql = """
        -- Stock Price Data (OHLCV)
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            adj_close REAL,
            market TEXT,
            UNIQUE(symbol, date)
        );

        CREATE INDEX IF NOT EXISTS idx_prices_symbol_date ON stock_prices(symbol, date);
        CREATE INDEX IF NOT EXISTS idx_prices_date ON stock_prices(date);

        -- Stock Fundamental Data
        CREATE TABLE IF NOT EXISTS stock_fundamentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            market_cap REAL,
            per REAL,
            pbr REAL,
            eps REAL,
            bps REAL,
            roe REAL,
            debt_ratio REAL,
            current_ratio REAL,
            revenue REAL,
            operating_income REAL,
            net_income REAL,
            UNIQUE(symbol, date)
        );

        CREATE INDEX IF NOT EXISTS idx_fundamentals_symbol_date ON stock_fundamentals(symbol, date);

        -- Stock Info
        CREATE TABLE IF NOT EXISTS stock_info (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            market TEXT,
            sector TEXT,
            industry TEXT,
            listing_date DATE,
            last_updated TIMESTAMP
        );

        -- Strategy Results
        CREATE TABLE IF NOT EXISTS strategy_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_name TEXT NOT NULL,
            run_date TIMESTAMP NOT NULL,
            start_date DATE,
            end_date DATE,
            total_return REAL,
            annual_return REAL,
            sharpe_ratio REAL,
            max_drawdown REAL,
            win_rate REAL,
            parameters TEXT,
            UNIQUE(strategy_name, run_date)
        );

        -- Portfolio Holdings
        CREATE TABLE IF NOT EXISTS portfolio_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_name TEXT NOT NULL,
            date DATE NOT NULL,
            symbol TEXT NOT NULL,
            weight REAL,
            quantity INTEGER,
            price REAL,
            value REAL,
            UNIQUE(portfolio_name, date, symbol)
        );

        CREATE INDEX IF NOT EXISTS idx_holdings_portfolio_date ON portfolio_holdings(portfolio_name, date);

        -- Background Tasks
        CREATE TABLE IF NOT EXISTS background_tasks (
            id TEXT PRIMARY KEY,
            task_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            total_items INTEGER DEFAULT 0,
            completed_items INTEGER DEFAULT 0,
            current_item TEXT,
            result TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_status ON background_tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_created ON background_tasks(created_at);
        """

        # For SQLite, execute each statement separately
        if self.db_type == 'sqlite':
            with self.engine.begin() as conn:
                for statement in schema_sql.split(';'):
                    statement = statement.strip()
                    if statement:
                        conn.execute(text(statement))
        else:
            # For PostgreSQL/MySQL, adjust the schema
            # (AUTO_INCREMENT -> SERIAL for PostgreSQL, etc.)
            with self.engine.begin() as conn:
                conn.execute(text(schema_sql))

        logger.info("Database schema initialized")

    def save_stock_prices(self, df: pd.DataFrame, if_exists: str = 'append') -> None:
        """
        Save stock price data to database

        Args:
            df: DataFrame with columns: symbol, date, open, high, low, close, volume
            if_exists: 'append' or 'replace'
        """
        if df.empty:
            logger.warning("No data to save")
            return

        if self.db_type == 'sqlite' and if_exists == 'append':
            # Use INSERT OR REPLACE to handle duplicates
            with self.engine.begin() as conn:
                for _, row in df.iterrows():
                    try:
                        # Convert Timestamp to string for SQLite compatibility
                        date_val = row.get('date')
                        if hasattr(date_val, 'strftime'):
                            date_val = date_val.strftime('%Y-%m-%d')
                        elif hasattr(date_val, 'isoformat'):
                            date_val = date_val.isoformat()[:10]

                        conn.execute(text("""
                            INSERT OR REPLACE INTO stock_prices
                            (symbol, date, open, high, low, close, volume, adj_close, market)
                            VALUES (:symbol, :date, :open, :high, :low, :close, :volume, :adj_close, :market)
                        """), {
                            'symbol': row.get('symbol'),
                            'date': date_val,
                            'open': float(row.get('open')) if pd.notna(row.get('open')) else None,
                            'high': float(row.get('high')) if pd.notna(row.get('high')) else None,
                            'low': float(row.get('low')) if pd.notna(row.get('low')) else None,
                            'close': float(row.get('close')) if pd.notna(row.get('close')) else None,
                            'volume': int(row.get('volume')) if pd.notna(row.get('volume')) else None,
                            'adj_close': float(row.get('adj_close')) if pd.notna(row.get('adj_close')) else None,
                            'market': row.get('market')
                        })
                    except Exception as e:
                        logger.warning(f"Error inserting row: {e}")
                        continue
            logger.info(f"Saved {len(df)} price records to database")
        else:
            df.to_sql('stock_prices', self.engine, if_exists=if_exists, index=False)
            logger.info(f"Saved {len(df)} price records to database")

    def get_stock_prices(self,
                        symbol: Union[str, List[str]] = None,
                        start_date: str = None,
                        end_date: str = None) -> pd.DataFrame:
        """
        Get stock price data from database

        Args:
            symbol: Stock symbol(s)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with price data
        """
        query = "SELECT * FROM stock_prices WHERE 1=1"
        params = {}

        if symbol:
            if isinstance(symbol, str):
                query += " AND symbol = :symbol"
                params['symbol'] = symbol
            elif isinstance(symbol, list):
                placeholders = ','.join([f':sym{i}' for i in range(len(symbol))])
                query += f" AND symbol IN ({placeholders})"
                for i, sym in enumerate(symbol):
                    params[f'sym{i}'] = sym

        if start_date:
            query += " AND date >= :start_date"
            params['start_date'] = start_date

        if end_date:
            query += " AND date <= :end_date"
            params['end_date'] = end_date

        query += " ORDER BY date"

        df = pd.read_sql(text(query), self.engine, params=params)

        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        return df

    def save_fundamentals(self, df: pd.DataFrame, if_exists: str = 'append') -> None:
        """Save fundamental data to database"""
        df.to_sql('stock_fundamentals', self.engine, if_exists=if_exists, index=False)
        logger.info(f"Saved {len(df)} fundamental records to database")

    def get_fundamentals(self,
                        symbol: Union[str, List[str]] = None,
                        start_date: str = None,
                        end_date: str = None) -> pd.DataFrame:
        """Get fundamental data from database"""
        query = "SELECT * FROM stock_fundamentals WHERE 1=1"
        params = {}

        if symbol:
            if isinstance(symbol, str):
                query += " AND symbol = :symbol"
                params['symbol'] = symbol
            elif isinstance(symbol, list):
                placeholders = ','.join([f':sym{i}' for i in range(len(symbol))])
                query += f" AND symbol IN ({placeholders})"
                for i, sym in enumerate(symbol):
                    params[f'sym{i}'] = sym

        if start_date:
            query += " AND date >= :start_date"
            params['start_date'] = start_date

        if end_date:
            query += " AND date <= :end_date"
            params['end_date'] = end_date

        query += " ORDER BY date"

        return pd.read_sql(text(query), self.engine, params=params)

    def save_stock_info(self, df: pd.DataFrame, if_exists: str = 'replace') -> None:
        """Save stock information to database"""
        df.to_sql('stock_info', self.engine, if_exists=if_exists, index=False)
        logger.info(f"Saved {len(df)} stock info records to database")

    def get_stock_info(self, symbol: Union[str, List[str]] = None) -> pd.DataFrame:
        """Get stock information from database"""
        query = "SELECT * FROM stock_info"
        params = {}

        if symbol:
            if isinstance(symbol, str):
                query += " WHERE symbol = :symbol"
                params['symbol'] = symbol
            elif isinstance(symbol, list):
                placeholders = ','.join([f':sym{i}' for i in range(len(symbol))])
                query += f" WHERE symbol IN ({placeholders})"
                for i, sym in enumerate(symbol):
                    params[f'sym{i}'] = sym

        return pd.read_sql(text(query), self.engine, params=params)

    def get_all_symbols(self, market: str = None) -> List[str]:
        """
        Get all stock symbols

        Args:
            market: Filter by market (KOSPI, KOSDAQ, NYSE, NASDAQ, etc.)

        Returns:
            List of symbols
        """
        query = "SELECT DISTINCT symbol FROM stock_info"
        params = {}

        if market:
            query += " WHERE market = :market"
            params['market'] = market

        df = pd.read_sql(text(query), self.engine, params=params)
        return df['symbol'].tolist()

    def execute_query(self, query: str, params: Dict = None) -> pd.DataFrame:
        """
        Execute custom SQL query

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query result as DataFrame
        """
        return pd.read_sql(text(query), self.engine, params=params or {})

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# Global database instance
_db_instance = None


def get_db() -> DatabaseManager:
    """
    Get global database instance (singleton pattern)

    Returns:
        DatabaseManager instance
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = DatabaseManager()

    return _db_instance
