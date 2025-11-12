"""
Feature Engineering Module
Calculates quantitative factors for stock analysis
"""
import pandas as pd
import numpy as np
from typing import Union, List

from ..utils.logger import get_logger
from ..utils.helpers import rank_normalize, winsorize

logger = get_logger(__name__)


class FactorCalculator:
    """
    Calculator for quantitative investment factors
    """

    @staticmethod
    def momentum_factor(prices: pd.Series,
                       period: int = 252,
                       skip_recent: int = 20) -> pd.Series:
        """
        Calculate momentum factor (past returns)

        Args:
            prices: Price series
            period: Lookback period (252 = 1 year)
            skip_recent: Skip recent days to avoid reversal (20 = 1 month)

        Returns:
            Momentum factor series
        """
        # Calculate return from (t-period) to (t-skip_recent)
        # This skips the most recent period to avoid short-term reversal
        past_price = prices.shift(skip_recent)
        old_price = prices.shift(period + skip_recent)

        momentum = (past_price / old_price) - 1

        return momentum

    @staticmethod
    def value_pbr_factor(pbr: pd.Series) -> pd.Series:
        """
        Calculate value factor based on PBR (Price-to-Book Ratio)
        Lower PBR = Higher value score

        Args:
            pbr: PBR series

        Returns:
            Value factor (inverse of PBR)
        """
        # Inverse: lower PBR = higher score
        return 1 / pbr.replace(0, np.nan)

    @staticmethod
    def value_per_factor(per: pd.Series) -> pd.Series:
        """
        Calculate value factor based on PER (Price-to-Earnings Ratio)
        Lower PER = Higher value score

        Args:
            per: PER series

        Returns:
            Value factor (inverse of PER)
        """
        # Inverse: lower PER = higher score
        # Filter out negative PERs
        per_positive = per.where(per > 0, np.nan)
        return 1 / per_positive

    @staticmethod
    def quality_roe_factor(roe: pd.Series) -> pd.Series:
        """
        Calculate quality factor based on ROE (Return on Equity)
        Higher ROE = Higher quality

        Args:
            roe: ROE series (as decimal, e.g., 0.15 for 15%)

        Returns:
            Quality factor
        """
        return roe

    @staticmethod
    def quality_debt_factor(debt_ratio: pd.Series) -> pd.Series:
        """
        Calculate quality factor based on debt ratio
        Lower debt = Higher quality

        Args:
            debt_ratio: Debt-to-equity ratio series

        Returns:
            Quality factor (inverse of debt ratio)
        """
        # Inverse: lower debt = higher score
        return 1 / (1 + debt_ratio)

    @staticmethod
    def size_factor(market_cap: pd.Series) -> pd.Series:
        """
        Calculate size factor
        Smaller companies often have higher returns (size premium)

        Args:
            market_cap: Market capitalization series

        Returns:
            Size factor (log of market cap, then inverted)
        """
        # Use log to normalize
        log_market_cap = np.log(market_cap)

        # Invert: smaller = higher score
        return -log_market_cap

    @staticmethod
    def volatility_factor(returns: pd.Series, period: int = 252) -> pd.Series:
        """
        Calculate volatility factor
        Lower volatility = Lower risk (preferred by some strategies)

        Args:
            returns: Return series
            period: Lookback period for volatility calculation

        Returns:
            Volatility factor (negative of rolling std)
        """
        volatility = returns.rolling(window=period).std()

        # Negative: lower volatility = higher score
        return -volatility

    @staticmethod
    def liquidity_factor(volume: pd.Series,
                        price: pd.Series,
                        period: int = 20) -> pd.Series:
        """
        Calculate liquidity factor (trading volume)
        Higher liquidity = easier to trade

        Args:
            volume: Volume series
            price: Price series
            period: Average period

        Returns:
            Liquidity factor (average dollar volume)
        """
        dollar_volume = volume * price
        avg_dollar_volume = dollar_volume.rolling(window=period).mean()

        return np.log(avg_dollar_volume)

    @staticmethod
    def trend_strength_factor(prices: pd.Series, period: int = 200) -> pd.Series:
        """
        Calculate trend strength factor
        Measures if stock is in uptrend

        Args:
            prices: Price series
            period: MA period for trend

        Returns:
            Trend strength (price / MA ratio)
        """
        ma = prices.rolling(window=period).mean()
        trend_strength = (prices / ma) - 1

        return trend_strength

    @staticmethod
    def combined_value_factor(pbr: pd.Series = None,
                             per: pd.Series = None,
                             weights: List[float] = None) -> pd.Series:
        """
        Calculate combined value factor from multiple metrics

        Args:
            pbr: PBR series
            per: PER series
            weights: Weights for each metric

        Returns:
            Combined value factor
        """
        factors = []

        if pbr is not None:
            factors.append(FactorCalculator.value_pbr_factor(pbr))

        if per is not None:
            factors.append(FactorCalculator.value_per_factor(per))

        if not factors:
            raise ValueError("At least one value metric required")

        # Default equal weights
        if weights is None:
            weights = [1.0 / len(factors)] * len(factors)

        # Combine with weights
        combined = pd.Series(0, index=factors[0].index)
        for factor, weight in zip(factors, weights):
            # Rank normalize each factor
            factor_ranked = rank_normalize(factor)
            combined += factor_ranked * weight

        return combined

    @staticmethod
    def combined_quality_factor(roe: pd.Series = None,
                               debt_ratio: pd.Series = None,
                               weights: List[float] = None) -> pd.Series:
        """
        Calculate combined quality factor

        Args:
            roe: ROE series
            debt_ratio: Debt ratio series
            weights: Weights for each metric

        Returns:
            Combined quality factor
        """
        factors = []

        if roe is not None:
            factors.append(FactorCalculator.quality_roe_factor(roe))

        if debt_ratio is not None:
            factors.append(FactorCalculator.quality_debt_factor(debt_ratio))

        if not factors:
            raise ValueError("At least one quality metric required")

        # Default equal weights
        if weights is None:
            weights = [1.0 / len(factors)] * len(factors)

        # Combine with weights
        combined = pd.Series(0, index=factors[0].index)
        for factor, weight in zip(factors, weights):
            factor_ranked = rank_normalize(factor)
            combined += factor_ranked * weight

        return combined


