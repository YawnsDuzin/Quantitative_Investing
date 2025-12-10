"""
Stock Screener Module
Comprehensive stock screening with multiple criteria
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import get_logger
from ..utils.database import get_db
from ..utils.helpers import rank_normalize

logger = get_logger(__name__)


class FilterOperator(Enum):
    """Filter comparison operators"""
    GREATER_THAN = 'gt'
    GREATER_EQUAL = 'gte'
    LESS_THAN = 'lt'
    LESS_EQUAL = 'lte'
    EQUAL = 'eq'
    NOT_EQUAL = 'ne'
    BETWEEN = 'between'
    IN = 'in'
    NOT_IN = 'not_in'
    TOP_N = 'top_n'
    BOTTOM_N = 'bottom_n'
    TOP_PCT = 'top_pct'
    BOTTOM_PCT = 'bottom_pct'


@dataclass
class ScreeningCriteria:
    """Single screening criterion"""
    field: str
    operator: FilterOperator
    value: Union[float, List, tuple]
    description: str = ""


class StockScreener:
    """
    Comprehensive stock screener with multiple screening criteria

    Supports filtering by:
    - Valuation (P/E, P/B, P/S, PEG, EV/EBITDA)
    - Profitability (ROE, ROA, margins)
    - Growth (revenue, earnings growth)
    - Financial health (F-Score, Z-Score, current ratio, debt)
    - Dividend (yield, payout ratio)
    - Momentum (price performance)
    - Analyst (recommendations, target price)
    - Ownership (institutional, insider)
    - Technical (52-week position, volume)
    """

    # Pre-defined screening templates
    TEMPLATES = {
        'value': {
            'name': 'Value Stocks',
            'description': 'Low valuation, strong fundamentals',
            'criteria': [
                ScreeningCriteria('per', FilterOperator.LESS_THAN, 15, 'P/E < 15'),
                ScreeningCriteria('pbr', FilterOperator.LESS_THAN, 1.5, 'P/B < 1.5'),
                ScreeningCriteria('peg_ratio', FilterOperator.LESS_THAN, 1.0, 'PEG < 1'),
                ScreeningCriteria('roe', FilterOperator.GREATER_THAN, 0.10, 'ROE > 10%'),
            ]
        },
        'growth': {
            'name': 'Growth Stocks',
            'description': 'High growth, strong momentum',
            'criteria': [
                ScreeningCriteria('revenue_growth', FilterOperator.GREATER_THAN, 0.15, 'Revenue Growth > 15%'),
                ScreeningCriteria('earnings_growth', FilterOperator.GREATER_THAN, 0.15, 'Earnings Growth > 15%'),
                ScreeningCriteria('gross_margin', FilterOperator.GREATER_THAN, 0.30, 'Gross Margin > 30%'),
            ]
        },
        'quality': {
            'name': 'Quality Stocks',
            'description': 'High quality, financially healthy',
            'criteria': [
                ScreeningCriteria('f_score', FilterOperator.GREATER_EQUAL, 7, 'F-Score >= 7'),
                ScreeningCriteria('roe', FilterOperator.GREATER_THAN, 0.15, 'ROE > 15%'),
                ScreeningCriteria('debt_ratio', FilterOperator.LESS_THAN, 100, 'Debt/Equity < 100%'),
                ScreeningCriteria('current_ratio', FilterOperator.GREATER_THAN, 1.5, 'Current Ratio > 1.5'),
            ]
        },
        'dividend': {
            'name': 'Dividend Stocks',
            'description': 'High dividend yield, sustainable payout',
            'criteria': [
                ScreeningCriteria('dividend_yield', FilterOperator.GREATER_THAN, 0.03, 'Dividend Yield > 3%'),
                ScreeningCriteria('payout_ratio', FilterOperator.LESS_THAN, 0.70, 'Payout Ratio < 70%'),
                ScreeningCriteria('f_score', FilterOperator.GREATER_EQUAL, 5, 'F-Score >= 5'),
            ]
        },
        'momentum': {
            'name': 'Momentum Stocks',
            'description': 'Strong price momentum, institutional buying',
            'criteria': [
                ScreeningCriteria('price_52w_range_pct', FilterOperator.GREATER_THAN, 0.7, 'Price near 52-week high'),
                ScreeningCriteria('held_percent_institutions', FilterOperator.GREATER_THAN, 0.50, 'Institutional > 50%'),
                ScreeningCriteria('avg_volume', FilterOperator.GREATER_THAN, 500000, 'Avg Volume > 500K'),
            ]
        },
        'small_cap_value': {
            'name': 'Small Cap Value',
            'description': 'Small cap stocks at attractive valuations',
            'criteria': [
                ScreeningCriteria('market_cap', FilterOperator.BETWEEN, (500e6, 2e9), 'Market Cap $500M-$2B'),
                ScreeningCriteria('per', FilterOperator.LESS_THAN, 15, 'P/E < 15'),
                ScreeningCriteria('pbr', FilterOperator.LESS_THAN, 2.0, 'P/B < 2'),
                ScreeningCriteria('f_score', FilterOperator.GREATER_EQUAL, 6, 'F-Score >= 6'),
            ]
        },
        'large_cap_quality': {
            'name': 'Large Cap Quality',
            'description': 'Large cap with high quality metrics',
            'criteria': [
                ScreeningCriteria('market_cap', FilterOperator.GREATER_THAN, 10e9, 'Market Cap > $10B'),
                ScreeningCriteria('roe', FilterOperator.GREATER_THAN, 0.20, 'ROE > 20%'),
                ScreeningCriteria('operating_margin', FilterOperator.GREATER_THAN, 0.15, 'Operating Margin > 15%'),
                ScreeningCriteria('debt_ratio', FilterOperator.LESS_THAN, 50, 'Debt/Equity < 50%'),
            ]
        },
        'turnaround': {
            'name': 'Turnaround Candidates',
            'description': 'Underperformers with improving fundamentals',
            'criteria': [
                ScreeningCriteria('price_to_52w_high', FilterOperator.LESS_THAN, 0.7, 'Price < 70% of 52-week high'),
                ScreeningCriteria('z_score', FilterOperator.GREATER_THAN, 1.81, 'Z-Score > 1.81 (not distressed)'),
                ScreeningCriteria('current_ratio', FilterOperator.GREATER_THAN, 1.0, 'Current Ratio > 1'),
            ]
        },
        'analyst_favorites': {
            'name': 'Analyst Favorites',
            'description': 'Strong analyst recommendations with upside',
            'criteria': [
                ScreeningCriteria('recommendation_mean', FilterOperator.LESS_THAN, 2.5, 'Buy rating (< 2.5)'),
                ScreeningCriteria('upside_to_target', FilterOperator.GREATER_THAN, 0.15, 'Upside > 15%'),
                ScreeningCriteria('number_of_analyst_opinions', FilterOperator.GREATER_THAN, 5, '> 5 analysts'),
            ]
        },
        'high_short_interest': {
            'name': 'High Short Interest',
            'description': 'Stocks with high short interest (potential squeeze)',
            'criteria': [
                ScreeningCriteria('short_percent_of_float', FilterOperator.GREATER_THAN, 0.10, 'Short Interest > 10%'),
                ScreeningCriteria('short_ratio', FilterOperator.GREATER_THAN, 5, 'Days to Cover > 5'),
                ScreeningCriteria('avg_volume', FilterOperator.GREATER_THAN, 1000000, 'Avg Volume > 1M'),
            ]
        },
        'insider_buying': {
            'name': 'Insider Buying',
            'description': 'Stocks with significant insider ownership',
            'criteria': [
                ScreeningCriteria('held_percent_insiders', FilterOperator.GREATER_THAN, 0.10, 'Insider Holdings > 10%'),
                ScreeningCriteria('market_cap', FilterOperator.GREATER_THAN, 500e6, 'Market Cap > $500M'),
            ]
        },
    }

    def __init__(self):
        """Initialize stock screener"""
        self.db = get_db()
        self.criteria: List[ScreeningCriteria] = []
        logger.info("Stock Screener initialized")

    def add_criterion(self,
                     field: str,
                     operator: Union[FilterOperator, str],
                     value: Union[float, List, tuple],
                     description: str = "") -> 'StockScreener':
        """
        Add a screening criterion

        Args:
            field: Column name to filter
            operator: Comparison operator
            value: Filter value
            description: Human-readable description

        Returns:
            Self for method chaining
        """
        if isinstance(operator, str):
            operator = FilterOperator(operator)

        criterion = ScreeningCriteria(field, operator, value, description)
        self.criteria.append(criterion)

        return self

    def clear_criteria(self) -> 'StockScreener':
        """Clear all screening criteria"""
        self.criteria = []
        return self

    def load_template(self, template_name: str) -> 'StockScreener':
        """
        Load a pre-defined screening template

        Args:
            template_name: Name of template (e.g., 'value', 'growth', 'quality')

        Returns:
            Self for method chaining
        """
        if template_name not in self.TEMPLATES:
            available = list(self.TEMPLATES.keys())
            raise ValueError(f"Unknown template: {template_name}. Available: {available}")

        template = self.TEMPLATES[template_name]
        self.criteria = template['criteria'].copy()

        logger.info(f"Loaded screening template: {template['name']}")
        return self

    def apply_filter(self, df: pd.DataFrame, criterion: ScreeningCriteria) -> pd.DataFrame:
        """
        Apply a single filter criterion to dataframe

        Args:
            df: Input dataframe
            criterion: Screening criterion

        Returns:
            Filtered dataframe
        """
        field = criterion.field
        op = criterion.operator
        value = criterion.value

        if field not in df.columns:
            logger.warning(f"Field '{field}' not in dataframe, skipping filter")
            return df

        # Handle missing values
        mask = df[field].notna()

        if op == FilterOperator.GREATER_THAN:
            mask &= df[field] > value
        elif op == FilterOperator.GREATER_EQUAL:
            mask &= df[field] >= value
        elif op == FilterOperator.LESS_THAN:
            mask &= df[field] < value
        elif op == FilterOperator.LESS_EQUAL:
            mask &= df[field] <= value
        elif op == FilterOperator.EQUAL:
            mask &= df[field] == value
        elif op == FilterOperator.NOT_EQUAL:
            mask &= df[field] != value
        elif op == FilterOperator.BETWEEN:
            mask &= (df[field] >= value[0]) & (df[field] <= value[1])
        elif op == FilterOperator.IN:
            mask &= df[field].isin(value)
        elif op == FilterOperator.NOT_IN:
            mask &= ~df[field].isin(value)
        elif op == FilterOperator.TOP_N:
            # Select top N by value
            top_indices = df[field].nlargest(int(value)).index
            mask = df.index.isin(top_indices)
        elif op == FilterOperator.BOTTOM_N:
            # Select bottom N by value
            bottom_indices = df[field].nsmallest(int(value)).index
            mask = df.index.isin(bottom_indices)
        elif op == FilterOperator.TOP_PCT:
            # Select top percentage
            threshold = df[field].quantile(1 - value)
            mask &= df[field] >= threshold
        elif op == FilterOperator.BOTTOM_PCT:
            # Select bottom percentage
            threshold = df[field].quantile(value)
            mask &= df[field] <= threshold

        return df[mask]

    def screen(self,
              df: pd.DataFrame = None,
              symbols: List[str] = None,
              return_scores: bool = False) -> pd.DataFrame:
        """
        Run screening with all criteria

        Args:
            df: Input dataframe (if None, fetches from database)
            symbols: Optional list of symbols to screen
            return_scores: If True, add composite score column

        Returns:
            Filtered dataframe
        """
        if df is None:
            df = self.db.get_screening_data(symbols)

        if df.empty:
            logger.warning("No data available for screening")
            return df

        original_count = len(df)
        logger.info(f"Starting screening with {original_count} stocks")

        # Apply each criterion
        for criterion in self.criteria:
            df = self.apply_filter(df, criterion)
            logger.info(f"After '{criterion.description or criterion.field}': {len(df)} stocks")

        logger.info(f"Screening complete: {len(df)} stocks passed (from {original_count})")

        # Calculate composite score if requested
        if return_scores and not df.empty:
            df = self._calculate_composite_score(df)

        return df

    def _calculate_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate a composite score based on multiple factors

        Args:
            df: Screened dataframe

        Returns:
            DataFrame with added score columns
        """
        df = df.copy()

        scores = []

        # Value score (lower valuation = higher score)
        value_cols = ['per', 'pbr', 'peg_ratio', 'ev_to_ebitda']
        for col in value_cols:
            if col in df.columns and df[col].notna().any():
                # Invert so lower is better
                df[f'{col}_score'] = 1 - rank_normalize(df[col])
                scores.append(f'{col}_score')

        # Quality score (higher = better)
        quality_cols = ['roe', 'roa', 'gross_margin', 'operating_margin', 'f_score']
        for col in quality_cols:
            if col in df.columns and df[col].notna().any():
                df[f'{col}_score'] = rank_normalize(df[col])
                scores.append(f'{col}_score')

        # Financial health (higher = better)
        health_cols = ['current_ratio', 'quick_ratio', 'z_score']
        for col in health_cols:
            if col in df.columns and df[col].notna().any():
                df[f'{col}_score'] = rank_normalize(df[col])
                scores.append(f'{col}_score')

        # Debt (lower = better)
        if 'debt_ratio' in df.columns and df['debt_ratio'].notna().any():
            df['debt_score'] = 1 - rank_normalize(df['debt_ratio'])
            scores.append('debt_score')

        # Growth (higher = better)
        growth_cols = ['revenue_growth', 'earnings_growth']
        for col in growth_cols:
            if col in df.columns and df[col].notna().any():
                df[f'{col}_score'] = rank_normalize(df[col])
                scores.append(f'{col}_score')

        # Analyst (buy rating = lower number = better)
        if 'recommendation_mean' in df.columns and df['recommendation_mean'].notna().any():
            df['analyst_score'] = 1 - rank_normalize(df['recommendation_mean'])
            scores.append('analyst_score')

        # Calculate composite score
        if scores:
            df['composite_score'] = df[scores].mean(axis=1)
            df['composite_rank'] = df['composite_score'].rank(ascending=False)

        return df

    def get_top_stocks(self,
                      n: int = 20,
                      sort_by: str = 'composite_score',
                      ascending: bool = False) -> pd.DataFrame:
        """
        Get top N stocks from screening results

        Args:
            n: Number of stocks to return
            sort_by: Column to sort by
            ascending: Sort order

        Returns:
            Top N stocks
        """
        df = self.screen(return_scores=True)

        if df.empty:
            return df

        if sort_by in df.columns:
            df = df.sort_values(sort_by, ascending=ascending)

        return df.head(n)

    @classmethod
    def get_available_templates(cls) -> Dict[str, str]:
        """Get list of available screening templates"""
        return {name: template['description'] for name, template in cls.TEMPLATES.items()}

    @classmethod
    def get_available_fields(cls) -> Dict[str, List[str]]:
        """Get list of available screening fields by category"""
        return {
            'valuation': [
                'market_cap', 'enterprise_value', 'per', 'forward_per', 'pbr',
                'psr', 'peg_ratio', 'ev_to_ebitda', 'ev_to_revenue'
            ],
            'per_share': [
                'eps', 'forward_eps', 'bps', 'revenue_per_share'
            ],
            'profitability': [
                'roe', 'roa', 'gross_margin', 'operating_margin',
                'profit_margin', 'ebitda_margin'
            ],
            'growth': [
                'revenue_growth', 'earnings_growth', 'earnings_quarterly_growth'
            ],
            'financial_health': [
                'debt_ratio', 'current_ratio', 'quick_ratio', 'total_debt',
                'total_cash', 'interest_coverage', 'f_score', 'z_score', 'z_score_zone'
            ],
            'cash_flow': [
                'operating_cash_flow', 'free_cash_flow', 'fcf_yield', 'cf_to_debt'
            ],
            'dividend': [
                'dividend_yield', 'dividend_rate', 'payout_ratio',
                'five_year_avg_dividend_yield'
            ],
            'risk': [
                'beta', 'fifty_two_week_high', 'fifty_two_week_low',
                'price_to_52w_high', 'price_to_52w_low', 'price_52w_range_pct'
            ],
            'volume_liquidity': [
                'avg_volume', 'avg_volume_10d', 'shares_outstanding',
                'float_shares', 'shares_short', 'short_ratio', 'short_percent_of_float'
            ],
            'ownership': [
                'held_percent_insiders', 'held_percent_institutions'
            ],
            'analyst': [
                'target_high_price', 'target_low_price', 'target_mean_price',
                'recommendation_mean', 'recommendation_key',
                'number_of_analyst_opinions', 'upside_to_target'
            ],
            'company': [
                'sector', 'industry', 'full_time_employees'
            ]
        }


