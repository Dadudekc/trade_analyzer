#C:\DaDudeKC\Trade Analyzer\scripts\tests\test_analysis.py

import unittest
import pandas as pd
from scripts.analysis import (
    load_config,
    calculate_overall_profit_loss,
    trade_analysis,
    generate_risk_management_report,
    calculate_performance_metrics,
    generate_performance_report
)
import json

class TestAnalysisFunctions(unittest.TestCase):
    
    def setUp(self):
        # Set up configuration for tests
        self.config = load_config()

        # Example data for testing
        self.data = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04'],
            'symbol': ['AAPL', 'AAPL', 'GOOG', 'GOOG'],
            'price': [150, 155, 2700, 2750],
            'quantity': [10, 5, 2, 1],
            'action': ['buy', 'sell', 'buy', 'sell']
        })
        self.expired_worthless = pd.DataFrame({
            'date': ['2023-01-05', '2023-01-06'],
            'symbol': ['AAPL', 'GOOG'],
            'total_loss': [200, 300]
        })
    
    def test_load_config(self):
        config = load_config()
        self.assertIn('thresholds', config)
        self.assertIn('recommendations', config)

    def test_calculate_overall_profit_loss(self):
        total_loss_expired_worthless = 500
        total_value_held_options = 1500
        result = calculate_overall_profit_loss(total_loss_expired_worthless, total_value_held_options)
        self.assertEqual(result, 1000)

    def test_trade_analysis(self):
        trade_summary, significant_trades, large_losses = trade_analysis(self.data, self.config)
        self.assertFalse(trade_summary.empty)
        self.assertEqual(significant_trades.iloc[0]['symbol'], 'AAPL')
        self.assertEqual(large_losses.iloc[0]['symbol'], 'AAPL')

    def test_generate_risk_management_report(self):
        total_loss_expired_worthless = self.expired_worthless['total_loss'].sum()
        total_value_held_options = self.data['price'].sum() * 10  # Placeholder for the actual calculation
        overall_profit_loss = calculate_overall_profit_loss(total_loss_expired_worthless, total_value_held_options)
        trade_summary, significant_trades, large_losses = trade_analysis(self.data, self.config)
        report = generate_risk_management_report(total_loss_expired_worthless, total_value_held_options, overall_profit_loss, trade_summary, significant_trades, large_losses, self.expired_worthless, self.config)
        self.assertIn("Risk Management Report", report)
        self.assertIn("Total Loss from Expired Worthless Options", report)
    
    def test_calculate_performance_metrics(self):
        total_profit_loss, win_rate, average_duration, best_trade, worst_trade, most_profitable_symbol, least_profitable_symbol, risk_reward_ratios = calculate_performance_metrics(self.data)
        self.assertIsInstance(total_profit_loss, float)
        self.assertIsInstance(win_rate, float)
        self.assertIsInstance(average_duration, float)
        self.assertIsInstance(best_trade, pd.Series)
        self.assertIsInstance(worst_trade, pd.Series)
        self.assertIsInstance(most_profitable_symbol, pd.Series)
        self.assertIsInstance(least_profitable_symbol, pd.Series)
        self.assertIsInstance(risk_reward_ratios, pd.DataFrame)
    
    def test_generate_performance_report(self):
        total_profit_loss, win_rate, average_duration, best_trade, worst_trade, most_profitable_symbol, least_profitable_symbol, risk_reward_ratios = calculate_performance_metrics(self.data)
        report = generate_performance_report(total_profit_loss, win_rate, average_duration, best_trade, worst_trade, most_profitable_symbol, least_profitable_symbol, risk_reward_ratios, self.config)
        self.assertIn("Performance Report", report)
        self.assertIn("Total Profit/Loss", report)

if __name__ == '__main__':
    unittest.main()
