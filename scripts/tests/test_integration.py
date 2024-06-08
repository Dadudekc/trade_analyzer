# C:\DaDudeKC\Trade Analyzer\scripts\tests\test_integration.py

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from scripts.main import main, ensure_csv_files_exist

class TestIntegration(unittest.TestCase):
    
    @patch('scripts.main.get_stock_data')
    @patch('scripts.main.fetch_messages')
    @patch('scripts.main.fetch_social_sentiment')
    @patch('scripts.main.get_news_data')
    @patch('scripts.main.perform_sentiment_analysis')
    @patch('scripts.main.merge_data')
    @patch('scripts.main.train_and_evaluate_model')
    def test_main_workflow(self, mock_train_and_evaluate_model, mock_merge_data, mock_perform_sentiment_analysis, mock_get_news_data, mock_fetch_social_sentiment, mock_fetch_messages, mock_get_stock_data):
        mock_get_stock_data.return_value = pd.DataFrame({
            'Date': ['2023-01-01'],
            'Open': [150.0],
            'High': [155.0],
            'Low': [149.0],
            'Close': [152.0],
            'Volume': [1000000]
        })
        mock_fetch_messages.return_value = pd.DataFrame()
        mock_fetch_social_sentiment.return_value = pd.DataFrame()
        mock_get_news_data.return_value = pd.DataFrame()
        mock_perform_sentiment_analysis.return_value = pd.DataFrame()
        mock_merge_data.return_value = pd.DataFrame()
        mock_train_and_evaluate_model.return_value = (0.9, 150.0, '2023-01-01')
        
        with patch('builtins.input', side_effect=['2', 'username', 'password']):
            with patch('scripts.main.get_robinhood_credentials') as mock_get_robinhood_credentials:
                mock_get_robinhood_credentials.return_value = ('username', 'password')
                held_options_info = {
                    'symbol': ['TSLA $197.5 Call 5/24/2024'],
                    'quantity': [1],
                    'price': [0.28],
                    'gain_percentage': [7.69]
                }
                main(held_options_info=held_options_info, username='username', password='password')

if __name__ == '__main__':
    unittest.main()
