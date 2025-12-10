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

        -- Extended Fundamentals (comprehensive metrics)
        CREATE TABLE IF NOT EXISTS extended_fundamentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,

            -- Valuation Metrics
            market_cap REAL,
            enterprise_value REAL,
            per REAL,
            forward_per REAL,
            pbr REAL,
            psr REAL,
            peg_ratio REAL,
            ev_to_ebitda REAL,
            ev_to_revenue REAL,

            -- Per Share Metrics
            eps REAL,
            forward_eps REAL,
            bps REAL,
            revenue_per_share REAL,

            -- Profitability Metrics
            roe REAL,
            roa REAL,
            gross_margin REAL,
            operating_margin REAL,
            profit_margin REAL,
            ebitda_margin REAL,

            -- Growth Metrics
            revenue_growth REAL,
            earnings_growth REAL,
            earnings_quarterly_growth REAL,

            -- Financial Health
            debt_ratio REAL,
            current_ratio REAL,
            quick_ratio REAL,
            total_debt REAL,
            total_cash REAL,
            total_cash_per_share REAL,
            interest_coverage REAL,

            -- Income Statement
            revenue REAL,
            gross_profit REAL,
            operating_income REAL,
            ebitda REAL,
            net_income REAL,

            -- Cash Flow Metrics
            operating_cash_flow REAL,
            free_cash_flow REAL,
            fcf_yield REAL,
            cf_to_debt REAL,

            -- Dividend Metrics
            dividend_yield REAL,
            dividend_rate REAL,
            payout_ratio REAL,
            ex_dividend_date DATE,
            five_year_avg_dividend_yield REAL,

            -- Risk Metrics
            beta REAL,
            fifty_two_week_high REAL,
            fifty_two_week_low REAL,
            fifty_day_average REAL,
            two_hundred_day_average REAL,
            price_to_52w_high REAL,
            price_to_52w_low REAL,
            price_52w_range_pct REAL,

            -- Volume & Liquidity
            avg_volume REAL,
            avg_volume_10d REAL,
            shares_outstanding REAL,
            float_shares REAL,
            shares_short REAL,
            short_ratio REAL,
            short_percent_of_float REAL,

            -- Ownership
            held_percent_insiders REAL,
            held_percent_institutions REAL,

            -- Analyst Data
            target_high_price REAL,
            target_low_price REAL,
            target_mean_price REAL,
            target_median_price REAL,
            recommendation_mean REAL,
            recommendation_key TEXT,
            number_of_analyst_opinions INTEGER,
            upside_to_target REAL,

            -- Company Info
            sector TEXT,
            industry TEXT,
            full_time_employees INTEGER,

            UNIQUE(symbol, date)
        );

        CREATE INDEX IF NOT EXISTS idx_extended_fund_symbol_date ON extended_fundamentals(symbol, date);
        CREATE INDEX IF NOT EXISTS idx_extended_fund_sector ON extended_fundamentals(sector);

        -- Financial Health Scores (F-Score, Z-Score)
        CREATE TABLE IF NOT EXISTS financial_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,

            -- Piotroski F-Score (0-9)
            f_score INTEGER,
            positive_net_income INTEGER,
            positive_ocf INTEGER,
            roa_improvement INTEGER,
            earnings_quality INTEGER,
            debt_decrease INTEGER,
            current_ratio_increase INTEGER,
            no_dilution INTEGER,
            gross_margin_increase INTEGER,
            asset_turnover_increase INTEGER,

            -- Altman Z-Score
            z_score REAL,
            z_score_zone TEXT,
            working_capital_to_assets REAL,
            retained_earnings_to_assets REAL,
            ebit_to_assets REAL,
            market_cap_to_liabilities REAL,
            revenue_to_assets REAL,

            UNIQUE(symbol, date)
        );

        CREATE INDEX IF NOT EXISTS idx_scores_symbol_date ON financial_scores(symbol, date);

        -- Dividend History
        CREATE TABLE IF NOT EXISTS dividend_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            dividend REAL,
            UNIQUE(symbol, date)
        );

        CREATE INDEX IF NOT EXISTS idx_dividend_symbol_date ON dividend_history(symbol, date);

        -- Analyst Recommendations
        CREATE TABLE IF NOT EXISTS analyst_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            firm TEXT,
            to_grade TEXT,
            from_grade TEXT,
            action TEXT,
            UNIQUE(symbol, date, firm)
        );

        CREATE INDEX IF NOT EXISTS idx_analyst_symbol_date ON analyst_recommendations(symbol, date);

        -- Earnings History (Actual vs Estimate)
        CREATE TABLE IF NOT EXISTS earnings_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            eps_actual REAL,
            eps_estimate REAL,
            earnings_surprise REAL,
            earnings_surprise_pct REAL,
            UNIQUE(symbol, date)
        );

        CREATE INDEX IF NOT EXISTS idx_earnings_symbol_date ON earnings_history(symbol, date);

        -- Institutional Holdings
        CREATE TABLE IF NOT EXISTS institutional_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            holder TEXT,
            shares REAL,
            date_reported DATE,
            pct_held REAL,
            value REAL
        );

        CREATE INDEX IF NOT EXISTS idx_inst_holdings_symbol ON institutional_holdings(symbol);

        -- Insider Transactions
        CREATE TABLE IF NOT EXISTS insider_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            insider TEXT,
            position TEXT,
            transaction_type TEXT,
            shares REAL,
            value REAL,
            shares_owned REAL
        );

        CREATE INDEX IF NOT EXISTS idx_insider_symbol_date ON insider_transactions(symbol, date);
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

    def save_extended_fundamentals(self, df: pd.DataFrame, if_exists: str = 'append') -> None:
        """Save extended fundamental data to database"""
        df.to_sql('extended_fundamentals', self.engine, if_exists=if_exists, index=False)
        logger.info(f"Saved {len(df)} extended fundamental records to database")

    def get_extended_fundamentals(self,
                                  symbol: Union[str, List[str]] = None,
                                  start_date: str = None,
                                  end_date: str = None) -> pd.DataFrame:
        """Get extended fundamental data from database"""
        query = "SELECT * FROM extended_fundamentals WHERE 1=1"
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

        query += " ORDER BY date DESC"

        return pd.read_sql(text(query), self.engine, params=params)

    def save_financial_scores(self, df: pd.DataFrame, if_exists: str = 'append') -> None:
        """Save financial health scores (F-Score, Z-Score) to database"""
        df.to_sql('financial_scores', self.engine, if_exists=if_exists, index=False)
        logger.info(f"Saved {len(df)} financial score records to database")

    def get_financial_scores(self,
                            symbol: Union[str, List[str]] = None,
                            start_date: str = None,
                            end_date: str = None) -> pd.DataFrame:
        """Get financial health scores from database"""
        query = "SELECT * FROM financial_scores WHERE 1=1"
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

        query += " ORDER BY date DESC"

        return pd.read_sql(text(query), self.engine, params=params)

    def save_dividend_history(self, df: pd.DataFrame, if_exists: str = 'append') -> None:
        """Save dividend history to database"""
        df.to_sql('dividend_history', self.engine, if_exists=if_exists, index=False)
        logger.info(f"Saved {len(df)} dividend records to database")

    def get_dividend_history(self, symbol: Union[str, List[str]] = None) -> pd.DataFrame:
        """Get dividend history from database"""
        query = "SELECT * FROM dividend_history"
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

        query += " ORDER BY date DESC"

        return pd.read_sql(text(query), self.engine, params=params)

    def save_analyst_recommendations(self, df: pd.DataFrame, if_exists: str = 'append') -> None:
        """Save analyst recommendations to database"""
        df.to_sql('analyst_recommendations', self.engine, if_exists=if_exists, index=False)
        logger.info(f"Saved {len(df)} analyst recommendation records to database")

    def get_analyst_recommendations(self, symbol: Union[str, List[str]] = None) -> pd.DataFrame:
        """Get analyst recommendations from database"""
        query = "SELECT * FROM analyst_recommendations"
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

        query += " ORDER BY date DESC"

        return pd.read_sql(text(query), self.engine, params=params)

    def save_earnings_history(self, df: pd.DataFrame, if_exists: str = 'append') -> None:
        """Save earnings history to database"""
        df.to_sql('earnings_history', self.engine, if_exists=if_exists, index=False)
        logger.info(f"Saved {len(df)} earnings history records to database")

    def get_earnings_history(self, symbol: Union[str, List[str]] = None) -> pd.DataFrame:
        """Get earnings history from database"""
        query = "SELECT * FROM earnings_history"
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

        query += " ORDER BY date DESC"

        return pd.read_sql(text(query), self.engine, params=params)

    def save_institutional_holdings(self, df: pd.DataFrame, if_exists: str = 'append') -> None:
        """Save institutional holdings to database"""
        df.to_sql('institutional_holdings', self.engine, if_exists=if_exists, index=False)
        logger.info(f"Saved {len(df)} institutional holding records to database")

    def get_institutional_holdings(self, symbol: Union[str, List[str]] = None) -> pd.DataFrame:
        """Get institutional holdings from database"""
        query = "SELECT * FROM institutional_holdings"
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

    def save_insider_transactions(self, df: pd.DataFrame, if_exists: str = 'append') -> None:
        """Save insider transactions to database"""
        df.to_sql('insider_transactions', self.engine, if_exists=if_exists, index=False)
        logger.info(f"Saved {len(df)} insider transaction records to database")

    def get_insider_transactions(self, symbol: Union[str, List[str]] = None) -> pd.DataFrame:
        """Get insider transactions from database"""
        query = "SELECT * FROM insider_transactions"
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

        query += " ORDER BY date DESC"

        return pd.read_sql(text(query), self.engine, params=params)

    def get_screening_data(self,
                          symbols: List[str] = None,
                          date: str = None) -> pd.DataFrame:
        """
        Get comprehensive data for stock screening

        Args:
            symbols: List of symbols to screen
            date: Date for screening (defaults to latest)

        Returns:
            DataFrame with all screening data
        """
        # Get latest extended fundamentals
        ext_query = """
            SELECT ef.* FROM extended_fundamentals ef
            INNER JOIN (
                SELECT symbol, MAX(date) as max_date
                FROM extended_fundamentals
                GROUP BY symbol
            ) latest ON ef.symbol = latest.symbol AND ef.date = latest.max_date
        """

        if symbols:
            placeholders = ','.join([f"'{s}'" for s in symbols])
            ext_query = f"""
                SELECT ef.* FROM extended_fundamentals ef
                INNER JOIN (
                    SELECT symbol, MAX(date) as max_date
                    FROM extended_fundamentals
                    WHERE symbol IN ({placeholders})
                    GROUP BY symbol
                ) latest ON ef.symbol = latest.symbol AND ef.date = latest.max_date
            """

        ext_df = pd.read_sql(text(ext_query), self.engine)

        # Get latest financial scores
        scores_query = """
            SELECT fs.* FROM financial_scores fs
            INNER JOIN (
                SELECT symbol, MAX(date) as max_date
                FROM financial_scores
                GROUP BY symbol
            ) latest ON fs.symbol = latest.symbol AND fs.date = latest.max_date
        """

        scores_df = pd.read_sql(text(scores_query), self.engine)

        # Merge data
        if not ext_df.empty and not scores_df.empty:
            # Remove duplicate columns before merge
            scores_cols = [c for c in scores_df.columns if c not in ext_df.columns or c == 'symbol']
            result = ext_df.merge(scores_df[scores_cols], on='symbol', how='left')
        elif not ext_df.empty:
            result = ext_df
        elif not scores_df.empty:
            result = scores_df
        else:
            result = pd.DataFrame()

        return result

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
