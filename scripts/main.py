# main.py

import os
from datetime import datetime
import sqlite3
import stocktwits_sentiment_analysis as stsa
import data_merging as dm
import robinhood_data as rhd
import keyword_analysis as ka
import model_training as mt
import data_processing as dp
import enhancements as enh

def main():
    # Set up logging
    stsa.setup_logging()
    
    # Set up the database
    stsa.setup_database()
    
    # Get input from the user
    ticker = input("Enter the stock ticker symbol: ").strip().upper()
    username = input("Enter your Robinhood username: ").strip()
    password = input("Enter your Robinhood password: ").strip()
    date_str = datetime.now().strftime('%Y-%m-%d')
    folder_path = os.path.join("data", ticker, date_str)
    api_key = "your_news_api_key_here"  # Replace with your News API key

    # Fetch Robinhood data
    robinhood_data = rhd.download_robinhood_data(username, password)
    
    # Fetch social sentiment data from StockTwits
    stocktwits_html = stsa.get_social_sentiment(ticker, max_scrolls=100)

    # Extract messages and sentiments from StockTwits
    sentiment_data = stsa.extract_messages_and_sentiments(stocktwits_html)
    sentiment_data = dp.perform_sentiment_analysis(sentiment_data)

    # Save sentiment messages to CSV
    dp.save_messages_to_csv(sentiment_data.to_dict('records'), os.path.join(folder_path, 'sentiment_data.csv'))

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
    
    # Save Robinhood data to the database
    if not robinhood_data.empty:
        robinhood_data.to_sql('RobinhoodData', conn, if_exists='replace', index=False)
    
    conn.close()

    # Merge stock data with sentiment data
    merged_data = dm.merge_data(stock_data, sentiment_data)

    # Display and save the merged data to CSV
    stsa.display_data(merged_data, headlines, sentiment_data, folder_path)

    # Perform keyword analysis
    messages = [{'message': row['content']} for index, row in sentiment_data.iterrows()]
    keyword_analysis_df = ka.perform_keyword_analysis(messages)
    keyword_csv_path = os.path.join(folder_path, 'common_keywords.csv')
    ka.save_to_csv(keyword_analysis_df, keyword_csv_path)
    conn = sqlite3.connect("trade_analyzer.db")
    ka.save_to_db(keyword_analysis_df, conn, 'common_keywords')
    conn.close()

    # Train and evaluate the model
    predictions = {}
    errors = {}
    best_r2_file = os.path.join(folder_path, 'best_r2.txt')
    best_r2, predicted_price, prediction_date = mt.train_and_evaluate_model(
        merged_data, '1d', best_r2_file, predictions, errors
    )
    print(f"Predicted price for {prediction_date.strftime('%Y-%m-%d')}: {predicted_price:.2f}")

    # Optionally display Robinhood data
    if not robinhood_data.empty:
        print("\nRobinhood Data:")
        print(robinhood_data.head())
        robinhood_data.to_csv(os.path.join(folder_path, 'robinhood_data.csv'), index=False)

    # Future enhancements
    if not robinhood_data.empty:
        # Personalized Insights
        enh.analyze_trade_patterns(robinhood_data)
        enh.compare_with_sentiment(robinhood_data, sentiment_data)
        enh.suggest_improvements(robinhood_data, sentiment_data, stock_data)

        # Risk Assessments
        enh.calculate_risk_metrics(robinhood_data)
        enh.identify_high_risk_trades(robinhood_data)
        enh.provide_risk_warnings(robinhood_data)

        # Performance Analysis
        enh.track_performance_metrics(robinhood_data)
        enh.compare_with_market(robinhood_data)
        enh.visualize_performance(robinhood_data)

if __name__ == "__main__":
    main()
