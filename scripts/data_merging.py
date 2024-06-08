# main.py

import os
from datetime import datetime
import sqlite3
import stocktwits_sentiment_analysis as stsa
import data_merging as dm

def main():
    # Set up logging
    stsa.setup_logging()
    
    # Set up the database
    stsa.setup_database()
    
    # Get input from the user
    ticker = input("Enter the stock ticker symbol: ").strip().upper()
    date_str = datetime.now().strftime('%Y-%m-%d')
    folder_path = os.path.join("data", ticker, date_str)
    api_key = "your_news_api_key_here"  # Replace with your News API key

    # Fetch social sentiment data from StockTwits
    stocktwits_html = stsa.get_social_sentiment(ticker, max_scrolls=100)

    # Extract messages and sentiments from StockTwits
    sentiment_data = stsa.extract_messages_and_sentiments(stocktwits_html)

    # Fetch stock data and news headlines
    stock_data = stsa.get_stock_data(ticker)
    news_headlines = stsa.get_news_data(ticker, api_key)

    # Extract headlines
    headlines = news_headlines['headline'].tolist() if not news_headlines.empty else []

    # Save to database
    conn = sqlite3.connect("trade_analyzer.db")
    stsa.insert_stock_data(conn, ticker, stock_data)
    stsa.insert_news_headlines(conn, ticker, headlines)
    stsa.insert_sentiment_data(conn, ticker, sentiment_data)
    conn.close()

    # Merge stock data with sentiment data
    merged_data = dm.merge_data(stock_data, sentiment_data)

    # Display and save the merged data to CSV
    stsa.display_data(merged_data, headlines, sentiment_data, folder_path)

if __name__ == "__main__":
    main()