class CrossSectionalFactors:
    """
    Calculate factors across multiple stocks at each time point
    (cross-sectional analysis)
    """

    @staticmethod
    def calculate_cross_sectional_factors(df: pd.DataFrame,
                                         date_col: str = 'date',
                                         symbol_col: str = 'symbol',
                                         price_col: str = 'close') -> pd.DataFrame:
        """
        Calculate cross-sectional factors for a panel of stocks

        Args:
            df: DataFrame with multi-stock data
            date_col: Date column name
            symbol_col: Symbol column name
            price_col: Price column name

        Returns:
            DataFrame with added factor columns
        """
        df = df.copy()
        df = df.sort_values([symbol_col, date_col])

        # Group by symbol and calculate time-series factors
        for symbol in df[symbol_col].unique():
            symbol_mask = df[symbol_col] == symbol
            symbol_df = df[symbol_mask].copy()

            # Calculate momentum
            if price_col in symbol_df.columns:
                momentum = FactorCalculator.momentum_factor(
                    symbol_df[price_col],
                    period=252,
                    skip_recent=20
                )
                df.loc[symbol_mask, 'momentum_12m'] = momentum

            # Calculate 6-month momentum
            if price_col in symbol_df.columns:
                momentum_6m = FactorCalculator.momentum_factor(
                    symbol_df[price_col],
                    period=126,
                    skip_recent=20
                )
                df.loc[symbol_mask, 'momentum_6m'] = momentum_6m

        # Calculate cross-sectional ranks for each date
        for date in df[date_col].unique():
            date_mask = df[date_col] == date
            date_df = df[date_mask].copy()

            # Rank normalize factors at each date
            for col in ['momentum_12m', 'momentum_6m']:
                if col in date_df.columns:
                    ranked = rank_normalize(date_df[col])
                    df.loc[date_mask, f'{col}_rank'] = ranked

            # Add other cross-sectional factors if available
            if 'pbr' in date_df.columns:
                value_pbr = FactorCalculator.value_pbr_factor(date_df['pbr'])
                df.loc[date_mask, 'value_pbr'] = rank_normalize(value_pbr)

            if 'per' in date_df.columns:
                value_per = FactorCalculator.value_per_factor(date_df['per'])
                df.loc[date_mask, 'value_per'] = rank_normalize(value_per)

            if 'roe' in date_df.columns:
                quality_roe = rank_normalize(date_df['roe'])
                df.loc[date_mask, 'quality_roe'] = quality_roe

            if 'market_cap' in date_df.columns:
                size = FactorCalculator.size_factor(date_df['market_cap'])
                df.loc[date_mask, 'size_factor'] = rank_normalize(size)

        logger.info("Cross-sectional factors calculated")
        return df

    @staticmethod
    def create_composite_score(df: pd.DataFrame,
                              factor_columns: List[str],
                              weights: List[float] = None) -> pd.Series:
        """
        Create composite score from multiple factors

        Args:
            df: DataFrame with factor columns
            factor_columns: List of factor column names
            weights: Weights for each factor (default equal weights)

        Returns:
            Composite score series
        """
        if weights is None:
            weights = [1.0 / len(factor_columns)] * len(factor_columns)

        composite_score = pd.Series(0, index=df.index)

        for col, weight in zip(factor_columns, weights):
            if col in df.columns:
                # Rank normalize and winsorize
                factor = winsorize(df[col], lower_percentile=0.01, upper_percentile=0.99)
                factor_ranked = rank_normalize(factor)
                composite_score += factor_ranked * weight

        return composite_score


