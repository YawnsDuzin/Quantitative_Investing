"""
Portfolio Optimizer Module
Implements portfolio optimization techniques (Equal Weights, Mean-Variance)
"""
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from typing import Dict, Union, Tuple, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class PortfolioOptimizer:
    """
    Portfolio Optimization Class
    """

    def __init__(self, prices: pd.DataFrame, risk_free_rate: float = 0.02):
        """
        Initialize the optimizer

        Args:
            prices: DataFrame of historical prices (index: date, columns: assets)
            risk_free_rate: Annual risk-free rate (default 0.02)
        """
        self.prices = prices
        self.returns = prices.pct_change().dropna()
        self.risk_free_rate = risk_free_rate
        self.assets = prices.columns.tolist()
        self.n_assets = len(self.assets)

    def optimize_equal_weights(self) -> Dict[str, float]:
        """
        Calculate equal weights for the portfolio

        Returns:
            Dictionary of asset weights {symbol: weight}
        """
        weight = 1.0 / self.n_assets
        weights = {asset: weight for asset in self.assets}

        logger.info(f"Calculated equal weights: {weights}")
        return weights

    def optimize_mean_variance(self, objective: str = 'sharpe') -> Dict[str, float]:
        """
        Perform Mean-Variance Optimization

        Args:
            objective: Optimization objective ('sharpe', 'min_volatility', 'max_return')

        Returns:
            Dictionary of asset weights {symbol: weight}
        """
        # Annualized mean returns and covariance matrix
        mu = self.returns.mean() * 252
        cov = self.returns.cov() * 252

        # Constraints: sum of weights = 1
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

        # Bounds: weights between 0 and 1 (no short selling)
        bounds = tuple((0, 1) for _ in range(self.n_assets))

        # Initial guess: equal weights
        init_guess = np.array([1.0 / self.n_assets] * self.n_assets)

        # Objective functions
        def neg_sharpe_ratio(weights, mu, cov, rf):
            returns = np.sum(mu * weights)
            volatility = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
            sharpe = (returns - rf) / volatility
            return -sharpe

        def portfolio_volatility(weights, cov):
            return np.sqrt(np.dot(weights.T, np.dot(cov, weights)))

        def neg_portfolio_return(weights, mu):
            return -np.sum(mu * weights)

        if objective == 'sharpe':
            args = (mu, cov, self.risk_free_rate)
            result = minimize(neg_sharpe_ratio, init_guess, args=args,
                             method='SLSQP', bounds=bounds, constraints=constraints)
        elif objective == 'min_volatility':
            args = (cov,)
            result = minimize(portfolio_volatility, init_guess, args=args,
                             method='SLSQP', bounds=bounds, constraints=constraints)
        elif objective == 'max_return':
            args = (mu,)
            result = minimize(neg_portfolio_return, init_guess, args=args,
                             method='SLSQP', bounds=bounds, constraints=constraints)
        else:
            raise ValueError(f"Unknown objective: {objective}")

        if not result.success:
            logger.warning(f"Optimization failed: {result.message}")
            return self.optimize_equal_weights()

        optimized_weights = {asset: weight for asset, weight in zip(self.assets, result.x)}

        # Clean small weights (floating point errors)
        optimized_weights = {k: v if v > 1e-4 else 0.0 for k, v in optimized_weights.items()}

        # Renormalize
        total_weight = sum(optimized_weights.values())
        if total_weight > 0:
            optimized_weights = {k: v / total_weight for k, v in optimized_weights.items()}

        logger.info(f"Calculated mean-variance weights ({objective}): {optimized_weights}")
        return optimized_weights

    def get_portfolio_metrics(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate expected portfolio metrics based on weights

        Args:
            weights: Dictionary of asset weights

        Returns:
            Dictionary with keys: expected_return, volatility, sharpe_ratio
        """
        weights_array = np.array([weights.get(asset, 0) for asset in self.assets])

        mu = self.returns.mean() * 252
        cov = self.returns.cov() * 252

        expected_return = np.sum(mu * weights_array)
        volatility = np.sqrt(np.dot(weights_array.T, np.dot(cov, weights_array)))
        sharpe_ratio = (expected_return - self.risk_free_rate) / volatility if volatility > 0 else 0

        return {
            'expected_return': expected_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio
        }
