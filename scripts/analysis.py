#C:\DaDudeKC\Trade Analyzer\scripts\analysis.py

import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration from a file
def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logging.info(f"Configuration loaded from {config_file}.")
        return config
    except Exception as e:
        logging.warning(f"Configuration file {config_file} not found. Using default configuration.")
        return {
            "thresholds": {
                "significant_trade": {"value": 1000, "description": "Significant trades are those that meet or exceed this value."},
                "large_loss": {"value": 500, "description": "Large losses are those that meet or exceed this value."},
                "high_win_rate": {"value": 0.75, "description": "High win rate is one that meets or exceeds this value."},
                "long_trade_duration": {"value": 48, "description": "Long trade durations are those that meet or exceed this value."}
            },
            "recommendations": {
                "replicate_successful_strategies": {"action": "Analyze successful trades and replicate strategies.", "description": "Analyze and document successful strategies to replicate them."},
                "learn_from_mistakes": {"action": "Review and learn from mistakes.", "description": "Analyze loss-making trades to avoid repeating mistakes."},
                "focus_profitable_symbols": {"action": "Focus on profitable symbols.", "description": "Allocate more resources to trading symbols that have yielded profits."},
                "review_unprofitable_symbols": {"action": "Review and refine strategies for unprofitable symbols.", "description": "Analyze unprofitable symbols to refine strategies or reduce exposure."},
                "diversified_strategy": {"action": "Maintain a diversified strategy.", "description": "Diversify across symbols, sectors, and strategies to spread risk."},
                "continuous_improvement": {"action": "Continuously improve strategies.", "description": "Stay informed and regularly review performance to improve strategies."}
            }
        }

# Calculate overall profit/loss
def calculate_overall_profit_loss(total_loss_expired_worthless, total_value_held_options):
    overall_profit_loss = total_value_held_options - total_loss_expired_worthless
    logging.info(f"Overall profit/loss calculated: {overall_profit_loss}")
    return overall_profit_loss

# Perform trade analysis
def trade_analysis(data, config):
    # Ensure 'date' column exists
    if 'date' not in data.columns:
        logging.error("'date' column is missing in the dataframe.")
        raise KeyError("'date' column is missing in the dataframe.")
        
    data['total_cost'] = data['price'] * data['quantity']
    summary = data.groupby('symbol').agg({
        'date': ['min', 'max'],
        'quantity': 'sum',
        'total_cost': 'sum',
        'price': 'mean'
    }).reset_index()
    
    # Flatten the MultiIndex columns
    summary.columns = ['symbol', 'start_date', 'end_date', 'total_quantity', 'total_cost', 'average_price']
    logging.info("Trade analysis summary generated.")
    
    significant_trades = summary[summary['total_cost'] >= config['thresholds']['significant_trade']['value']]
    large_losses = summary[summary['total_cost'] >= config['thresholds']['large_loss']['value']]
    
    return summary, significant_trades, large_losses

