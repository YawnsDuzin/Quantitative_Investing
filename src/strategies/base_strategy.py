"""
Base Strategy Class
Abstract base class for all trading strategies
"""
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.config_loader import get_config

logger = get_logger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies
    """

    def __init__(self, name: str = "BaseStrategy", config: Dict = None):
        """
        Initialize strategy

        Args:
            name: Strategy name
            config: Strategy configuration
        """
        self.name = name
        self.config = config or self._load_default_config()
        self.positions = pd.DataFrame()
        self.signals = pd.DataFrame()

        logger.info(f"Initialized strategy: {name}")

    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        config_loader = get_config()
        return config_loader.get_strategy_config()

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals

        Args:
            data: DataFrame with stock data and factors

        Returns:
            DataFrame with signals (1=buy, 0=hold, -1=sell)
        """
        pass

    @abstractmethod
    def select_stocks(self, data: pd.DataFrame, top_n: int = None) -> List[str]:
        """
        Select stocks to trade

        Args:
            data: DataFrame with stock data
            top_n: Number of stocks to select

        Returns:
            List of selected stock symbols
        """
        pass

    def calculate_weights(self,
                         selected_stocks: List[str],
                         data: pd.DataFrame = None,
                         method: str = 'equal') -> Dict[str, float]:
        """
        Calculate portfolio weights for selected stocks

        Args:
            selected_stocks: List of stock symbols
            data: DataFrame with stock data (needed for some weighting methods)
            method: Weighting method ('equal', 'market_cap', 'inverse_volatility')

        Returns:
            Dictionary of {symbol: weight}
        """
        n_stocks = len(selected_stocks)

        if n_stocks == 0:
            return {}

        if method == 'equal':
            # Equal weight
            weight = 1.0 / n_stocks
            return {symbol: weight for symbol in selected_stocks}

        elif method == 'market_cap' and data is not None:
            # Market cap weighted
            if 'market_cap' in data.columns:
                market_caps = data[data['symbol'].isin(selected_stocks)].groupby('symbol')['market_cap'].last()
                total_market_cap = market_caps.sum()
                return {symbol: market_caps[symbol] / total_market_cap for symbol in selected_stocks}

        elif method == 'inverse_volatility' and data is not None:
            # Inverse volatility weighted
            if 'returns' in data.columns:
                volatility = data[data['symbol'].isin(selected_stocks)].groupby('symbol')['returns'].std()
                inv_vol = 1 / volatility
                total_inv_vol = inv_vol.sum()
                return {symbol: inv_vol[symbol] / total_inv_vol for symbol in selected_stocks}

        # Default to equal weight if method not supported
        logger.warning(f"Weighting method '{method}' not supported, using equal weights")
        weight = 1.0 / n_stocks
        return {symbol: weight for symbol in selected_stocks}

    def rebalance_portfolio(self,
                           data: pd.DataFrame,
                           current_date: datetime,
                           current_positions: Dict[str, float] = None) -> Dict[str, float]:
        """
        Rebalance portfolio

        Args:
            data: DataFrame with stock data
            current_date: Current rebalancing date
            current_positions: Current positions {symbol: weight}

        Returns:
            New positions {symbol: weight}
        """
        # Get data for current date
        current_data = data[data['date'] == current_date]

        # Select stocks
        top_n = self.config.get('max_positions', 20)
        selected_stocks = self.select_stocks(current_data, top_n=top_n)

        # Calculate weights
        weighting_method = self.config.get('equal_weight', True)
        method = 'equal' if weighting_method else 'market_cap'
        new_positions = self.calculate_weights(selected_stocks, current_data, method=method)

        logger.info(f"Rebalanced portfolio on {current_date}: {len(new_positions)} positions")

        return new_positions

    def apply_position_limits(self,
                             positions: Dict[str, float],
                             max_position_size: float = None) -> Dict[str, float]:
        """
        Apply position size limits

        Args:
            positions: Position weights
            max_position_size: Maximum weight per position

        Returns:
            Adjusted positions
        """
        if max_position_size is None:
            max_position_size = self.config.get('max_position_size', 0.1)

        adjusted_positions = {}
        excess_weight = 0

        # First pass: cap positions and calculate excess
        for symbol, weight in positions.items():
            if weight > max_position_size:
                adjusted_positions[symbol] = max_position_size
                excess_weight += (weight - max_position_size)
            else:
                adjusted_positions[symbol] = weight

        # Second pass: redistribute excess weight
        if excess_weight > 0:
            eligible_positions = {k: v for k, v in adjusted_positions.items()
                                 if v < max_position_size}

            if eligible_positions:
                redistribution = excess_weight / len(eligible_positions)
                for symbol in eligible_positions:
                    adjusted_positions[symbol] = min(
                        adjusted_positions[symbol] + redistribution,
                        max_position_size
                    )

        # Normalize to sum to 1.0
        total_weight = sum(adjusted_positions.values())
        if total_weight > 0:
            adjusted_positions = {k: v / total_weight for k, v in adjusted_positions.items()}

        return adjusted_positions

    def get_rebalancing_dates(self,
                             start_date: datetime,
                             end_date: datetime,
                             frequency: str = 'monthly') -> List[datetime]:
        """
        Get list of rebalancing dates

        Args:
            start_date: Start date
            end_date: End date
            frequency: Rebalancing frequency ('daily', 'weekly', 'monthly', 'quarterly')

        Returns:
            List of rebalancing dates
        """
        if frequency == 'daily':
            dates = pd.date_range(start_date, end_date, freq='D')
        elif frequency == 'weekly':
            dates = pd.date_range(start_date, end_date, freq='W-FRI')
        elif frequency == 'monthly':
            dates = pd.date_range(start_date, end_date, freq='MS')  # Month start
        elif frequency == 'quarterly':
            dates = pd.date_range(start_date, end_date, freq='QS')
        else:
            logger.warning(f"Unknown frequency: {frequency}, using monthly")
            dates = pd.date_range(start_date, end_date, freq='MS')

        return dates.tolist()

    def filter_universe(self,
                       data: pd.DataFrame,
                       min_market_cap: float = None,
                       min_price: float = 5.0,
                       min_volume: float = None) -> pd.DataFrame:
        """
        Filter stock universe based on criteria

        Args:
            data: DataFrame with stock data
            min_market_cap: Minimum market cap
            min_price: Minimum price (to avoid penny stocks)
            min_volume: Minimum average volume

        Returns:
            Filtered DataFrame
        """
        filtered = data.copy()

        # Filter by price
        if 'close' in filtered.columns:
            filtered = filtered[filtered['close'] >= min_price]

        # Filter by market cap
        if min_market_cap and 'market_cap' in filtered.columns:
            filtered = filtered[filtered['market_cap'] >= min_market_cap]

        # Filter by volume
        if min_volume and 'volume' in filtered.columns:
            filtered = filtered[filtered['volume'] >= min_volume]

        # Remove stocks with missing critical data
        critical_cols = ['close', 'volume']
        for col in critical_cols:
            if col in filtered.columns:
                filtered = filtered.dropna(subset=[col])

        logger.info(f"Filtered universe: {len(filtered)} stocks remaining")

        return filtered

    def get_strategy_info(self) -> Dict:
        """
        Get strategy information

        Returns:
            Dictionary with strategy info
        """
        return {
            'name': self.name,
            'config': self.config,
            'description': self.__doc__
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
