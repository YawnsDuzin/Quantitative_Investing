"""
Helper utilities for Quantitative Investing System
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Union, List, Tuple


def get_date_range(start_date: Union[str, datetime] = None,
                   end_date: Union[str, datetime] = None,
                   days: int = None) -> Tuple[datetime, datetime]:
    """
    Get date range for data collection

    Args:
        start_date: Start date (string or datetime)
        end_date: End date (string or datetime)
        days: Number of days to go back from end_date

    Returns:
        Tuple of (start_date, end_date) as datetime objects
    """
    if end_date is None:
        end_date = datetime.now()
    elif isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)

    if start_date is None:
        if days is not None:
            start_date = end_date - timedelta(days=days)
        else:
            start_date = end_date - timedelta(days=365 * 5)  # Default 5 years
    elif isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)

    return start_date, end_date


def calculate_returns(prices: pd.Series,
                     periods: int = 1,
                     method: str = 'simple') -> pd.Series:
    """
    Calculate returns from price series

    Args:
        prices: Price series
        periods: Number of periods for return calculation
        method: 'simple' or 'log' returns

    Returns:
        Returns series
    """
    if method == 'simple':
        returns = prices.pct_change(periods=periods)
    elif method == 'log':
        returns = np.log(prices / prices.shift(periods))
    else:
        raise ValueError(f"Unknown method: {method}")

    return returns


def resample_ohlcv(df: pd.DataFrame,
                   freq: str = 'W',
                   price_col: str = 'Close') -> pd.DataFrame:
    """
    Resample OHLCV data to different frequency

    Args:
        df: DataFrame with OHLCV columns and datetime index
        freq: Resampling frequency ('D', 'W', 'M', etc.)
        price_col: Name of the price column to use for Close

    Returns:
        Resampled DataFrame
    """
    resampled = pd.DataFrame()

    # Resample OHLCV
    if 'Open' in df.columns:
        resampled['Open'] = df['Open'].resample(freq).first()
    if 'High' in df.columns:
        resampled['High'] = df['High'].resample(freq).max()
    if 'Low' in df.columns:
        resampled['Low'] = df['Low'].resample(freq).min()
    if price_col in df.columns:
        resampled['Close'] = df[price_col].resample(freq).last()
    if 'Volume' in df.columns:
        resampled['Volume'] = df['Volume'].resample(freq).sum()

    # Resample other columns (use last value)
    for col in df.columns:
        if col not in ['Open', 'High', 'Low', 'Close', 'Volume']:
            resampled[col] = df[col].resample(freq).last()

    return resampled.dropna()


def remove_outliers(df: pd.DataFrame,
                   columns: List[str],
                   method: str = 'iqr',
                   threshold: float = 3.0) -> pd.DataFrame:
    """
    Remove outliers from dataframe

    Args:
        df: Input dataframe
        columns: Columns to check for outliers
        method: 'iqr' (Interquartile Range) or 'zscore'
        threshold: Threshold for outlier detection (3.0 for zscore, 1.5 for IQR)

    Returns:
        DataFrame with outliers removed
    """
    df_clean = df.copy()

    for col in columns:
        if col not in df_clean.columns:
            continue

        if method == 'iqr':
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            df_clean = df_clean[
                (df_clean[col] >= lower_bound) &
                (df_clean[col] <= upper_bound)
            ]

        elif method == 'zscore':
            mean = df_clean[col].mean()
            std = df_clean[col].std()
            df_clean = df_clean[
                np.abs((df_clean[col] - mean) / std) <= threshold
            ]

    return df_clean


def winsorize(series: pd.Series,
             lower_percentile: float = 0.01,
             upper_percentile: float = 0.99) -> pd.Series:
    """
    Winsorize series by capping extreme values

    Args:
        series: Input series
        lower_percentile: Lower percentile to cap (e.g., 0.01 for 1%)
        upper_percentile: Upper percentile to cap (e.g., 0.99 for 99%)

    Returns:
        Winsorized series
    """
    lower_bound = series.quantile(lower_percentile)
    upper_bound = series.quantile(upper_percentile)

    return series.clip(lower=lower_bound, upper=upper_bound)


def normalize(df: pd.DataFrame,
             columns: List[str],
             method: str = 'minmax') -> pd.DataFrame:
    """
    Normalize dataframe columns

    Args:
        df: Input dataframe
        columns: Columns to normalize
        method: 'minmax' (0-1 scaling) or 'zscore' (standardization)

    Returns:
        DataFrame with normalized columns
    """
    df_norm = df.copy()

    for col in columns:
        if col not in df_norm.columns:
            continue

        if method == 'minmax':
            min_val = df_norm[col].min()
            max_val = df_norm[col].max()
            if max_val > min_val:
                df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)

        elif method == 'zscore':
            mean = df_norm[col].mean()
            std = df_norm[col].std()
            if std > 0:
                df_norm[col] = (df_norm[col] - mean) / std

    return df_norm


def rank_normalize(series: pd.Series) -> pd.Series:
    """
    Rank normalize series (convert to percentile ranks)

    Args:
        series: Input series

    Returns:
        Rank normalized series (0-1)
    """
    return series.rank(pct=True)


def format_number(value: float, decimal_places: int = 2) -> str:
    """
    Format number with thousand separators

    Args:
        value: Number to format
        decimal_places: Number of decimal places

    Returns:
        Formatted string
    """
    return f"{value:,.{decimal_places}f}"


def calculate_period_return(start_value: float,
                           end_value: float,
                           periods: int = 1) -> float:
    """
    Calculate period return

    Args:
        start_value: Starting value
        end_value: Ending value
        periods: Number of periods

    Returns:
        Annualized return
    """
    if start_value <= 0:
        return 0.0

    total_return = (end_value / start_value) - 1

    if periods > 1:
        annualized_return = (1 + total_return) ** (1 / periods) - 1
        return annualized_return

    return total_return
