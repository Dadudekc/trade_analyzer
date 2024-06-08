# C:\DaDudeKC\Trade Analyzer\scripts\tests\test_main.py

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from scripts.data_processing import (
    perform_sentiment_analysis,
    save_messages_to_csv,
    load_trade_data,
    identify_expired_options,
    calculate_held_options_value,
    filter_data_by_date,
    get_adjusted_date_range_for_small_intervals
)
from scripts.main import fetch_data_with_retries, is_trade_data, calculate_overall_profit_loss
import os
import requests

class TestMainFunctions(unittest.TestCase):
    
    @patch('scripts.main.requests.get')
    def test_fetch_data_with_retries(self, mock_get):
        mock_get.side_effect = [requests.exceptions.RequestException("Error"), MagicMock(status_code=200, json=lambda: {"data": []})]
        
        result = fetch_data_with_retries(lambda: pd.DataFrame([{"data": 1}]), max_retries=2, wait_time=1)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

    def test_is_trade_data(self):
        valid_data = pd.DataFrame({
            'date': ['2023-01-01'],
            'symbol': ['AAPL'],
            'action': ['buy'],
            'quantity': [10],
            'price': [150.0]
        })
        invalid_data = pd.DataFrame({
            'timestamp': ['2023-01-01'],
            'message': ['Test message']
        })
        
        self.assertTrue(is_trade_data(valid_data))
        self.assertFalse(is_trade_data(invalid_data))
    
    def test_calculate_overall_profit_loss(self):
        result = calculate_overall_profit_loss(100, 500)
        self.assertEqual(result, 400)

    def test_perform_sentiment_analysis(self):
        data = pd.DataFrame({'message': ["I love this!", "I hate this!"]})
        result = perform_sentiment_analysis(data)
        self.assertIn('sentiment', result.columns)
        self.assertEqual(len(result), 2)

    def test_perform_sentiment_analysis_empty(self):
        data = pd.DataFrame({'message': []})
        result = perform_sentiment_analysis(data)
        self.assertIn('sentiment', result.columns)
        self.assertEqual(len(result), 0)

    def test_save_messages_to_csv(self):
        messages = [{'message': "Test message", 'timestamp': "2023-01-01"}]
        filename = 'test_messages.csv'
        save_messages_to_csv(messages, filename)
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    def test_save_messages_to_csv_empty(self):
        messages = []
        filename = 'test_messages_empty.csv'
        save_messages_to_csv(messages, filename)
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    def test_identify_expired_options_no_buy(self):
        data = pd.DataFrame({'symbol': [], 'action': [], 'quantity': [], 'price': []})
        total_loss, expired_worthless = identify_expired_options(data)
        self.assertEqual(total_loss, 0)
        self.assertEqual(len(expired_worthless), 0)

    def test_identify_expired_options_no_sell(self):
        data = pd.DataFrame({
            'symbol': ['AAPL'],
            'action': ['buy'],
            'quantity': [10],
            'price': [150.0]
        })
        total_loss, expired_worthless = identify_expired_options(data)
        self.assertEqual(total_loss, 1500.0)
        self.assertEqual(len(expired_worthless), 1)

    def test_identify_expired_options_mismatched_quantities(self):
        data = pd.DataFrame({
            'symbol': ['AAPL', 'AAPL'],
            'action': ['buy', 'sell'],
            'quantity': [10, 5],
            'price': [150.0, 155.0]
        })
        total_loss, expired_worthless = identify_expired_options(data)
        self.assertEqual(total_loss, 1500.0)
        self.assertEqual(len(expired_worthless), 1)

    def test_calculate_held_options_value_empty(self):
        held_options_info = {'symbol': [], 'quantity': [], 'price': [], 'gain_percentage': []}
        result = calculate_held_options_value(held_options_info)
        self.assertEqual(result, 0.0)

    def test_calculate_held_options_value_invalid_data(self):
        held_options_info = {'symbol': ['AAPL'], 'quantity': ['invalid'], 'price': [150.0], 'gain_percentage': [10]}
        result = calculate_held_options_value(held_options_info)
        self.assertEqual(result, 0.0)

    def test_get_adjusted_date_range_for_small_intervals(self):
        interval = '1m'
        end_date = '2024-05-15'
        start_date, end_date = get_adjusted_date_range_for_small_intervals(interval, end_date)
        self.assertEqual(start_date, '2024-05-14')
        self.assertEqual(end_date, '2024-05-15')

if __name__ == '__main__':
    unittest.main()
