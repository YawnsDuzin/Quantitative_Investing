"""
Performance Metrics Module
Calculates various performance metrics for backtesting results
"""
import pandas as pd
import numpy as np
from typing import Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceMetrics:
    """
    Calculator for portfolio performance metrics
    """

    def __init__(self, portfolio_data, risk_free_rate: float = 0.03):
        """
        Initialize performance metrics calculator

        Args:
            portfolio_data: DataFrame with portfolio values and returns, OR Series of portfolio values
            risk_free_rate: Annual risk-free rate (default 3%)
        """
        self.risk_free_rate = risk_free_rate

        # Handle Series input (just portfolio values)
        if isinstance(portfolio_data, pd.Series):
            self.portfolio_df = pd.DataFrame({
                'portfolio_value': portfolio_data
            })
            self.portfolio_df['returns'] = self.portfolio_df['portfolio_value'].pct_change()
        else:
            self.portfolio_df = portfolio_data.copy()
            # Ensure returns column exists
            if 'returns' not in self.portfolio_df.columns:
                if 'portfolio_value' in self.portfolio_df.columns:
                    self.portfolio_df['returns'] = self.portfolio_df['portfolio_value'].pct_change()

    def total_return(self) -> float:
        """
        Calculate total return

        Returns:
            Total return as decimal (e.g., 0.5 for 50%)
        """
        if 'portfolio_value' not in self.portfolio_df.columns:
            return 0.0

        initial_value = self.portfolio_df['portfolio_value'].iloc[0]
        final_value = self.portfolio_df['portfolio_value'].iloc[-1]

        return (final_value / initial_value) - 1

    def annual_return(self) -> float:
        """
        Calculate annualized return (CAGR)

        Returns:
            Annualized return
        """
        total_ret = self.total_return()
        n_days = len(self.portfolio_df)
        n_years = n_days / 252  # Trading days per year

        if n_years > 0:
            annual_ret = (1 + total_ret) ** (1 / n_years) - 1
            return annual_ret
        else:
            return 0.0

    def volatility(self, annualized: bool = True) -> float:
        """
        Calculate volatility (standard deviation of returns)

        Args:
            annualized: Return annualized volatility

        Returns:
            Volatility
        """
        if 'returns' not in self.portfolio_df.columns:
            return 0.0

        vol = self.portfolio_df['returns'].std()

        if annualized:
            vol = vol * np.sqrt(252)

        return vol

    def sharpe_ratio(self, periods_per_year: int = 252) -> float:
        """
        Calculate Sharpe ratio

        Args:
            periods_per_year: Trading periods per year (252 for daily)

        Returns:
            Sharpe ratio
        """
        if 'returns' not in self.portfolio_df.columns:
            return 0.0

        returns = self.portfolio_df['returns'].dropna()

        if len(returns) == 0:
            return 0.0

        # Calculate excess returns
        daily_rf_rate = (1 + self.risk_free_rate) ** (1 / periods_per_year) - 1
        excess_returns = returns - daily_rf_rate

        # Calculate Sharpe ratio
        mean_excess = excess_returns.mean()
        std_excess = excess_returns.std()

        if std_excess > 0:
            sharpe = (mean_excess / std_excess) * np.sqrt(periods_per_year)
            return sharpe
        else:
            return 0.0

    def sortino_ratio(self, periods_per_year: int = 252) -> float:
        """
        Calculate Sortino ratio (only penalizes downside volatility)

        Args:
            periods_per_year: Trading periods per year

        Returns:
            Sortino ratio
        """
        if 'returns' not in self.portfolio_df.columns:
            return 0.0

        returns = self.portfolio_df['returns'].dropna()

        if len(returns) == 0:
            return 0.0

        # Calculate excess returns
        daily_rf_rate = (1 + self.risk_free_rate) ** (1 / periods_per_year) - 1
        excess_returns = returns - daily_rf_rate

        # Calculate downside deviation (only negative returns)
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = downside_returns.std()

        if downside_std > 0:
            sortino = (excess_returns.mean() / downside_std) * np.sqrt(periods_per_year)
            return sortino
        else:
            return 0.0

    def max_drawdown(self) -> float:
        """
        Calculate maximum drawdown

        Returns:
            Maximum drawdown as positive decimal
        """
        if 'portfolio_value' not in self.portfolio_df.columns:
            return 0.0

        portfolio_values = self.portfolio_df['portfolio_value']

        # Calculate running maximum
        running_max = portfolio_values.expanding().max()

        # Calculate drawdown
        drawdown = (portfolio_values - running_max) / running_max

        # Return maximum drawdown (as positive number)
        return abs(drawdown.min())

    def calmar_ratio(self) -> float:
        """
        Calculate Calmar ratio (annual return / max drawdown)

        Returns:
            Calmar ratio
        """
        annual_ret = self.annual_return()
        max_dd = self.max_drawdown()

        if max_dd > 0:
            return annual_ret / max_dd
        else:
            return 0.0

    def win_rate(self) -> float:
        """
        Calculate win rate (percentage of positive return periods)

        Returns:
            Win rate (0-1)
        """
        if 'returns' not in self.portfolio_df.columns:
            return 0.0

        returns = self.portfolio_df['returns'].dropna()

        if len(returns) == 0:
            return 0.0

        win_rate = (returns > 0).sum() / len(returns)

        return win_rate

    def profit_factor(self) -> float:
        """
        Calculate profit factor (gross profit / gross loss)

        Returns:
            Profit factor
        """
        if 'returns' not in self.portfolio_df.columns:
            return 0.0

        returns = self.portfolio_df['returns'].dropna()

        if len(returns) == 0:
            return 0.0

        gross_profit = returns[returns > 0].sum()
        gross_loss = abs(returns[returns < 0].sum())

        if gross_loss > 0:
            return gross_profit / gross_loss
        else:
            return 0.0

    def information_ratio(self, benchmark_returns: pd.Series) -> float:
        """
        Calculate information ratio (alpha / tracking error)

        Args:
            benchmark_returns: Benchmark return series

        Returns:
            Information ratio
        """
        if 'returns' not in self.portfolio_df.columns:
            return 0.0

        portfolio_returns = self.portfolio_df['returns'].dropna()

        # Align dates
        common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
        portfolio_returns = portfolio_returns.loc[common_dates]
        benchmark_returns = benchmark_returns.loc[common_dates]

        # Calculate active returns
        active_returns = portfolio_returns - benchmark_returns

        # Calculate tracking error
        tracking_error = active_returns.std() * np.sqrt(252)

        if tracking_error > 0:
            information_ratio = (active_returns.mean() * 252) / tracking_error
            return information_ratio
        else:
            return 0.0

    def value_at_risk(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR)

        Args:
            confidence_level: Confidence level (default 95%)

        Returns:
            VaR (positive number representing potential loss)
        """
        if 'returns' not in self.portfolio_df.columns:
            return 0.0

        returns = self.portfolio_df['returns'].dropna()

        if len(returns) == 0:
            return 0.0

        # Calculate VaR at given confidence level
        var = abs(returns.quantile(1 - confidence_level))

        return var

    def conditional_value_at_risk(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall

        Args:
            confidence_level: Confidence level (default 95%)

        Returns:
            CVaR (average loss beyond VaR)
        """
        if 'returns' not in self.portfolio_df.columns:
            return 0.0

        returns = self.portfolio_df['returns'].dropna()

        if len(returns) == 0:
            return 0.0

        # Get VaR threshold
        var_threshold = returns.quantile(1 - confidence_level)

        # Calculate average of returns below VaR
        cvar = abs(returns[returns <= var_threshold].mean())

        return cvar

    def monthly_returns(self) -> pd.Series:
        """
        Calculate monthly returns

        Returns:
            Series of monthly returns
        """
        if 'portfolio_value' not in self.portfolio_df.columns:
            return pd.Series()

        # Resample to monthly
        monthly = self.portfolio_df['portfolio_value'].resample('M').last()
        monthly_ret = monthly.pct_change()

        return monthly_ret

    def get_all_metrics(self) -> dict:
        """
        Calculate all performance metrics

        Returns:
            Dictionary with all metrics
        """
        metrics = {
            'Total Return': self.total_return(),
            'Annual Return': self.annual_return(),
            'Volatility': self.volatility(),
            'Sharpe Ratio': self.sharpe_ratio(),
            'Sortino Ratio': self.sortino_ratio(),
            'Max Drawdown': self.max_drawdown(),
            'Calmar Ratio': self.calmar_ratio(),
            'Win Rate': self.win_rate(),
            'Profit Factor': self.profit_factor(),
            'VaR (95%)': self.value_at_risk(0.95),
            'CVaR (95%)': self.conditional_value_at_risk(0.95)
        }

        return metrics

    def print_summary(self):
        """Print performance summary"""
        metrics = self.get_all_metrics()

        print("\n" + "="*50)
        print("PERFORMANCE SUMMARY")
        print("="*50)

        for metric_name, value in metrics.items():
            if 'Return' in metric_name or 'Drawdown' in metric_name or 'VaR' in metric_name or 'Rate' in metric_name:
                print(f"{metric_name:.<30} {value:>8.2%}")
            else:
                print(f"{metric_name:.<30} {value:>8.2f}")

        print("="*50 + "\n")


