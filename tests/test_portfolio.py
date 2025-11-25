import unittest
import pandas as pd
import numpy as np
from src.portfolio.portfolio_optimizer import PortfolioOptimizer

class TestPortfolioOptimizer(unittest.TestCase):
    def setUp(self):
        # Create sample price data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        np.random.seed(42)

        # 3 Assets:
        # A: Low risk, low return
        # B: High risk, high return
        # C: Negative correlation with A

        returns_a = np.random.normal(0.0005, 0.01, 100)
        returns_b = np.random.normal(0.001, 0.02, 100)
        returns_c = -returns_a * 0.5 + np.random.normal(0.0002, 0.01, 100)

        price_a = 100 * np.cumprod(1 + returns_a)
        price_b = 100 * np.cumprod(1 + returns_b)
        price_c = 100 * np.cumprod(1 + returns_c)

        self.prices = pd.DataFrame({
            'A': price_a,
            'B': price_b,
            'C': price_c
        }, index=dates)

        self.optimizer = PortfolioOptimizer(self.prices)

    def test_equal_weights(self):
        weights = self.optimizer.optimize_equal_weights()
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        for asset in ['A', 'B', 'C']:
            self.assertAlmostEqual(weights[asset], 1/3)

    def test_mean_variance_sharpe(self):
        weights = self.optimizer.optimize_mean_variance(objective='sharpe')
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(sum(weights.values()), 1.0)

        # Check if weights are non-negative (no short selling)
        for w in weights.values():
            self.assertGreaterEqual(w, 0.0)

    def test_mean_variance_min_volatility(self):
        weights = self.optimizer.optimize_mean_variance(objective='min_volatility')

        # Calculate volatility of this portfolio
        metrics = self.optimizer.get_portfolio_metrics(weights)
        min_vol = metrics['volatility']

        # Compare with equal weights portfolio
        eq_weights = self.optimizer.optimize_equal_weights()
        eq_metrics = self.optimizer.get_portfolio_metrics(eq_weights)

        # Min vol portfolio should have lower (or equal) volatility than equal weights
        self.assertLessEqual(min_vol, eq_metrics['volatility'])

    def test_get_portfolio_metrics(self):
        weights = {'A': 0.5, 'B': 0.5, 'C': 0.0}
        metrics = self.optimizer.get_portfolio_metrics(weights)

        expected_keys = ['expected_return', 'volatility', 'sharpe_ratio']
        for key in expected_keys:
            self.assertIn(key, metrics)
            self.assertIsInstance(metrics[key], float)

if __name__ == '__main__':
    unittest.main()