class ScreeningPresets:
    """Pre-built screening configurations for common use cases"""

    @staticmethod
    def warren_buffett_style() -> StockScreener:
        """Warren Buffett-style value investing criteria"""
        screener = StockScreener()
        screener.add_criterion('roe', FilterOperator.GREATER_THAN, 0.15, 'ROE > 15%')
        screener.add_criterion('debt_ratio', FilterOperator.LESS_THAN, 50, 'Low debt')
        screener.add_criterion('profit_margin', FilterOperator.GREATER_THAN, 0.10, 'High margins')
        screener.add_criterion('f_score', FilterOperator.GREATER_EQUAL, 6, 'Healthy finances')
        screener.add_criterion('per', FilterOperator.LESS_THAN, 20, 'Reasonable valuation')
        return screener

    @staticmethod
    def peter_lynch_garp() -> StockScreener:
        """Peter Lynch Growth at Reasonable Price (GARP) criteria"""
        screener = StockScreener()
        screener.add_criterion('peg_ratio', FilterOperator.LESS_THAN, 1.0, 'PEG < 1')
        screener.add_criterion('earnings_growth', FilterOperator.GREATER_THAN, 0.10, 'Earnings growth > 10%')
        screener.add_criterion('debt_ratio', FilterOperator.LESS_THAN, 100, 'Manageable debt')
        return screener

    @staticmethod
    def piotroski_high_score() -> StockScreener:
        """High Piotroski F-Score stocks"""
        screener = StockScreener()
        screener.add_criterion('f_score', FilterOperator.GREATER_EQUAL, 8, 'F-Score >= 8')
        screener.add_criterion('market_cap', FilterOperator.GREATER_THAN, 1e9, 'Market cap > $1B')
        return screener

    @staticmethod
    def dividend_aristocrat_style() -> StockScreener:
        """Dividend aristocrat-style criteria"""
        screener = StockScreener()
        screener.add_criterion('dividend_yield', FilterOperator.GREATER_THAN, 0.02, 'Yield > 2%')
        screener.add_criterion('payout_ratio', FilterOperator.LESS_THAN, 0.60, 'Sustainable payout')
        screener.add_criterion('debt_ratio', FilterOperator.LESS_THAN, 100, 'Low debt')
        screener.add_criterion('market_cap', FilterOperator.GREATER_THAN, 5e9, 'Large cap')
        return screener

    @staticmethod
    def momentum_breakout() -> StockScreener:
        """Momentum breakout criteria"""
        screener = StockScreener()
        screener.add_criterion('price_52w_range_pct', FilterOperator.GREATER_THAN, 0.8, 'Near 52-week high')
        screener.add_criterion('avg_volume', FilterOperator.GREATER_THAN, 500000, 'High liquidity')
        screener.add_criterion('revenue_growth', FilterOperator.GREATER_THAN, 0.10, 'Growing revenue')
        return screener

    @staticmethod
    def deep_value() -> StockScreener:
        """Deep value / contrarian criteria"""
        screener = StockScreener()
        screener.add_criterion('pbr', FilterOperator.LESS_THAN, 1.0, 'P/B < 1')
        screener.add_criterion('z_score', FilterOperator.GREATER_THAN, 1.81, 'Not in distress')
        screener.add_criterion('current_ratio', FilterOperator.GREATER_THAN, 1.5, 'Good liquidity')
        return screener


def main():
    """Example usage"""
    screener = StockScreener()

    # Example 1: Load pre-defined template
    print("=== Value Template ===")
    screener.load_template('value')
    for c in screener.criteria:
        print(f"  {c.field}: {c.operator.value} {c.value}")

    # Example 2: Custom screening
    print("\n=== Custom Screening ===")
    screener.clear_criteria()
    screener.add_criterion('per', 'lt', 15, 'P/E < 15')
    screener.add_criterion('roe', 'gt', 0.15, 'ROE > 15%')
    screener.add_criterion('market_cap', 'gt', 1e9, 'Market Cap > $1B')

    for c in screener.criteria:
        print(f"  {c.description}")

    # Example 3: Available templates
    print("\n=== Available Templates ===")
    for name, desc in StockScreener.get_available_templates().items():
        print(f"  {name}: {desc}")

    # Example 4: Available fields
    print("\n=== Available Fields (by category) ===")
    for category, fields in StockScreener.get_available_fields().items():
        print(f"  {category}: {', '.join(fields[:3])}...")


if __name__ == "__main__":
    main()
