# C:\DaDudeKC\Trade Analyzer\scripts\tests\test_sentiment_analysis.py

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime
import os
import json
from scripts.sentiment_analysis import (
    analyze_sentiment_vader,
    analyze_sentiment_textblob,
    perform_sentiment_analysis,
    load_messages_from_file,
    get_social_sentiment
)

class TestSentimentAnalysis(unittest.TestCase):
    def setUp(self):
        self.sample_messages = [
            {'timestamp': '2024-05-23 22:42:23', 'message': 'This is a great stock!'},
            {'timestamp': '2024-05-23 22:43:23', 'message': 'Not sure about the future of this stock.'},
            {'timestamp': '2024-05-23 22:44:23', 'message': 'I think this stock is overvalued.'},
            {'timestamp': None, 'message': 'No timestamp message.'},
            {'message': 'No timestamp and no content column.'},
        ]
        
        self.sample_dataframe = pd.DataFrame(self.sample_messages)
        self.sentiment_filename = 'test_sentiment_analysis.csv'
        self.trends_filename = 'test_daily_sentiment_trends.csv'

    def test_analyze_sentiment_textblob(self):
        result = analyze_sentiment_textblob(self.sample_messages)
        self.assertIn('textblob_sentiment', result.columns)
        self.assertEqual(len(result), len(self.sample_messages))

    def test_analyze_sentiment_vader(self):
        result = analyze_sentiment_vader(self.sample_dataframe)
        self.assertIn('vader_sentiment', result.columns)
        self.assertEqual(len(result), len(self.sample_messages))

    def test_perform_sentiment_analysis(self):
        perform_sentiment_analysis(self.sample_messages, self.sentiment_filename, self.trends_filename)
        
        self.assertTrue(os.path.exists(self.sentiment_filename))
        self.assertTrue(os.path.exists(self.trends_filename))

        sentiment_df = pd.read_csv(self.sentiment_filename)
        trends_df = pd.read_csv(self.trends_filename)

        self.assertIn('textblob_sentiment', sentiment_df.columns)
        self.assertIn('vader_sentiment', sentiment_df.columns)
        self.assertIn('date', trends_df.columns)
        self.assertIn('textblob_sentiment', trends_df.columns)
        self.assertIn('vader_sentiment', trends_df.columns)

        # Clean up
        os.remove(self.sentiment_filename)
        os.remove(self.trends_filename)

    def test_load_messages_from_file(self):
        test_file = 'test_messages.json'
        with open(test_file, 'w') as file:
            for message in self.sample_messages:
                json.dump(message, file)
                file.write("\n")
        
        messages = load_messages_from_file(test_file)
        self.assertEqual(len(messages), len(self.sample_messages))

        # Clean up
        os.remove(test_file)

if __name__ == '__main__':
    unittest.main()
