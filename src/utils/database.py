"""
Database utilities for Quantitative Investing System
"""
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

        self.db_type = db_config.get('type', 'postgresql')
        self.engine: Optional[Engine] = None

        # Create engine based on database type
        if self.db_type == 'postgresql':
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 5432)
            database = db_config.get('name', 'quant_investing')
            user = db_config.get('user', 'postgres')
            password = db_config.get('password', 'postgres')
            self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        elif self.db_type == 'sqlite':
            db_path = db_config.get('path', 'data/database/quant_investing.db')
            db_path = Path(db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection_string = f"sqlite:///{db_path}"

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
        if self.db_type == 'postgresql':
            self._initialize_postgresql_schema()
        elif self.db_type == 'sqlite':
            self._initialize_sqlite_schema()
        else:
            self._initialize_sqlite_schema()

        logger.info("Database schema initialized")

    def _initialize_postgresql_schema(self):
        """Initialize PostgreSQL database schema"""
        schema_statements = [
            # Stock Price Data (OHLCV)
            """
            CREATE TABLE IF NOT EXISTS stock_prices (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                open DOUBLE PRECISION,
                high DOUBLE PRECISION,
                low DOUBLE PRECISION,
                close DOUBLE PRECISION,
                volume BIGINT,
                adj_close DOUBLE PRECISION,
                market VARCHAR(50),
                UNIQUE(symbol, date)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_prices_symbol_date ON stock_prices(symbol, date)",
            "CREATE INDEX IF NOT EXISTS idx_prices_date ON stock_prices(date)",
            # Add UNIQUE constraint if it doesn't exist (for existing tables)
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'stock_prices_symbol_date_key'
                    OR conname = 'uq_stock_prices_symbol_date'
                ) THEN
                    BEGIN
                        ALTER TABLE stock_prices ADD CONSTRAINT uq_stock_prices_symbol_date UNIQUE (symbol, date);
                    EXCEPTION WHEN others THEN
                        NULL;
                    END;
                END IF;
            END $$
            """,

            # Stock Fundamental Data
            """
            CREATE TABLE IF NOT EXISTS stock_fundamentals (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                market_cap DOUBLE PRECISION,
                per DOUBLE PRECISION,
                pbr DOUBLE PRECISION,
                eps DOUBLE PRECISION,
                bps DOUBLE PRECISION,
                roe DOUBLE PRECISION,
                debt_ratio DOUBLE PRECISION,
                current_ratio DOUBLE PRECISION,
                revenue DOUBLE PRECISION,
                operating_income DOUBLE PRECISION,
                net_income DOUBLE PRECISION,
                UNIQUE(symbol, date)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_fundamentals_symbol_date ON stock_fundamentals(symbol, date)",

            # Stock Info
            """
            CREATE TABLE IF NOT EXISTS stock_info (
                symbol VARCHAR(50) PRIMARY KEY,
                name VARCHAR(200),
                market VARCHAR(50),
                sector VARCHAR(100),
                industry VARCHAR(100),
                listing_date DATE,
                last_updated TIMESTAMP
            )
            """,

            # Strategy Results
            """
            CREATE TABLE IF NOT EXISTS strategy_results (
                id SERIAL PRIMARY KEY,
                strategy_name VARCHAR(100) NOT NULL,
                run_date TIMESTAMP NOT NULL,
                start_date DATE,
                end_date DATE,
                total_return DOUBLE PRECISION,
                annual_return DOUBLE PRECISION,
                sharpe_ratio DOUBLE PRECISION,
                max_drawdown DOUBLE PRECISION,
                win_rate DOUBLE PRECISION,
                parameters TEXT,
                UNIQUE(strategy_name, run_date)
            )
            """,

            # Portfolio Holdings
            """
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                id SERIAL PRIMARY KEY,
                portfolio_name VARCHAR(100) NOT NULL,
                date DATE NOT NULL,
                symbol VARCHAR(50) NOT NULL,
                weight DOUBLE PRECISION,
                quantity INTEGER,
                price DOUBLE PRECISION,
                value DOUBLE PRECISION,
                UNIQUE(portfolio_name, date, symbol)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_holdings_portfolio_date ON portfolio_holdings(portfolio_name, date)",

            # Background Tasks
            """
            CREATE TABLE IF NOT EXISTS background_tasks (
                id VARCHAR(100) PRIMARY KEY,
                task_type VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                total_items INTEGER DEFAULT 0,
                completed_items INTEGER DEFAULT 0,
                current_item VARCHAR(200),
                result TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON background_tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_created ON background_tasks(created_at)"
        ]

        with self.engine.begin() as conn:
            for statement in schema_statements:
                try:
                    conn.execute(text(statement.strip()))
                except Exception as e:
                    logger.warning(f"Schema statement warning: {e}")

    def _initialize_sqlite_schema(self):
        """Initialize SQLite database schema"""
        schema_sql = """
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
        CREATE TABLE IF NOT EXISTS stock_info (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            market TEXT,
            sector TEXT,
            industry TEXT,
            listing_date DATE,
            last_updated TIMESTAMP
        );
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

        with self.engine.begin() as conn:
            for statement in schema_sql.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))

    def save_stock_prices(self, df: pd.DataFrame, if_exists: str = 'append', batch_size: int = 500) -> None:
        """
        Save stock price data to database

        Args:
            df: DataFrame with columns: symbol, date, open, high, low, close, volume
            if_exists: 'append' or 'replace'
            batch_size: Number of rows to insert per batch (for PostgreSQL)
        """
        if df.empty:
            logger.warning("No data to save")
            return

        if if_exists == 'append':
            # Prepare all rows first
            rows_to_insert = []
            for _, row in df.iterrows():
                # Convert Timestamp to string for compatibility
                date_val = row.get('date')
                if hasattr(date_val, 'strftime'):
                    date_val = date_val.strftime('%Y-%m-%d')
                elif hasattr(date_val, 'isoformat'):
                    date_val = date_val.isoformat()[:10]

                rows_to_insert.append({
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

            success_count = 0
            error_count = 0

            if self.db_type == 'postgresql':
                # PostgreSQL: Use batch upsert for better performance
                upsert_sql = text("""
                    INSERT INTO stock_prices
                    (symbol, date, open, high, low, close, volume, adj_close, market)
                    VALUES (:symbol, :date, :open, :high, :low, :close, :volume, :adj_close, :market)
                    ON CONFLICT (symbol, date) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        adj_close = EXCLUDED.adj_close,
                        market = EXCLUDED.market
                """)

                # Fallback: DELETE then INSERT (for tables without UNIQUE constraint)
                delete_sql = text("DELETE FROM stock_prices WHERE symbol = :symbol AND date = :date")
                insert_sql = text("""
                    INSERT INTO stock_prices
                    (symbol, date, open, high, low, close, volume, adj_close, market)
                    VALUES (:symbol, :date, :open, :high, :low, :close, :volume, :adj_close, :market)
                """)

                # Process in batches
                for i in range(0, len(rows_to_insert), batch_size):
                    batch = rows_to_insert[i:i + batch_size]
                    try:
                        with self.engine.begin() as conn:
                            conn.execute(upsert_sql, batch)
                        success_count += len(batch)
                    except Exception as e:
                        # If ON CONFLICT fails (no UNIQUE constraint), use DELETE + INSERT
                        if 'unique' in str(e).lower() or 'conflict' in str(e).lower():
                            logger.info("Using DELETE+INSERT fallback (no UNIQUE constraint)")
                            for params in batch:
                                try:
                                    with self.engine.begin() as conn:
                                        conn.execute(delete_sql, {'symbol': params['symbol'], 'date': params['date']})
                                        conn.execute(insert_sql, params)
                                    success_count += 1
                                except Exception as e2:
                                    error_count += 1
                                    if error_count <= 5:
                                        logger.warning(f"Error inserting row {params.get('symbol')} {params.get('date')}: {e2}")
                        else:
                            # Other errors: try individual upserts
                            logger.warning(f"Batch insert failed, trying individual inserts: {e}")
                            for params in batch:
                                try:
                                    with self.engine.begin() as conn:
                                        conn.execute(upsert_sql, params)
                                    success_count += 1
                                except Exception as e2:
                                    # Final fallback: DELETE + INSERT
                                    try:
                                        with self.engine.begin() as conn:
                                            conn.execute(delete_sql, {'symbol': params['symbol'], 'date': params['date']})
                                            conn.execute(insert_sql, params)
                                        success_count += 1
                                    except Exception as e3:
                                        error_count += 1
                                        if error_count <= 5:
                                            logger.warning(f"Error inserting row {params.get('symbol')} {params.get('date')}: {e3}")
            else:
                # SQLite: Use individual inserts with INSERT OR REPLACE
                for params in rows_to_insert:
                    try:
                        with self.engine.begin() as conn:
                            conn.execute(text("""
                                INSERT OR REPLACE INTO stock_prices
                                (symbol, date, open, high, low, close, volume, adj_close, market)
                                VALUES (:symbol, :date, :open, :high, :low, :close, :volume, :adj_close, :market)
                            """), params)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        if error_count <= 5:
                            logger.warning(f"Error inserting row {params.get('symbol')} {params.get('date')}: {e}")

            if error_count > 5:
                logger.warning(f"... and {error_count - 5} more errors")
            logger.info(f"Saved {success_count}/{len(df)} price records to database ({error_count} errors)")
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
            # Handle various date formats including those with time components
            # First convert to string and extract only the date part (YYYY-MM-DD)
            date_str = df['date'].astype(str).str.strip()
            # Extract first 10 characters (YYYY-MM-DD) to handle formats like "2020-01-01 00:00:00"
            date_str = date_str.str[:10]
            df['date'] = pd.to_datetime(date_str, format='%Y-%m-%d', errors='coerce')

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
        if df.empty:
            logger.warning("No stock info to save")
            return

        if self.db_type == 'postgresql':
            # PostgreSQL: Use upsert for better handling
            success_count = 0
            error_count = 0

            upsert_sql = text("""
                INSERT INTO stock_info (symbol, name, market, sector, industry, listing_date, last_updated)
                VALUES (:symbol, :name, :market, :sector, :industry, :listing_date, :last_updated)
                ON CONFLICT (symbol) DO UPDATE SET
                    name = EXCLUDED.name,
                    market = EXCLUDED.market,
                    sector = EXCLUDED.sector,
                    industry = EXCLUDED.industry,
                    listing_date = EXCLUDED.listing_date,
                    last_updated = EXCLUDED.last_updated
            """)

            # Fallback: DELETE then INSERT
            delete_sql = text("DELETE FROM stock_info WHERE symbol = :symbol")
            insert_sql = text("""
                INSERT INTO stock_info (symbol, name, market, sector, industry, listing_date, last_updated)
                VALUES (:symbol, :name, :market, :sector, :industry, :listing_date, :last_updated)
            """)

            for _, row in df.iterrows():
                params = {
                    'symbol': row.get('symbol'),
                    'name': row.get('name'),
                    'market': row.get('market'),
                    'sector': row.get('sector'),
                    'industry': row.get('industry'),
                    'listing_date': row.get('listing_date') if pd.notna(row.get('listing_date')) else None,
                    'last_updated': row.get('last_updated') if pd.notna(row.get('last_updated')) else None
                }

                try:
                    with self.engine.begin() as conn:
                        conn.execute(upsert_sql, params)
                    success_count += 1
                except Exception as e:
                    # Fallback: DELETE + INSERT
                    try:
                        with self.engine.begin() as conn:
                            conn.execute(delete_sql, {'symbol': params['symbol']})
                            conn.execute(insert_sql, params)
                        success_count += 1
                    except Exception as e2:
                        error_count += 1
                        if error_count <= 5:
                            logger.warning(f"Error inserting stock_info {params.get('symbol')}: {e2}")

            if error_count > 5:
                logger.warning(f"... and {error_count - 5} more errors")
            logger.info(f"Saved {success_count}/{len(df)} stock info records to database ({error_count} errors)")
        else:
            # SQLite: Use to_sql with replace
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
