# C:\DaDudeKC\Trade Analyzer\scripts\tests\test_model_training.py

import unittest
import os
import pandas as pd
from datetime import datetime
from scripts.model_training import (
    load_best_r2_score, save_best_r2_score, save_best_model, next_weekday, 
    get_adjusted_date_range_for_small_intervals, train_and_evaluate_model
)

class TestModelTraining(unittest.TestCase):
    
    def setUp(self):
        # Setup test data and parameters
        self.best_r2_file = 'test_best_r2.txt'
        self.model_file = 'test_model.pkl'
        self.merged_data = pd.DataFrame({
            'Datetime': pd.date_range(start='2023-01-01', periods=100, freq='D'),
            'Open': pd.Series([x for x in range(100)]),
            'High': pd.Series([x + 1 for x in range(100)]),
            'Low': pd.Series([x - 1 for x in range(100)]),
            'Close': pd.Series([x for x in range(100)]),
            'Volume': pd.Series([x for x in range(100)]),
            'sentiment': pd.Series([0.5 for x in range(100)])
        })
        self.interval = '1d'
        self.predictions = {}
        self.errors = {}

    def tearDown(self):
        # Cleanup test files
        if os.path.exists(self.best_r2_file):
            os.remove(self.best_r2_file)
        if os.path.exists(self.model_file):
            os.remove(self.model_file)

    def test_load_best_r2_score(self):
        save_best_r2_score(self.best_r2_file, 0.85)
        self.assertEqual(load_best_r2_score(self.best_r2_file), 0.85)
    
    def test_save_best_r2_score(self):
        save_best_r2_score(self.best_r2_file, 0.85)
        self.assertTrue(os.path.exists(self.best_r2_file))
    
    def test_next_weekday(self):
        self.assertEqual(next_weekday(datetime(2023, 1, 6)), datetime(2023, 1, 9))  # Friday to Monday
    
    def test_get_adjusted_date_range_for_small_intervals(self):
        start_date, end_date = get_adjusted_date_range_for_small_intervals('1d', '2024-05-15')
        self.assertEqual(start_date, '2023-05-15')
        self.assertEqual(end_date, '2024-05-15')
    
    def test_train_and_evaluate_model(self):
        best_r2, predicted_price, prediction_date = train_and_evaluate_model(
            self.merged_data, self.interval, self.best_r2_file, self.predictions, self.errors
        )
        self.assertTrue(best_r2 >= 0)
        self.assertTrue(predicted_price >= 0)
        self.assertTrue(isinstance(prediction_date, datetime))

if __name__ == '__main__':
    unittest.main()