# Generate risk management report
def generate_risk_management_report(total_loss_expired_worthless, total_value_held_options, overall_profit_loss, trade_summary, significant_trades, large_losses, expired_worthless, config):
    try:
        most_traded_symbol = trade_summary.loc[trade_summary['total_quantity'].idxmax()]['symbol']
        largest_loss_trade = expired_worthless.loc[expired_worthless['total_loss'].idxmax()]
    except Exception as e:
        logging.error(f"Error in generating risk management report: {e}")
        raise
    
    report = f"""
    Risk Management Report
    ======================
    Total Loss from Expired Worthless Options: ${total_loss_expired_worthless:.2f}
    Total Value of Held Options: ${total_value_held_options:.2f}
    Overall Profit/Loss: ${overall_profit_loss:.2f}

    Detailed Expired Options:
    -------------------------
    {expired_worthless.to_string(index=False)}

    Trade Summary:
    --------------
    {trade_summary.to_string(index=False)}

    Key Insights:
    -------------
    1. Most Traded Symbol: {most_traded_symbol}
    2. Largest Loss Trade: {largest_loss_trade['symbol']} on {largest_loss_trade['date']} with a loss of ${largest_loss_trade['total_loss']:.2f}
    3. Significant Trades (>= ${config['thresholds']['significant_trade']['value']}):
    {significant_trades.to_string(index=False)}

    4. Large Losses (>= ${config['thresholds']['large_loss']['value']}):
    {large_losses.to_string(index=False)}

    Recommendations:
    ----------------
    1. **Regular Monitoring and Adjustment:** Monitor your {most_traded_symbol} positions regularly and adjust them before expiration.
    2. **Stop-Loss Orders:** Implement stop-loss orders to prevent large losses like the one on {largest_loss_trade['date']}.
    3. **Diversifying Trades:** Spread risk across multiple trades to avoid concentration on symbols like {most_traded_symbol}.
    4. **Maintaining a Trading Journal:** Document all trades to identify patterns and improve strategies.
    5. **Performance Review:** Regularly review your trading performance to identify strengths and weaknesses.
    6. **Continuous Education:** Stay updated with market trends and strategies to improve your trading skills.
    7. **Analyze Significant Trades:** Pay close attention to trades that are significantly large and analyze their success/failure rates.
    8. **Review Large Losses:** Understand the reasons behind large losses and adjust your strategy to minimize such occurrences in the future.
    """
    
    logging.info("Risk management report generated.")
    return report

# Calculate performance metrics
def calculate_performance_metrics(data):
    try:
        # Calculate total profit/loss
        data['total_cost'] = data['price'] * data['quantity']
        data['profit_loss'] = np.where(data['action'] == 'buy', -data['total_cost'], data['total_cost'])
        total_profit_loss = float(data['profit_loss'].sum())
        logging.info(f"Total profit/loss calculated: {total_profit_loss}")
        
        # Calculate win rate
        wins = data[data['profit_loss'] > 0].shape[0]
        total_trades = data.shape[0]
        win_rate = wins / total_trades if total_trades > 0 else 0
        logging.info(f"Win rate calculated: {win_rate}")
        
        # Calculate average trade duration
        data['date'] = pd.to_datetime(data['date'])
        data.sort_values(by='date', inplace=True)
        data['duration'] = data['date'].diff().dt.total_seconds().div(3600)
        average_duration = data['duration'].mean()
        logging.info(f"Average trade duration calculated: {average_duration}")
        
        # Identify the best and worst trades
        best_trade = data.loc[data['profit_loss'].idxmax()]
        worst_trade = data.loc[data['profit_loss'].idxmin()]
        
        # Calculate additional metrics
        profit_loss_per_symbol = data.groupby('symbol')['profit_loss'].sum().reset_index()
        profit_loss_per_symbol.columns = ['symbol', 'total_profit_loss']
        most_profitable_symbol = profit_loss_per_symbol.loc[profit_loss_per_symbol['total_profit_loss'].idxmax()]
        least_profitable_symbol = profit_loss_per_symbol.loc[profit_loss_per_symbol['total_profit_loss'].idxmin()]
        
        # Calculate risk-reward ratio
        risk_reward_ratios = data.groupby('symbol').apply(lambda df: df[df['profit_loss'] > 0]['profit_loss'].sum() / -df[df['profit_loss'] < 0]['profit_loss'].sum()).reset_index()
        risk_reward_ratios.columns = ['symbol', 'risk_reward_ratio']
    except Exception as e:
        logging.error(f"Error in calculating performance metrics: {e}")
        raise
    
    logging.info("Performance metrics calculated successfully.")
    return total_profit_loss, win_rate, average_duration, best_trade, worst_trade, most_profitable_symbol, least_profitable_symbol, risk_reward_ratios


