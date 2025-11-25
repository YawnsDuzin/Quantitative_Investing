import unittest
import pandas as pd
import numpy as np
from src.data_processing.indicators import TechnicalIndicators, add_all_indicators

class TestTechnicalIndicators(unittest.TestCase):
    def setUp(self):
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(len(dates)))

        self.df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'high': prices + 1,
            'low': prices - 1,
            'volume': np.random.randint(100, 1000, size=len(dates))
        })
        self.ti = TechnicalIndicators()

    def test_sma(self):
        sma = self.ti.sma(self.df['close'], period=20)
        self.assertEqual(len(sma), 100)
        self.assertTrue(np.isnan(sma[18]))  # First 19 values should be NaN
        self.assertFalse(np.isnan(sma[19])) # 20th value should be valid

    def test_rsi(self):
        rsi = self.ti.rsi(self.df['close'], period=14)
        self.assertEqual(len(rsi), 100)
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        self.assertTrue(((valid_rsi >= 0) & (valid_rsi <= 100)).all())

    def test_macd(self):
        macd, signal, hist = self.ti.macd(self.df['close'])
        self.assertEqual(len(macd), 100)
        self.assertEqual(len(signal), 100)
        self.assertEqual(len(hist), 100)

    def test_add_all_indicators(self):
        df_with_indicators = add_all_indicators(self.df)
        expected_columns = ['sma_20', 'rsi', 'macd', 'bb_upper', 'atr']
        for col in expected_columns:
            self.assertIn(col, df_with_indicators.columns)

if __name__ == '__main__':
    unittest.main()
