import unittest
import pandas as pd
import numpy as np
from src.strategies.quant_strategies import create_strategy

class TestStrategies(unittest.TestCase):
    def setUp(self):
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        np.random.seed(42)

        # Create data for multiple stocks
        stocks = ['A', 'B', 'C']
        data_list = []
        for stock in stocks:
            df = pd.DataFrame({
                'date': dates,
                'symbol': stock,
                'close': 100 + np.cumsum(np.random.randn(len(dates))),
                'pbr': np.random.uniform(0.5, 3.0, len(dates)),
                'roe': np.random.uniform(0.0, 0.3, len(dates))
            })
            data_list.append(df)

        self.data = pd.concat(data_list, ignore_index=True)

    def test_momentum_strategy(self):
        strategy = create_strategy('momentum')
        # Momentum strategy needs longer history, but let's test if it runs
        # We might need to adjust lookback_period for this small test data
        strategy.lookback_period = 10
        strategy.skip_recent = 1

        signals = strategy.generate_signals(self.data)
        self.assertIn('momentum_rank', signals.columns)

        selected = strategy.select_stocks(signals, top_n=1)
        self.assertEqual(len(selected), 1)

    def test_value_strategy(self):
        strategy = create_strategy('value')
        signals = strategy.generate_signals(self.data)
        self.assertIn('value_score', signals.columns)

        selected = strategy.select_stocks(signals, top_n=2)
        self.assertEqual(len(selected), 2)

    def test_quality_strategy(self):
        strategy = create_strategy('quality')
        signals = strategy.generate_signals(self.data)
        self.assertIn('quality_score', signals.columns)

        selected = strategy.select_stocks(signals, top_n=2)
        self.assertEqual(len(selected), 2)

if __name__ == '__main__':
    unittest.main()
