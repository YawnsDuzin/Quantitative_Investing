"""
Backtesting Engine
Simulates strategy performance on historical data
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm

from ..strategies.base_strategy import BaseStrategy
from ..utils.logger import get_logger
from ..utils.config_loader import get_config

logger = get_logger(__name__)


class Backtester:
    """
    Backtesting engine for trading strategies
    """

    def __init__(self,
                 strategy: BaseStrategy,
                 initial_capital: float = 100000000,
                 commission: float = 0.0015,
                 slippage: float = 0.001):
        """
        Initialize backtester

        Args:
            strategy: Trading strategy to backtest
            initial_capital: Initial capital (default 100M KRW or 100K USD)
            commission: Commission rate per trade (default 0.15%)
            slippage: Slippage rate (default 0.1%)
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        # Results
        self.portfolio_values = []
        self.positions_history = []
        self.trades = []
        self.daily_returns = []

        logger.info(f"Backtester initialized with {strategy.name} strategy")

    def run(self,
           data: pd.DataFrame,
           start_date: datetime = None,
           end_date: datetime = None,
           rebalance_frequency: str = 'monthly') -> pd.DataFrame:
        """
        Run backtest

        Args:
            data: DataFrame with stock data
            start_date: Backtest start date
            end_date: Backtest end date
            rebalance_frequency: Rebalancing frequency

        Returns:
            DataFrame with backtest results
        """
        logger.info(f"Starting backtest from {start_date} to {end_date}")

        # Filter data by date range
        if start_date:
            data = data[data['date'] >= start_date]
        if end_date:
            data = data[data['date'] <= end_date]

        # Get rebalancing dates
        rebalance_dates = self.strategy.get_rebalancing_dates(
            data['date'].min(),
            data['date'].max(),
            frequency=rebalance_frequency
        )

        # Get all trading dates
        all_dates = sorted(data['date'].unique())

        # Initialize portfolio
        current_capital = self.initial_capital
        current_positions = {}  # {symbol: shares}
        current_weights = {}  # {symbol: weight}

        # Track portfolio value over time
        portfolio_history = []

        for date in tqdm(all_dates, desc="Backtesting"):
            # Get data for current date
            current_data = data[data['date'] == date]

            # Check if it's a rebalancing date
            if date in rebalance_dates:
                logger.debug(f"Rebalancing on {date}")

                # Generate signals and select stocks
                signals = self.strategy.generate_signals(current_data)
                new_weights = self.strategy.rebalance_portfolio(
                    signals,
                    date,
                    current_weights
                )

                # Execute rebalancing trades
                current_positions, current_capital, trades = self._rebalance(
                    current_data,
                    current_positions,
                    new_weights,
                    current_capital,
                    date
                )

                current_weights = new_weights
                self.trades.extend(trades)

            # Calculate portfolio value
            portfolio_value = self._calculate_portfolio_value(
                current_data,
                current_positions,
                current_capital
            )

            # Record portfolio state
            portfolio_history.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'cash': current_capital,
                'n_positions': len(current_positions)
            })

        # Convert to DataFrame
        results_df = pd.DataFrame(portfolio_history)
        results_df = results_df.set_index('date')

        # Calculate returns
        results_df['returns'] = results_df['portfolio_value'].pct_change()
        results_df['cumulative_returns'] = (1 + results_df['returns']).cumprod() - 1

        self.portfolio_values = results_df

        logger.info(f"Backtest completed. Final portfolio value: {results_df['portfolio_value'].iloc[-1]:,.0f}")

        return results_df

    def _rebalance(self,
                  current_data: pd.DataFrame,
                  current_positions: Dict[str, int],
                  target_weights: Dict[str, float],
                  cash: float,
                  date: datetime) -> Tuple[Dict[str, int], float, List[Dict]]:
        """
        Execute rebalancing trades

        Args:
            current_data: Current market data
            current_positions: Current positions {symbol: shares}
            target_weights: Target portfolio weights {symbol: weight}
            cash: Available cash
            date: Current date

        Returns:
            Tuple of (new_positions, new_cash, trades)
        """
        trades = []
        new_positions = {}

        # Calculate total portfolio value
        portfolio_value = self._calculate_portfolio_value(
            current_data,
            current_positions,
            cash
        )

        # Get current prices
        prices = dict(zip(current_data['symbol'], current_data['close']))

        # Sell positions not in target
        for symbol in list(current_positions.keys()):
            if symbol not in target_weights or target_weights[symbol] == 0:
                # Sell entire position
                if symbol in prices:
                    shares = current_positions[symbol]
                    price = prices[symbol]
                    sell_value = shares * price * (1 - self.commission - self.slippage)
                    cash += sell_value

                    trades.append({
                        'date': date,
                        'symbol': symbol,
                        'action': 'SELL',
                        'shares': shares,
                        'price': price,
                        'value': sell_value
                    })

                    logger.debug(f"Sold {shares} shares of {symbol} at {price}")

        # Buy or adjust positions based on target weights
        for symbol, weight in target_weights.items():
            if symbol not in prices:
                logger.warning(f"No price data for {symbol} on {date}")
                continue

            target_value = portfolio_value * weight
            price = prices[symbol]

            # Apply slippage to buy price
            buy_price = price * (1 + self.slippage)

            # Calculate target shares
            target_shares = int(target_value / buy_price / (1 + self.commission))

            current_shares = current_positions.get(symbol, 0)

            if target_shares > current_shares:
                # Buy more shares
                shares_to_buy = target_shares - current_shares
                cost = shares_to_buy * buy_price * (1 + self.commission)

                if cost <= cash:
                    cash -= cost
                    new_positions[symbol] = target_shares

                    trades.append({
                        'date': date,
                        'symbol': symbol,
                        'action': 'BUY',
                        'shares': shares_to_buy,
                        'price': buy_price,
                        'value': cost
                    })

                    logger.debug(f"Bought {shares_to_buy} shares of {symbol} at {buy_price}")
                else:
                    logger.warning(f"Insufficient cash to buy {symbol}")
                    new_positions[symbol] = current_shares

            elif target_shares < current_shares:
                # Sell some shares
                shares_to_sell = current_shares - target_shares
                sell_price = price * (1 - self.slippage)
                proceeds = shares_to_sell * sell_price * (1 - self.commission)

                cash += proceeds
                new_positions[symbol] = target_shares

                trades.append({
                    'date': date,
                    'symbol': symbol,
                    'action': 'SELL',
                    'shares': shares_to_sell,
                    'price': sell_price,
                    'value': proceeds
                })

                logger.debug(f"Sold {shares_to_sell} shares of {symbol} at {sell_price}")

            else:
                # Keep current position
                new_positions[symbol] = current_shares

        return new_positions, cash, trades

    def _calculate_portfolio_value(self,
                                   current_data: pd.DataFrame,
                                   positions: Dict[str, int],
                                   cash: float) -> float:
        """
        Calculate total portfolio value

        Args:
            current_data: Current market data
            positions: Current positions {symbol: shares}
            cash: Cash balance

        Returns:
            Total portfolio value
        """
        stock_value = 0

        # Get current prices
        prices = dict(zip(current_data['symbol'], current_data['close']))

        # Calculate value of stock positions
        for symbol, shares in positions.items():
            if symbol in prices:
                stock_value += shares * prices[symbol]
            else:
                logger.warning(f"No price data for {symbol}")

        total_value = stock_value + cash

        return total_value

    def get_trades_df(self) -> pd.DataFrame:
        """
        Get trades as DataFrame

        Returns:
            DataFrame with all trades
        """
        if not self.trades:
            return pd.DataFrame()

        return pd.DataFrame(self.trades)

    def get_summary(self) -> Dict:
        """
        Get backtest summary statistics

        Returns:
            Dictionary with summary metrics
        """
        if self.portfolio_values.empty:
            return {}

        from .performance_metrics import PerformanceMetrics

        metrics = PerformanceMetrics(self.portfolio_values)

        summary = {
            'initial_capital': self.initial_capital,
            'final_value': self.portfolio_values['portfolio_value'].iloc[-1],
            'total_return': metrics.total_return(),
            'annual_return': metrics.annual_return(),
            'volatility': metrics.volatility(),
            'sharpe_ratio': metrics.sharpe_ratio(),
            'max_drawdown': metrics.max_drawdown(),
            'calmar_ratio': metrics.calmar_ratio(),
            'win_rate': metrics.win_rate(),
            'n_trades': len(self.trades)
        }

        return summary


