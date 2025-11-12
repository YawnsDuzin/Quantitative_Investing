"""
Technical Indicators Module
Calculates various technical indicators for stock analysis
"""
import pandas as pd
import numpy as np
from typing import Union, Tuple

from ..utils.logger import get_logger

logger = get_logger(__name__)


class TechnicalIndicators:
    """
    Technical indicators calculator
    """

    @staticmethod
    def sma(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Simple Moving Average

        Args:
            prices: Price series
            period: Number of periods

        Returns:
            SMA series
        """
        return prices.rolling(window=period).mean()

    @staticmethod
    def ema(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Exponential Moving Average

        Args:
            prices: Price series
            period: Number of periods

        Returns:
            EMA series
        """
        return prices.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index

        Args:
            prices: Price series
            period: Number of periods

        Returns:
            RSI series (0-100)
        """
        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        # Calculate RS and RSI
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def macd(prices: pd.Series,
            fast_period: int = 12,
            slow_period: int = 26,
            signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence

        Args:
            prices: Price series
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        # Calculate MACD line
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow

        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(prices: pd.Series,
                       period: int = 20,
                       std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands

        Args:
            prices: Price series
            period: Number of periods
            std_dev: Number of standard deviations

        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        middle_band = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        return upper_band, middle_band, lower_band

    @staticmethod
    def atr(high: pd.Series,
           low: pd.Series,
           close: pd.Series,
           period: int = 14) -> pd.Series:
        """
        Average True Range

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Number of periods

        Returns:
            ATR series
        """
        # Calculate True Range
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Calculate ATR
        atr = true_range.rolling(window=period).mean()

        return atr

    @staticmethod
    def stochastic(high: pd.Series,
                  low: pd.Series,
                  close: pd.Series,
                  k_period: int = 14,
                  d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            k_period: %K period
            d_period: %D period

        Returns:
            Tuple of (%K, %D)
        """
        # Calculate %K
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k = 100 * (close - lowest_low) / (highest_high - lowest_low)

        # Calculate %D (SMA of %K)
        d = k.rolling(window=d_period).mean()

        return k, d

    @staticmethod
    def adx(high: pd.Series,
           low: pd.Series,
           close: pd.Series,
           period: int = 14) -> pd.Series:
        """
        Average Directional Index

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Number of periods

        Returns:
            ADX series
        """
        # Calculate +DM and -DM
        high_diff = high.diff()
        low_diff = -low.diff()

        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

        # Calculate True Range
        tr = TechnicalIndicators.atr(high, low, close, period=1)

        # Calculate smoothed +DI and -DI
        atr_value = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr_value)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr_value)

        # Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On-Balance Volume

        Args:
            close: Close price series
            volume: Volume series

        Returns:
            OBV series
        """
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv

    @staticmethod
    def vwap(high: pd.Series,
            low: pd.Series,
            close: pd.Series,
            volume: pd.Series) -> pd.Series:
        """
        Volume Weighted Average Price

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            volume: Volume series

        Returns:
            VWAP series
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap

    @staticmethod
    def momentum(prices: pd.Series, period: int = 12) -> pd.Series:
        """
        Momentum indicator

        Args:
            prices: Price series
            period: Number of periods

        Returns:
            Momentum series
        """
        return prices.diff(period)

    @staticmethod
    def roc(prices: pd.Series, period: int = 12) -> pd.Series:
        """
        Rate of Change

        Args:
            prices: Price series
            period: Number of periods

        Returns:
            ROC series (percentage)
        """
        return ((prices - prices.shift(period)) / prices.shift(period)) * 100

    @staticmethod
    def williams_r(high: pd.Series,
                   low: pd.Series,
                   close: pd.Series,
                   period: int = 14) -> pd.Series:
        """
        Williams %R

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Number of periods

        Returns:
            Williams %R series (-100 to 0)
        """
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        wr = -100 * (highest_high - close) / (highest_high - lowest_low)

        return wr

    @staticmethod
    def cci(high: pd.Series,
           low: pd.Series,
           close: pd.Series,
           period: int = 20,
           constant: float = 0.015) -> pd.Series:
        """
        Commodity Channel Index

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Number of periods
            constant: CCI constant (default 0.015)

        Returns:
            CCI series
        """
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )

        cci = (typical_price - sma_tp) / (constant * mad)

        return cci


def add_all_indicators(df: pd.DataFrame,
                      close_col: str = 'close',
                      high_col: str = 'high',
                      low_col: str = 'low',
                      volume_col: str = 'volume') -> pd.DataFrame:
    """
    Add all technical indicators to a dataframe

    Args:
        df: DataFrame with OHLCV data
        close_col: Name of close price column
        high_col: Name of high price column
        low_col: Name of low price column
        volume_col: Name of volume column

    Returns:
        DataFrame with added indicator columns
    """
    df = df.copy()
    ti = TechnicalIndicators()

    try:
        # Moving Averages
        df['sma_20'] = ti.sma(df[close_col], 20)
        df['sma_50'] = ti.sma(df[close_col], 50)
        df['sma_200'] = ti.sma(df[close_col], 200)
        df['ema_12'] = ti.ema(df[close_col], 12)
        df['ema_26'] = ti.ema(df[close_col], 26)

        # RSI
        df['rsi'] = ti.rsi(df[close_col], 14)

        # MACD
        macd, signal, hist = ti.macd(df[close_col])
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist

        # Bollinger Bands
        upper, middle, lower = ti.bollinger_bands(df[close_col])
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower

        # ATR
        df['atr'] = ti.atr(df[high_col], df[low_col], df[close_col])

        # Stochastic
        k, d = ti.stochastic(df[high_col], df[low_col], df[close_col])
        df['stoch_k'] = k
        df['stoch_d'] = d

        # Momentum
        df['momentum'] = ti.momentum(df[close_col], 12)
        df['roc'] = ti.roc(df[close_col], 12)

        # Volume indicators
        if volume_col in df.columns:
            df['obv'] = ti.obv(df[close_col], df[volume_col])
            df['vwap'] = ti.vwap(df[high_col], df[low_col], df[close_col], df[volume_col])

        logger.info("Added all technical indicators")

    except Exception as e:
        logger.error(f"Error adding indicators: {str(e)}")

    return df


def main():
    """Example usage"""
    # Create sample data
    dates = pd.date_range('2023-01-01', '2024-01-01', freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(len(dates))) * 2

    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    })

    # Add indicators
    df = add_all_indicators(df)

    print(df[['date', 'close', 'sma_20', 'rsi', 'macd']].tail(10))


if __name__ == "__main__":
    main()