def add_all_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all available factors to dataframe

    Args:
        df: DataFrame with price and fundamental data

    Returns:
        DataFrame with added factor columns
    """
    df = df.copy()
    calc = FactorCalculator()

    try:
        # Price-based factors
        if 'close' in df.columns:
            df['momentum_12m'] = calc.momentum_factor(df['close'], 252, 20)
            df['momentum_6m'] = calc.momentum_factor(df['close'], 126, 20)
            df['momentum_3m'] = calc.momentum_factor(df['close'], 63, 20)

        # Value factors
        if 'pbr' in df.columns:
            df['value_pbr'] = calc.value_pbr_factor(df['pbr'])

        if 'per' in df.columns:
            df['value_per'] = calc.value_per_factor(df['per'])

        # Quality factors
        if 'roe' in df.columns:
            df['quality_roe'] = calc.quality_roe_factor(df['roe'])

        if 'debt_ratio' in df.columns:
            df['quality_debt'] = calc.quality_debt_factor(df['debt_ratio'])

        # Size factor
        if 'market_cap' in df.columns:
            df['size_factor'] = calc.size_factor(df['market_cap'])

        # Liquidity factor
        if 'volume' in df.columns and 'close' in df.columns:
            df['liquidity'] = calc.liquidity_factor(df['volume'], df['close'])

        logger.info("Added all factors")

    except Exception as e:
        logger.error(f"Error adding factors: {str(e)}")

    return df


def main():
    """Example usage"""
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', '2024-01-01', freq='D')

    df = pd.DataFrame({
        'date': dates,
        'symbol': 'TEST',
        'close': 100 + np.cumsum(np.random.randn(len(dates))),
        'pbr': 1.5 + np.random.randn(len(dates)) * 0.1,
        'per': 15 + np.random.randn(len(dates)) * 2,
        'roe': 0.15 + np.random.randn(len(dates)) * 0.02,
        'debt_ratio': 0.5 + np.random.randn(len(dates)) * 0.05,
        'market_cap': 1e12,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    })

    # Add factors
    df = add_all_factors(df)

    print(df[['date', 'close', 'momentum_12m', 'value_pbr', 'quality_roe']].tail(10))


if __name__ == "__main__":
    main()
