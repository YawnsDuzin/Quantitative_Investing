"""
Quantitative Trading Strategies
Implements popular quant strategies: Momentum, Value, Quality, Multi-Factor
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from .base_strategy import BaseStrategy
from ..utils.logger import get_logger
from ..utils.helpers import rank_normalize, winsorize

logger = get_logger(__name__)


class MomentumStrategy(BaseStrategy):
    """
    Momentum Strategy
    Buys stocks with highest past returns (winners continue to win)
    """

    def __init__(self, lookback_period: int = 252, skip_recent: int = 20, config: Dict = None):
        """
        Initialize momentum strategy

        Args:
            lookback_period: Lookback period in days (252 = 1 year)
            skip_recent: Skip recent days to avoid reversal (20 = 1 month)
            config: Strategy configuration
        """
        super().__init__(name="Momentum", config=config)
        self.lookback_period = lookback_period
        self.skip_recent = skip_recent

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate momentum signals"""
        signals = data.copy()

        # Calculate momentum for each stock
        signals['momentum_score'] = signals.groupby('symbol')['close'].transform(
            lambda x: (x.shift(self.skip_recent) / x.shift(self.lookback_period + self.skip_recent)) - 1
        )

        # Rank normalize across stocks for each date
        signals['momentum_rank'] = signals.groupby('date')['momentum_score'].transform(rank_normalize)

        return signals

    def select_stocks(self, data: pd.DataFrame, top_n: int = None) -> List[str]:
        """
        Select stocks with highest momentum

        Args:
            data: DataFrame with momentum scores
            top_n: Number of top stocks to select

        Returns:
            List of selected stock symbols
        """
        if top_n is None:
            top_n = self.config.get('max_positions', 20)

        # Ensure momentum_rank exists
        if 'momentum_rank' not in data.columns:
            data = self.generate_signals(data)

        # Remove stocks with missing momentum scores
        valid_data = data.dropna(subset=['momentum_rank'])

        # Sort by momentum rank and select top N
        top_stocks = valid_data.nlargest(top_n, 'momentum_rank')

        return top_stocks['symbol'].tolist()


class ValueStrategy(BaseStrategy):
    """
    Value Strategy
    Buys undervalued stocks (low P/B, low P/E)
    """

    def __init__(self, use_pbr: bool = True, use_per: bool = True, config: Dict = None):
        """
        Initialize value strategy

        Args:
            use_pbr: Use Price-to-Book ratio
            use_per: Use Price-to-Earnings ratio
            config: Strategy configuration
        """
        super().__init__(name="Value", config=config)
        self.use_pbr = use_pbr
        self.use_per = use_per

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate value signals"""
        signals = data.copy()
        value_scores = []

        # PBR-based value score (lower is better)
        if self.use_pbr and 'pbr' in signals.columns:
            signals['value_pbr_score'] = 1 / signals['pbr'].replace(0, np.nan)
            signals['value_pbr_rank'] = signals.groupby('date')['value_pbr_score'].transform(rank_normalize)
            value_scores.append('value_pbr_rank')

        # PER-based value score (lower is better, exclude negative PER)
        if self.use_per and 'per' in signals.columns:
            per_positive = signals['per'].where(signals['per'] > 0, np.nan)
            signals['value_per_score'] = 1 / per_positive
            signals['value_per_rank'] = signals.groupby('date')['value_per_score'].transform(rank_normalize)
            value_scores.append('value_per_rank')

        # Combined value score
        if value_scores:
            signals['value_score'] = signals[value_scores].mean(axis=1)
        else:
            logger.warning("No value metrics available")
            signals['value_score'] = 0

        return signals

    def select_stocks(self, data: pd.DataFrame, top_n: int = None) -> List[str]:
        """Select stocks with highest value scores"""
        if top_n is None:
            top_n = self.config.get('max_positions', 20)

        # Ensure value_score exists
        if 'value_score' not in data.columns:
            data = self.generate_signals(data)

        # Remove stocks with missing value scores
        valid_data = data.dropna(subset=['value_score'])

        # Sort by value score and select top N
        top_stocks = valid_data.nlargest(top_n, 'value_score')

        return top_stocks['symbol'].tolist()


class QualityStrategy(BaseStrategy):
    """
    Quality Strategy
    Buys high-quality stocks (high ROE, low debt)
    """

    def __init__(self, use_roe: bool = True, use_debt_ratio: bool = True, config: Dict = None):
        """
        Initialize quality strategy

        Args:
            use_roe: Use Return on Equity
            use_debt_ratio: Use debt-to-equity ratio
            config: Strategy configuration
        """
        super().__init__(name="Quality", config=config)
        self.use_roe = use_roe
        self.use_debt_ratio = use_debt_ratio

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate quality signals"""
        signals = data.copy()
        quality_scores = []

        # ROE-based quality score (higher is better)
        if self.use_roe and 'roe' in signals.columns:
            signals['quality_roe_rank'] = signals.groupby('date')['roe'].transform(rank_normalize)
            quality_scores.append('quality_roe_rank')

        # Debt ratio-based quality score (lower is better)
        if self.use_debt_ratio and 'debt_ratio' in signals.columns:
            signals['quality_debt_score'] = 1 / (1 + signals['debt_ratio'])
            signals['quality_debt_rank'] = signals.groupby('date')['quality_debt_score'].transform(rank_normalize)
            quality_scores.append('quality_debt_rank')

        # Combined quality score
        if quality_scores:
            signals['quality_score'] = signals[quality_scores].mean(axis=1)
        else:
            logger.warning("No quality metrics available")
            signals['quality_score'] = 0

        return signals

    def select_stocks(self, data: pd.DataFrame, top_n: int = None) -> List[str]:
        """Select stocks with highest quality scores"""
        if top_n is None:
            top_n = self.config.get('max_positions', 20)

        # Ensure quality_score exists
        if 'quality_score' not in data.columns:
            data = self.generate_signals(data)

        # Remove stocks with missing quality scores
        valid_data = data.dropna(subset=['quality_score'])

        # Sort by quality score and select top N
        top_stocks = valid_data.nlargest(top_n, 'quality_score')

        return top_stocks['symbol'].tolist()