def run_backtest(strategy: BaseStrategy,
                data: pd.DataFrame,
                start_date: datetime = None,
                end_date: datetime = None,
                initial_capital: float = 100000000,
                commission: float = 0.0015,
                slippage: float = 0.001,
                rebalance_frequency: str = 'monthly') -> Tuple[pd.DataFrame, Dict]:
    """
    Convenience function to run backtest

    Args:
        strategy: Trading strategy
        data: Stock data
        start_date: Start date
        end_date: End date
        initial_capital: Initial capital
        commission: Commission rate
        slippage: Slippage rate
        rebalance_frequency: Rebalancing frequency

    Returns:
        Tuple of (results DataFrame, summary dict)
    """
    backtester = Backtester(
        strategy=strategy,
        initial_capital=initial_capital,
        commission=commission,
        slippage=slippage
    )

    results = backtester.run(
        data=data,
        start_date=start_date,
        end_date=end_date,
        rebalance_frequency=rebalance_frequency
    )

    summary = backtester.get_summary()

    return results, summary


def main():
    """Example usage"""
    from ..strategies.quant_strategies import create_strategy

    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')

    stocks = ['STOCK_A', 'STOCK_B', 'STOCK_C', 'STOCK_D', 'STOCK_E']
    data_list = []

    for stock in stocks:
        df = pd.DataFrame({
            'date': dates,
            'symbol': stock,
            'close': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
            'volume': np.random.randint(1000000, 10000000, len(dates))
        })
        data_list.append(df)

    data = pd.concat(data_list, ignore_index=True)

    # Create strategy
    strategy = create_strategy('momentum')

    # Run backtest
    results, summary = run_backtest(
        strategy=strategy,
        data=data,
        initial_capital=100000000
    )

    print("Backtest Summary:")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