# Generate performance report
def generate_performance_report(total_profit_loss, win_rate, average_duration, best_trade, worst_trade, most_profitable_symbol, least_profitable_symbol, risk_reward_ratios, config):
    high_win_rate_threshold = config['thresholds']['high_win_rate']['value']
    long_trade_duration_threshold = config['thresholds']['long_trade_duration']['value']
    
    high_win_rate = win_rate >= high_win_rate_threshold
    long_trade_duration = average_duration >= long_trade_duration_threshold
    
    report = f"""
    Performance Report
    ==================
    Total Profit/Loss: ${total_profit_loss:.2f}
    Win Rate: {win_rate:.2%} ({'High' if high_win_rate else 'Low'})
    Average Trade Duration (hours): {average_duration:.2f} ({'Long' if long_trade_duration else 'Short'})

    Best Trade:
    -----------
    Symbol: {best_trade['symbol']}
    Date: {best_trade['date']}
    Profit: ${best_trade['profit_loss']:.2f}

    Worst Trade:
    ------------
    Symbol: {worst_trade['symbol']}
    Date: {worst_trade['date']}
    Loss: ${worst_trade['profit_loss']:.2f}

    Most Profitable Symbol:
    -----------------------
    Symbol: {most_profitable_symbol['symbol']}
    Total Profit: ${most_profitable_symbol['total_profit_loss']:.2f}

    Least Profitable Symbol:
    ------------------------
    Symbol: {least_profitable_symbol['symbol']}
    Total Loss: ${least_profitable_symbol['total_profit_loss']:.2f}

    Risk-Reward Ratios:
    -------------------
    {risk_reward_ratios.to_string(index=False)}

    Key Insights:
    -------------
    1. High Win Rate: {'Yes' if high_win_rate else 'No'} (Threshold: {high_win_rate_threshold * 100}%)
    2. Long Trade Duration: {'Yes' if long_trade_duration else 'No'} (Threshold: {long_trade_duration_threshold} hours)

    Recommendations:
    ----------------
    1. **Replicate Successful Strategies:** Analyze your best trade on {best_trade['date']} with {best_trade['symbol']} to understand what worked and try to replicate those strategies.
    2. **Learn from Mistakes:** Identify and learn from your worst trade on {worst_trade['date']} with {worst_trade['symbol']} to avoid repeating mistakes.
    3. **Focus on Profitable Symbols:** Consider increasing trades in {most_profitable_symbol['symbol']} as it has been the most profitable.
    4. **Review Unprofitable Symbols:** Analyze trades in {least_profitable_symbol['symbol']} to understand why they resulted in losses and consider reducing exposure.
    5. **Diversified Strategy:** Maintain a diversified trading strategy to spread risk and avoid heavy losses on a single trade.
    6. **Continuous Improvement:** Regularly review and refine your trading strategies based on performance data to enhance profitability.
    7. **Achieve High Win Rate:** Aim to increase your win rate by focusing on strategies that have historically been successful.
    8. **Manage Trade Duration:** Avoid holding trades for longer durations unless there is a clear strategy and rationale for doing so.
    """
    
    logging.info("Performance report generated.")
    return report

if __name__ == "__main__":
    # Load configuration
    config = load_config()

    # Example usage
    data = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04'],
        'symbol': ['AAPL', 'AAPL', 'GOOG', 'GOOG'],
        'price': [150, 155, 2700, 2750],
        'quantity': [10, 5, 2, 1],
        'action': ['buy', 'sell', 'buy', 'sell']
    })
    expired_worthless = pd.DataFrame({
        'date': ['2023-01-05', '2023-01-06'],
        'symbol': ['AAPL', 'GOOG'],
        'total_loss': [200, 300]
    })

    total_loss_expired_worthless = expired_worthless['total_loss'].sum()
    total_value_held_options = data['price'].sum() * 10  # Placeholder for the actual calculation
    overall_profit_loss = calculate_overall_profit_loss(total_loss_expired_worthless, total_value_held_options)
    trade_summary, significant_trades, large_losses = trade_analysis(data, config)
    risk_report = generate_risk_management_report(total_loss_expired_worthless, total_value_held_options, overall_profit_loss, trade_summary, significant_trades, large_losses, expired_worthless, config)
    print(risk_report)

    total_profit_loss, win_rate, average_duration, best_trade, worst_trade, most_profitable_symbol, least_profitable_symbol, risk_reward_ratios = calculate_performance_metrics(data)
    performance_report = generate_performance_report(total_profit_loss, win_rate, average_duration, best_trade, worst_trade, most_profitable_symbol, least_profitable_symbol, risk_reward_ratios, config)
    print(performance_report)