class MultiFactorStrategy(BaseStrategy):
    """
    Multi-Factor Strategy
    Combines multiple factors (Momentum, Value, Quality, Size)
    """

    def __init__(self,
                 momentum_weight: float = 0.4,
                 value_weight: float = 0.3,
                 quality_weight: float = 0.2,
                 size_weight: float = 0.1,
                 config: Dict = None):
        """
        Initialize multi-factor strategy

        Args:
            momentum_weight: Weight for momentum factor
            value_weight: Weight for value factor
            quality_weight: Weight for quality factor
            size_weight: Weight for size factor
            config: Strategy configuration
        """
        super().__init__(name="MultiF actor", config=config)

        # Normalize weights to sum to 1.0
        total_weight = momentum_weight + value_weight + quality_weight + size_weight
        self.weights = {
            'momentum': momentum_weight / total_weight,
            'value': value_weight / total_weight,
            'quality': quality_weight / total_weight,
            'size': size_weight / total_weight
        }

        logger.info(f"Multi-factor weights: {self.weights}")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate multi-factor signals"""
        signals = data.copy()

        # Calculate individual factor scores
        factor_scores = []

        # 1. Momentum Factor
        if 'close' in signals.columns:
            signals['momentum_score'] = signals.groupby('symbol')['close'].transform(
                lambda x: (x.shift(20) / x.shift(272)) - 1  # 12-month momentum, skip 1 month
            )
            signals['momentum_rank'] = signals.groupby('date')['momentum_score'].transform(rank_normalize)
            factor_scores.append(('momentum_rank', self.weights['momentum']))

        # 2. Value Factor (PBR + PER)
        value_components = []

        if 'pbr' in signals.columns:
            signals['value_pbr_score'] = 1 / signals['pbr'].replace(0, np.nan)
            signals['value_pbr_rank'] = signals.groupby('date')['value_pbr_score'].transform(rank_normalize)
            value_components.append('value_pbr_rank')

        if 'per' in signals.columns:
            per_positive = signals['per'].where(signals['per'] > 0, np.nan)
            signals['value_per_score'] = 1 / per_positive
            signals['value_per_rank'] = signals.groupby('date')['value_per_score'].transform(rank_normalize)
            value_components.append('value_per_rank')

        if value_components:
            signals['value_rank'] = signals[value_components].mean(axis=1)
            factor_scores.append(('value_rank', self.weights['value']))

        # 3. Quality Factor (ROE + Debt Ratio)
        quality_components = []

        if 'roe' in signals.columns:
            signals['quality_roe_rank'] = signals.groupby('date')['roe'].transform(rank_normalize)
            quality_components.append('quality_roe_rank')

        if 'debt_ratio' in signals.columns:
            signals['quality_debt_score'] = 1 / (1 + signals['debt_ratio'])
            signals['quality_debt_rank'] = signals.groupby('date')['quality_debt_score'].transform(rank_normalize)
            quality_components.append('quality_debt_rank')

        if quality_components:
            signals['quality_rank'] = signals[quality_components].mean(axis=1)
            factor_scores.append(('quality_rank', self.weights['quality']))

        # 4. Size Factor (Market Cap - smaller is better)
        if 'market_cap' in signals.columns:
            signals['size_score'] = -np.log(signals['market_cap'])  # Negative log: smaller = higher score
            signals['size_rank'] = signals.groupby('date')['size_score'].transform(rank_normalize)
            factor_scores.append(('size_rank', self.weights['size']))

        # Combine all factor scores
        if factor_scores:
            signals['composite_score'] = 0
            for factor_col, weight in factor_scores:
                if factor_col in signals.columns:
                    signals['composite_score'] += signals[factor_col].fillna(0) * weight

            # Normalize composite score
            signals['composite_rank'] = signals.groupby('date')['composite_score'].transform(rank_normalize)
        else:
            logger.warning("No factors available for multi-factor strategy")
            signals['composite_score'] = 0
            signals['composite_rank'] = 0

        return signals

    def select_stocks(self, data: pd.DataFrame, top_n: int = None) -> List[str]:
        """Select stocks with highest composite scores"""
        if top_n is None:
            top_n = self.config.get('max_positions', 20)

        # Ensure composite_rank exists
        if 'composite_rank' not in data.columns:
            data = self.generate_signals(data)

        # Remove stocks with missing composite scores
        valid_data = data.dropna(subset=['composite_rank'])

        # Sort by composite rank and select top N
        top_stocks = valid_data.nlargest(top_n, 'composite_rank')

        logger.info(f"Selected {len(top_stocks)} stocks based on multi-factor analysis")

        return top_stocks['symbol'].tolist()


class SizeStrategy(BaseStrategy):
    """
    Size Strategy (Small-Cap Premium)
    Buys smaller companies (by market cap)
    """

    def __init__(self, config: Dict = None):
        """Initialize size strategy"""
        super().__init__(name="Size", config=config)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate size signals"""
        signals = data.copy()

        if 'market_cap' in signals.columns:
            # Smaller market cap = higher score
            signals['size_score'] = -np.log(signals['market_cap'])
            signals['size_rank'] = signals.groupby('date')['size_score'].transform(rank_normalize)
        else:
            logger.warning("Market cap data not available")
            signals['size_rank'] = 0

        return signals

    def select_stocks(self, data: pd.DataFrame, top_n: int = None) -> List[str]:
        """Select smallest stocks"""
        if top_n is None:
            top_n = self.config.get('max_positions', 20)

        # Ensure size_rank exists
        if 'size_rank' not in data.columns:
            data = self.generate_signals(data)

        # Remove stocks with missing size scores
        valid_data = data.dropna(subset=['size_rank'])

        # Sort by size rank and select top N (smallest companies)
        top_stocks = valid_data.nlargest(top_n, 'size_rank')

        return top_stocks['symbol'].tolist()


