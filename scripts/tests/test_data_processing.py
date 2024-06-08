# C:\DaDudeKC\Trade Analyzer\scripts\tests\test_data_processing.py

import unittest
import pandas as pd
from datetime import datetime
from scripts.data_processing import (perform_sentiment_analysis, save_messages_to_csv, load_trade_data, 
                                     identify_expired_options, calculate_held_options_value, filter_data_by_date, 
                                     get_adjusted_date_range_for_small_intervals)

class TestDataProcessing(unittest.TestCase):

    def setUp(self):
        # Setup a sample sentiment data DataFrame
        self.sentiment_data = pd.DataFrame({
            'message': [
                "I love trading Tesla stock!",
                "I'm worried about the market.",
                "Great news for tech stocks!",
                "The market is crashing!",
                "Stock prices are stable."
            ],
            'timestamp': pd.date_range(start='2023-01-01', periods=5, freq='T')
        })

        # Setup a sample trade data DataFrame
        self.trade_data = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=5, freq='D'),
            'symbol': ['AAPL', 'GOOG', 'TSLA', 'AAPL', 'TSLA'],
            'action': ['buy', 'sell', 'buy', 'sell', 'buy'],
            'quantity': [10, 5, 8, 3, 10],
            'price': [150, 120, 700, 155, 680]
        })

        # Setup a sample held options info DataFrame
        self.held_options_info = pd.DataFrame({
            'symbol': ['AAPL', 'GOOG', 'TSLA'],
            'quantity': [10, 5, 8],
            'price': [150, 120, 700],
            'gain_percentage': [10, -5, 20]
        })

    def test_perform_sentiment_analysis(self):
        result = perform_sentiment_analysis(self.sentiment_data.copy())
        self.assertIn('sentiment', result.columns)
        self.assertEqual(len(result), 5)

    def test_save_messages_to_csv(self):
        save_messages_to_csv(self.sentiment_data.to_dict('records'), filename='test_collected_messages.csv')
        loaded_data = pd.read_csv('test_collected_messages.csv')
        self.assertEqual(len(loaded_data), 5)

    def test_load_trade_data(self):
        self.trade_data.to_csv('test_trade_data.csv', index=False)
        data = load_trade_data('test_trade_data.csv')
        self.assertIsNotNone(data)
        self.assertEqual(len(data), 5)
        self.assertIn('date', data.columns)

    def test_identify_expired_options(self):
        expired_loss, expired_data = identify_expired_options(self.trade_data.copy())
        self.assertIsNotNone(expired_data)
        self.assertIn('total_loss', expired_data.columns)

    def test_calculate_held_options_value(self):
        total_value = calculate_held_options_value(self.held_options_info)
        self.assertGreater(total_value, 0)

    def test_filter_data_by_date(self):
        filtered_data = filter_data_by_date(self.trade_data.copy(), '2023-01-02', '2023-01-04')
        self.assertEqual(len(filtered_data), 3)

    def test_get_adjusted_date_range_for_small_intervals(self):
        start_date, end_date = get_adjusted_date_range_for_small_intervals('1m', '2023-01-01')
        self.assertEqual(start_date, '2022-12-31')
        self.assertEqual(end_date, '2023-01-01')

if __name__ == '__main__':
    unittest.main()