def compare_strategies(results_dict: dict, risk_free_rate: float = 0.03):
    """
    Compare multiple strategy results

    Args:
        results_dict: Dictionary of {strategy_name: results_df}
        risk_free_rate: Risk-free rate

    Returns:
        DataFrame with comparison metrics
    """
    comparison = []

    for strategy_name, results_df in results_dict.items():
        metrics = PerformanceMetrics(results_df, risk_free_rate)
        summary = metrics.get_all_metrics()
        summary['Strategy'] = strategy_name
        comparison.append(summary)

    comparison_df = pd.DataFrame(comparison)
    comparison_df = comparison_df.set_index('Strategy')

    return comparison_df


def main():
    """Example usage"""
    # Create sample portfolio data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')

    portfolio_value = 100000000
    returns = np.random.randn(len(dates)) * 0.01 + 0.0003  # Slight positive drift

    portfolio_values = [portfolio_value]
    for ret in returns[1:]:
        portfolio_value *= (1 + ret)
        portfolio_values.append(portfolio_value)

    df = pd.DataFrame({
        'date': dates,
        'portfolio_value': portfolio_values
    })
    df = df.set_index('date')
    df['returns'] = df['portfolio_value'].pct_change()

    # Calculate metrics
    metrics = PerformanceMetrics(df)
    metrics.print_summary()


if __name__ == "__main__":
    main()