def create_strategy(strategy_name: str, config: Dict = None) -> BaseStrategy:
    """
    Factory function to create strategy instances

    Args:
        strategy_name: Name of strategy ('momentum', 'value', 'quality', 'multifactor', 'size')
        config: Strategy configuration

    Returns:
        Strategy instance
    """
    strategy_name = strategy_name.lower()

    if strategy_name == 'momentum':
        return MomentumStrategy(config=config)
    elif strategy_name == 'value':
        return ValueStrategy(config=config)
    elif strategy_name == 'quality':
        return QualityStrategy(config=config)
    elif strategy_name == 'multifactor' or strategy_name == 'multi_factor':
        return MultiFactorStrategy(config=config)
    elif strategy_name == 'size':
        return SizeStrategy(config=config)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")


def main():
    """Example usage"""
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', '2024-01-01', freq='D')

    stocks = ['STOCK_A', 'STOCK_B', 'STOCK_C', 'STOCK_D', 'STOCK_E']
    data_list = []

    for stock in stocks:
        df = pd.DataFrame({
            'date': dates,
            'symbol': stock,
            'close': 100 + np.cumsum(np.random.randn(len(dates))),
            'pbr': 1.5 + np.random.randn(len(dates)) * 0.1,
            'per': 15 + np.random.randn(len(dates)) * 2,
            'roe': 0.15 + np.random.randn(len(dates)) * 0.02,
            'debt_ratio': 0.5 + np.random.randn(len(dates)) * 0.05,
            'market_cap': np.random.uniform(1e11, 1e12)
        })
        data_list.append(df)

    data = pd.concat(data_list, ignore_index=True)

    # Test multi-factor strategy
    strategy = create_strategy('multifactor')

    # Generate signals
    signals = strategy.generate_signals(data)

    # Select stocks for a specific date
    test_date = dates[-1]
    selected = strategy.select_stocks(signals[signals['date'] == test_date], top_n=3)

    print(f"Selected stocks: {selected}")
    print(f"\nTop stocks with scores:")
    print(signals[signals['date'] == test_date][['symbol', 'composite_rank']].sort_values('composite_rank', ascending=False).head())


if __name__ == "__main__":
    main()
