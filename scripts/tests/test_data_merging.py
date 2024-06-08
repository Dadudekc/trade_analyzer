# C:\DaDudeKC\Trade Analyzer\scripts\tests\test_data_merging.py

import unittest
import pandas as pd
from scripts.data_merging import merge_data

class TestDataMerging(unittest.TestCase):

    def setUp(self):
        # Create sample stock data
        self.stock_data = pd.DataFrame({
            'Datetime': pd.date_range(start='2023-01-01', periods=5, freq='T'),
            'Open': [100, 101, 102, 103, 104],
            'High': [110, 111, 112, 113, 114],
            'Low': [90, 91, 92, 93, 94],
            'Close': [105, 106, 107, 108, 109],
            'Volume': [1000, 1100, 1200, 1300, 1400]
        })

        # Create sample sentiment data
        self.sentiment_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=5, freq='2T'),
            'sentiment': [0.1, 0.2, 0.3, 0.4, 0.5]
        })

    def test_merge_data(self):
        merged_data = merge_data(self.stock_data, self.sentiment_data)
        
        # Check that the merged data has the same number of rows as stock data
        self.assertEqual(len(merged_data), len(self.stock_data))

        # Check that the merged data contains columns from both stock data and sentiment data
        self.assertIn('sentiment', merged_data.columns)
        self.assertIn('Open', merged_data.columns)

        # Check that the sentiment values are aligned correctly
        expected_sentiment = [0.1, 0.1, 0.2, 0.2, 0.3]
        self.assertListEqual(merged_data['sentiment'].tolist(), expected_sentiment)

if __name__ == '__main__':
    unittest.main()
