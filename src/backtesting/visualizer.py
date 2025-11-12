"""
Visualization Module
Visualizes backtesting results and performance metrics
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Optional, List

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (14, 8)


class BacktestVisualizer:
    """
    Visualizer for backtesting results
    """

    def __init__(self, results_df: pd.DataFrame):
        """
        Initialize visualizer

        Args:
            results_df: DataFrame with backtest results
        """
        self.results_df = results_df

    def plot_portfolio_value(self, benchmark: pd.Series = None, save_path: str = None):
        """
        Plot portfolio value over time

        Args:
            benchmark: Benchmark series for comparison
            save_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot portfolio value
        ax.plot(self.results_df.index, self.results_df['portfolio_value'],
                label='Strategy', linewidth=2, color='#2E86DE')

        # Plot benchmark if provided
        if benchmark is not None:
            ax.plot(benchmark.index, benchmark,
                   label='Benchmark', linewidth=2, color='#EE5A6F', alpha=0.7)

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Portfolio Value', fontsize=12)
        ax.set_title('Portfolio Value Over Time', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)

        # Format y-axis with commas
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved portfolio value plot to {save_path}")

        plt.show()

    def plot_cumulative_returns(self, benchmark_returns: pd.Series = None, save_path: str = None):
        """
        Plot cumulative returns

        Args:
            benchmark_returns: Benchmark return series
            save_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        # Calculate cumulative returns
        if 'cumulative_returns' not in self.results_df.columns:
            cum_returns = (1 + self.results_df['returns']).cumprod() - 1
        else:
            cum_returns = self.results_df['cumulative_returns']

        # Plot strategy cumulative returns
        ax.plot(cum_returns.index, cum_returns * 100,
                label='Strategy', linewidth=2, color='#2E86DE')

        # Plot benchmark if provided
        if benchmark_returns is not None:
            benchmark_cum = (1 + benchmark_returns).cumprod() - 1
            ax.plot(benchmark_cum.index, benchmark_cum * 100,
                   label='Benchmark', linewidth=2, color='#EE5A6F', alpha=0.7)

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cumulative Return (%)', fontsize=12)
        ax.set_title('Cumulative Returns', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.show()

    def plot_drawdown(self, save_path: str = None):
        """
        Plot drawdown over time

        Args:
            save_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        # Calculate drawdown
        portfolio_values = self.results_df['portfolio_value']
        running_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - running_max) / running_max * 100

        # Plot drawdown
        ax.fill_between(drawdown.index, drawdown, 0,
                        color='#EE5A6F', alpha=0.3, label='Drawdown')
        ax.plot(drawdown.index, drawdown,
                color='#EE5A6F', linewidth=1.5)

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Drawdown (%)', fontsize=12)
        ax.set_title('Drawdown Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11)

        # Add max drawdown annotation
        max_dd = drawdown.min()
        max_dd_date = drawdown.idxmin()
        ax.annotate(f'Max DD: {max_dd:.2f}%',
                   xy=(max_dd_date, max_dd),
                   xytext=(max_dd_date, max_dd - 5),
                   fontsize=10,
                   ha='center')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.show()

    def plot_monthly_returns_heatmap(self, save_path: str = None):
        """
        Plot monthly returns as heatmap

        Args:
            save_path: Path to save figure
        """
        # Calculate monthly returns
        monthly_returns = self.results_df['portfolio_value'].resample('M').last().pct_change() * 100

        # Create year-month pivot table
        monthly_returns.index = pd.to_datetime(monthly_returns.index)
        monthly_data = pd.DataFrame({
            'Year': monthly_returns.index.year,
            'Month': monthly_returns.index.month,
            'Return': monthly_returns.values
        })

        pivot = monthly_data.pivot(index='Year', columns='Month', values='Return')

        # Plot heatmap
        fig, ax = plt.subplots(figsize=(14, 8))

        sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=0,
                   cbar_kws={'label': 'Return (%)'}, ax=ax)

        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Year', fontsize=12)
        ax.set_title('Monthly Returns Heatmap (%)', fontsize=14, fontweight='bold')

        # Month labels
        month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.set_xticklabels(month_labels)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.show()

    def plot_return_distribution(self, save_path: str = None):
        """
        Plot return distribution

        Args:
            save_path: Path to save figure
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        returns = self.results_df['returns'].dropna() * 100

        # Histogram
        ax1.hist(returns, bins=50, color='#2E86DE', alpha=0.7, edgecolor='black')
        ax1.axvline(returns.mean(), color='red', linestyle='--',
                   label=f'Mean: {returns.mean():.2f}%', linewidth=2)
        ax1.set_xlabel('Daily Return (%)', fontsize=12)
        ax1.set_ylabel('Frequency', fontsize=12)
        ax1.set_title('Return Distribution', fontsize=13, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Q-Q plot
        from scipy import stats
        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title('Q-Q Plot', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.show()

    def plot_rolling_sharpe(self, window: int = 252, save_path: str = None):
        """
        Plot rolling Sharpe ratio

        Args:
            window: Rolling window size (default 252 trading days = 1 year)
            save_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        returns = self.results_df['returns'].dropna()

        # Calculate rolling Sharpe ratio
        rolling_sharpe = (returns.rolling(window).mean() / returns.rolling(window).std()) * np.sqrt(252)

        ax.plot(rolling_sharpe.index, rolling_sharpe,
                linewidth=2, color='#2E86DE')
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        ax.axhline(y=1, color='green', linestyle='--', alpha=0.3, label='Sharpe = 1')

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Rolling Sharpe Ratio', fontsize=12)
        ax.set_title(f'Rolling Sharpe Ratio ({window} days)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.show()

    def create_full_report(self, save_dir: str = None):
        """
        Create full visualization report

        Args:
            save_dir: Directory to save all plots
        """
        logger.info("Creating full visualization report...")

        # Portfolio value
        self.plot_portfolio_value(
            save_path=f"{save_dir}/portfolio_value.png" if save_dir else None
        )

        # Cumulative returns
        self.plot_cumulative_returns(
            save_path=f"{save_dir}/cumulative_returns.png" if save_dir else None
        )

        # Drawdown
        self.plot_drawdown(
            save_path=f"{save_dir}/drawdown.png" if save_dir else None
        )

        # Monthly returns heatmap
        self.plot_monthly_returns_heatmap(
            save_path=f"{save_dir}/monthly_returns.png" if save_dir else None
        )

        # Return distribution
        self.plot_return_distribution(
            save_path=f"{save_dir}/return_distribution.png" if save_dir else None
        )

        # Rolling Sharpe
        self.plot_rolling_sharpe(
            save_path=f"{save_dir}/rolling_sharpe.png" if save_dir else None
        )

        logger.info("Full report created!")


def compare_strategies_plot(results_dict: Dict[str, pd.DataFrame], save_path: str = None):
    """
    Compare multiple strategies in one plot

    Args:
        results_dict: Dictionary of {strategy_name: results_df}
        save_path: Path to save figure
    """
    fig, ax = plt.subplots(figsize=(14, 7))

    colors = ['#2E86DE', '#EE5A6F', '#10AC84', '#F79F1F', '#A55EEA']

    for i, (name, results_df) in enumerate(results_dict.items()):
        cum_returns = (1 + results_df['returns']).cumprod() - 1
        ax.plot(cum_returns.index, cum_returns * 100,
                label=name, linewidth=2, color=colors[i % len(colors)])

    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Cumulative Return (%)', fontsize=12)
    ax.set_title('Strategy Comparison', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()


def main():
    """Example usage"""
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')

    portfolio_value = 100000000
    returns = np.random.randn(len(dates)) * 0.01 + 0.0003

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

    # Create visualizer
    viz = BacktestVisualizer(df)

    # Plot portfolio value
    viz.plot_portfolio_value()

    # Plot cumulative returns
    viz.plot_cumulative_returns()


if __name__ == "__main__":
    main()
