import unittest
from scripts.sentiment_analysis import get_social_sentiment

class TestSentimentAnalysisRealData(unittest.TestCase):
    def test_get_social_sentiment_real_data(self):
        ticker = 'TSLA'  # Use a popular ticker for a higher chance of getting data
        result_df = get_social_sentiment(ticker)

        # Debug information
        print("Resulting DataFrame:")
        print(result_df)

        # Assertions
        self.assertGreaterEqual(len(result_df), 1)
        self.assertIn('timestamp', result_df.columns)
        self.assertIn('message', result_df.columns)
        self.assertIn('sentiment', result_df.columns)

if __name__ == '__main__':
    unittest.main()
