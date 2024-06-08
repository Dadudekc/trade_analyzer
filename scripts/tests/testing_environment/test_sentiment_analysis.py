# test_sentiment_analysis.py
import unittest
import logging
from get_social_sentiment import get_social_sentiment

class TestSentimentAnalysisRealData(unittest.TestCase):
    
    def test_get_social_sentiment_real_data(self):
        result_df = get_social_sentiment()
        logging.info(f"Resulting DataFrame:\n{result_df}")
        self.assertGreaterEqual(len(result_df), 1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
