#C:\DaDudeKC\Trade Analyzer\scripts\tests\test_robinhood_data.py

import unittest
from unittest.mock import patch, MagicMock
from scripts.robinhood_data import download_robinhood_data

class TestRobinhoodData(unittest.TestCase):

    @patch('scripts.robinhood_data.rh.orders.get_all_open_stock_orders')
    @patch('scripts.robinhood_data.rh.orders.get_all_stock_orders')
    @patch('scripts.robinhood_data.rh.stocks.get_instrument_by_url')
    @patch('scripts.robinhood_data.login_robinhood')
    def test_download_robinhood_data(self, mock_login, mock_get_instrument, mock_get_all_orders, mock_get_open_orders):
        # Mock login
        mock_login.return_value = None

        # Mock instrument data
        mock_get_instrument.return_value = {'symbol': 'AAPL'}

        # Mock no orders
        mock_get_open_orders.return_value = []
        mock_get_all_orders.return_value = []
        
        df = download_robinhood_data('user', 'pass')
        self.assertTrue(df.empty)

        # Mock only open orders
        mock_get_open_orders.return_value = [
            {
                'updated_at': '2024-01-02T00:00:00Z',
                'instrument': 'https://api.robinhood.com/instruments/def456/',
                'side': 'buy',
                'quantity': '10.0000',
                'price': '145.00',
                'executions': [],
                'state': 'queued'
            }
        ]
        mock_get_all_orders.return_value = []

        df = download_robinhood_data('user', 'pass')
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['symbol'], 'AAPL')

        # Mock past orders
        mock_get_open_orders.return_value = []
        mock_get_all_orders.return_value = [
            {
                'updated_at': '2024-01-02T00:00:00Z',
                'instrument': 'https://api.robinhood.com/instruments/def456/',
                'side': 'sell',
                'quantity': '5.0000',
                'executions': [{'price': '150.00'}],
                'state': 'filled'
            }
        ]

        df = download_robinhood_data('user', 'pass')
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['symbol'], 'AAPL')
        self.assertEqual(df.iloc[0]['price'], 150.00)
        
        # Mock both open and past orders
        mock_get_open_orders.return_value = [
            {
                'updated_at': '2024-01-02T00:00:00Z',
                'instrument': 'https://api.robinhood.com/instruments/def456/',
                'side': 'buy',
                'quantity': '10.0000',
                'price': '145.00',
                'executions': [],
                'state': 'queued'
            }
        ]
        mock_get_all_orders.return_value = [
            {
                'updated_at': '2024-01-02T00:00:00Z',
                'instrument': 'https://api.robinhood.com/instruments/def456/',
                'side': 'sell',
                'quantity': '5.0000',
                'executions': [{'price': '150.00'}],
                'state': 'filled'
            }
        ]

        df = download_robinhood_data('user', 'pass')
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['symbol'], 'AAPL')
        self.assertEqual(df.iloc[1]['symbol'], 'AAPL')
        self.assertEqual(df.iloc[0]['price'], 145.00)
        self.assertEqual(df.iloc[1]['price'], 150.00)

if __name__ == '__main__':
    unittest.main()
