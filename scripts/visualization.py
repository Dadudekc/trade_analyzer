import pandas as pd
import matplotlib.pyplot as plt
import logging
from sklearn.preprocessing import MinMaxScaler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def visualize_trading_performance(data):
    data['profit_loss'] = data['price'] * data['quantity']
    data['profit_loss_cumsum'] = data['profit_loss'].cumsum()

    plt.figure(figsize=(10, 6))
    plt.plot(data['date'], data['profit_loss_cumsum'], label='Cumulative Profit/Loss')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Profit/Loss')
    plt.title('Trading Performance Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()

    # Additional visualizations
    plt.figure(figsize=(10, 6))
    data['profit_loss'].plot(kind='hist', bins=50, alpha=0.7)
    plt.xlabel('Profit/Loss')
    plt.title('Profit/Loss Distribution')
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(10, 6))
    data.groupby('symbol')['profit_loss'].sum().plot(kind='bar')
    plt.xlabel('Symbol')
    plt.ylabel('Total Profit/Loss')
    plt.title('Profit/Loss by Symbol')
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(10, 6))
    data['action'].value_counts().plot(kind='pie', autopct='%1.1f%%')
    plt.title('Distribution of Buy/Sell Actions')
    plt.ylabel('')
    plt.show()

    # Separate winning and losing trades
    winning_trades = data[data['profit_loss'] > 0]
    losing_trades = data[data['profit_loss'] <= 0]

    plt.figure(figsize=(10, 6))
    plt.bar(['Winning Trades', 'Losing Trades'], [winning_trades['profit_loss'].sum(), losing_trades['profit_loss'].sum()])
    plt.ylabel('Total Profit/Loss')
    plt.title('Total Profit/Loss of Winning and Losing Trades')
    plt.grid(True)
    plt.show()

def visualize_sentiment_vs_stock(sentiment_file='data/daily_sentiment_trends.csv', stock_file='data/stock_data.csv', output_file='data/sentiment_vs_stock_price.png'):
    try:
        sentiment_df = pd.read_csv(sentiment_file)
        stock_data = pd.read_csv(stock_file)

        if sentiment_df.empty or stock_data.empty:
            logger.error("Sentiment data or stock data is empty, cannot plot visualization.")
            return

        sentiment_df['date'] = pd.to_datetime(sentiment_df['date'])
        stock_data['Date'] = pd.to_datetime(stock_data['Date'])

        scaler = MinMaxScaler()
        sentiment_df['Normalized_Sentiment'] = scaler.fit_transform(sentiment_df[['sentiment']])
        stock_data['Normalized_Close'] = scaler.fit_transform(stock_data[['Close']])

        plt.figure(figsize=(10, 5))
        plt.plot(sentiment_df['date'], sentiment_df['Normalized_Sentiment'], label='Sentiment')
        plt.plot(stock_data['Date'], stock_data['Normalized_Close'], label='Stock Price')
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.title('Sentiment and Stock Price Over Time')
        plt.legend()
        plt.savefig(output_file)
        plt.show()
        logger.info(f"Sentiment vs stock price visualization saved to {output_file}")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")

# Example usage
if __name__ == "__main__":
    # Load example data
    trade_data_file = 'data/cleaned_trade_data.csv'
    sentiment_file = 'data/daily_sentiment_trends.csv'
    stock_file = 'data/stock_data.csv'
    try:
        trade_data = pd.read_csv(trade_data_file)
        visualize_trading_performance(trade_data)
    except FileNotFoundError as e:
        logger.error(f"Trade data file not found: {e}")

    visualize_sentiment_vs_stock(sentiment_file, stock_file)
