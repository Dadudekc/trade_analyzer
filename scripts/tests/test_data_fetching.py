#C:\DaDudeKC\Trade Analyzer\scripts\test_data_fetching.py

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from library.data_fetching import (
    fetch_messages,
    fetch_trends_data,
    get_stock_data,
    get_news_data,
    fetch_social_sentiment,
    setup_driver
)
import pandas as pd

class TestDataFetching(unittest.TestCase):

    @patch('scripts.data_fetching.WebDriverWait')
    @patch('scripts.data_fetching.setup_driver')
    def test_fetch_messages(self, mock_setup_driver, mock_WebDriverWait):
        mock_driver = MagicMock()
        mock_button = MagicMock()
        mock_setup_driver.return_value = mock_driver
        mock_driver.find_elements.side_effect = [
            [MagicMock(text='Test message 1'), MagicMock(text='Test message 2')],
            [MagicMock(text='12:00 PM - Jan 1, 2023'), MagicMock(text='12:05 PM - Jan 1, 2023')]
        ]
        mock_WebDriverWait.return_value.until.return_value = mock_button
        mock_button.click.return_value = None

        messages = fetch_messages(mock_driver, max_messages=2, max_scrolls=2)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['message'], 'Test message 1')
        self.assertEqual(messages[1]['message'], 'Test message 2')

    @patch('scripts.data_fetching.TrendReq')
    def test_fetch_trends_data(self, mock_TrendReq):
        mock_pytrends = MagicMock()
        mock_TrendReq.return_value = mock_pytrends
        mock_pytrends.interest_over_time.return_value = pd.DataFrame({
            'date': [datetime(2023, 1, 1)],
            'trend': [100]
        })

        trends_data = fetch_trends_data(mock_pytrends, 'Test Keyword')
        self.assertFalse(trends_data.empty)
        self.assertEqual(trends_data.iloc[0]['trend'], 100)

    @patch('scripts.data_fetching.requests.get')
    def test_get_news_data(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = {
            'articles': [
                {'publishedAt': '2023-01-01T00:00:00Z', 'title': 'Test Headline', 'description': 'Test Content'}
            ]
        }

        news_data = get_news_data('TSLA')
        self.assertFalse(news_data.empty)
        self.assertEqual(news_data.iloc[0]['headline'], 'Test Headline')

    @patch('scripts.data_fetching.WebDriverWait')
    @patch('scripts.data_fetching.setup_driver')
    def test_fetch_social_sentiment(self, mock_setup_driver, mock_WebDriverWait):
        mock_driver = MagicMock()
        mock_button = MagicMock()
        mock_setup_driver.return_value = mock_driver

        # Setup side_effect to mock multiple calls to find_elements
        mock_driver.find_elements.side_effect = [
            [MagicMock(text='Positive message'), MagicMock(text='Negative message')],
            [MagicMock(text='12:00 PM - Jan 1, 2023'), MagicMock(text='12:05 PM - Jan 1, 2023')],
            [MagicMock(text='Positive message'), MagicMock(text='Negative message')],
            [MagicMock(text='12:00 PM - Jan 1, 2023'), MagicMock(text='12:05 PM - Jan 1, 2023')]
        ]
        mock_WebDriverWait.return_value.until.return_value = mock_button
        mock_button.click.return_value = None

        sentiment_data = fetch_social_sentiment('TSLA', max_scrolls=2)
        self.assertFalse(sentiment_data.empty)
        self.assertEqual(len(sentiment_data), 4)
        self.assertEqual(sentiment_data.iloc[0]['message'], 'Positive message')

    @patch('scripts.data_fetching.yf.download')
    def test_get_stock_data(self, mock_download):
        mock_download.return_value = pd.DataFrame({
            'Date': [datetime(2023, 1, 1)],
            'Open': [100],
            'High': [110],
            'Low': [90],
            'Close': [105],
            'Volume': [1000]
        })

        stock_data = get_stock_data('TSLA', '2023-01-01', '2023-01-02', '1d')
        self.assertFalse(stock_data.empty)
        self.assertEqual(stock_data.iloc[0]['Open'], 100)

if __name__ == '__main__':
    unittest.main()
