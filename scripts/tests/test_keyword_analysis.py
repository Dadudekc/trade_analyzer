#C:\DaDudeKC\Trade Analyzer\scripts\tests\test_keyword_analysis.py

import unittest
import pandas as pd
from scripts.keyword_analysis import clean_message, perform_keyword_analysis

class TestKeywordAnalysis(unittest.TestCase):

    def test_clean_message(self):
        message = 'Tesla stock price is going up! Check out https://example.com for more info.'
        cleaned = clean_message(message)
        expected = 'tesla stock price going check info'
        self.assertEqual(cleaned, expected)

    def test_perform_keyword_analysis(self):
        messages = [
            {'message': 'Tesla stock price is going up! Check out https://example.com for more info.'},
            {'message': 'I just bought $TSLA stocks. Excited about the future!'},
            {'message': 'Tesla #stocks are performing well. Visit www.example.com for details.'}
        ]
        perform_keyword_analysis(messages, 'test_common_keywords.csv')
        common_words_df = pd.read_csv('test_common_keywords.csv')
        expected_words = ['tesla', 'stock', 'price', 'going', 'check', 'info', 'bought', 'tsla', 'stocks', 'excited', 'future', 'performing', 'well', 'visit', 'details']
        self.assertTrue(all(word in expected_words for word in common_words_df['word'].tolist()))

if __name__ == '__main__':
    unittest.main()
