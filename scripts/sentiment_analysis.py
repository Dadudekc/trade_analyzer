# C:\DaDudeKC\Trade Analyzer\scripts\sentiment_analysis.py

import os
import time
import pandas as pd
import logging
import argparse
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
def setup_logging(level=logging.INFO):
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    return logger

logger = setup_logging()

def analyze_sentiment_vader(data):
    analyzer = SentimentIntensityAnalyzer()
    if 'content' in data.columns:
        data['content'] = data['content'].fillna('')  # Replace None values with empty string
    else:
        logger.warning("'content' column is missing in the DataFrame.")
        data['content'] = ''
    data['vader_sentiment'] = data['content'].apply(lambda x: analyzer.polarity_scores(x)['compound'])
    return data

def analyze_sentiment_textblob(messages):
    sentiments = []
    for message_data in messages:
        try:
            message = message_data.get('message', '')
            analysis = TextBlob(message)
            sentiment = analysis.sentiment.polarity
            sentiments.append({
                'timestamp': message_data.get('timestamp', datetime.now()),
                'content': message,
                'textblob_sentiment': sentiment
            })
        except Exception as e:
            logger.error(f"Error processing message: {message_data}. Error: {e}")
    return pd.DataFrame(sentiments)

def perform_sentiment_analysis(messages, sentiment_filename='sentiment_analysis.csv', trends_filename='daily_sentiment_trends.csv'):
    try:
        logger.info("Starting sentiment analysis with TextBlob.")
        textblob_sentiments_df = analyze_sentiment_textblob(messages)

        logger.info("TextBlob analysis complete. DataFrame head: \n%s", textblob_sentiments_df.head())

        logger.info("Starting sentiment analysis with VADER.")
        vader_sentiments_df = analyze_sentiment_vader(textblob_sentiments_df)

        logger.info("VADER analysis complete. DataFrame head: \n%s", vader_sentiments_df.head())

        combined_sentiments_df = pd.merge(
            textblob_sentiments_df[['timestamp', 'content', 'textblob_sentiment']],
            vader_sentiments_df[['timestamp', 'content', 'vader_sentiment']],
            on=['timestamp', 'content']
        )
        
        logger.info("Combined DataFrame head: \n%s", combined_sentiments_df.head())

        combined_sentiments_df.to_csv(sentiment_filename, index=False, encoding='utf-8')
        logger.info(f"Sentiment analysis saved to {sentiment_filename}")

        combined_sentiments_df['date'] = pd.to_datetime(combined_sentiments_df['timestamp']).dt.date
        daily_sentiment = combined_sentiments_df.groupby('date').agg({
            'textblob_sentiment': 'mean',
            'vader_sentiment': 'mean'
        }).reset_index()
        daily_sentiment.to_csv(trends_filename, index=False, encoding='utf-8')
        logger.info(f"Daily sentiment trends saved to {trends_filename}")
    except KeyError as e:
        logger.error(f"KeyError occurred during sentiment analysis: {e}")
    except Exception as e:
        logger.error(f"An error occurred during sentiment analysis: {e}")

def load_messages_from_file(input_file):
    """
    Load messages from a file. The file should contain JSON-like dictionaries per line.
    """
    try:
        messages = pd.read_json(input_file, lines=True)
        logger.info(f"Loaded {len(messages)} messages from {input_file}")
        return messages.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Error loading messages from file: {e}")
        return []

def get_social_sentiment(ticker, max_scrolls=20, scroll_pause_time=1):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        url = f'https://stocktwits.com/symbol/{ticker}'
        driver.get(url)
        time.sleep(3)  # Allow time for the page to load

        last_height = driver.execute_script("return document.body.scrollHeight")
        collected_messages = []

        for scroll in range(max_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

            messages = driver.find_elements(By.XPATH, '//div[@class="message__content"]')
            timestamps = driver.find_elements(By.XPATH, '//div[@class="message__time"]')

            logger.info(f"Found {len(messages)} messages and {len(timestamps)} timestamps on scroll {scroll + 1}.")

            for message, timestamp in zip(messages, timestamps):
                try:
                    logger.info(f"Message: {message.text}, Timestamp: {timestamp.text}")
                    timestamp_text = timestamp.text
                    if "am" in timestamp_text.lower() or "pm" in timestamp_text.lower():
                        timestamp_obj = datetime.strptime(timestamp_text, '%I:%M %p - %b %d, %Y')
                    else:
                        timestamp_obj = datetime.strptime(timestamp_text, '%b %d, %Y')
                    content = message.text
                    analysis = TextBlob(content)
                    sentiment = analysis.sentiment.polarity
                    message_data = {'timestamp': timestamp_obj, 'message': content, 'sentiment': sentiment}
                    collected_messages.append(message_data)
                except ValueError as e:
                    logger.error(f"Error parsing timestamp: {e}")
                    continue

        logger.info(f"Collected {len(collected_messages)} messages.")
        return pd.DataFrame(collected_messages)
    except Exception as e:
        logger.error(f"Failed to fetch social sentiment data for {ticker}. Error: {e}.")
        return pd.DataFrame()
    finally:
        driver.quit()

def main():
    parser = argparse.ArgumentParser(description="Perform sentiment analysis on messages.")
    parser.add_argument('--input_file', type=str, help='Path to the input file containing messages.')
    parser.add_argument('--sentiment_file', type=str, default='sentiment_analysis.csv', help='Path to save the sentiment analysis results.')
    parser.add_argument('--trends_file', type=str, default='daily_sentiment_trends.csv', help='Path to save the daily sentiment trends.')
    parser.add_argument('--log_level', type=str, default='INFO', help='Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).')
    parser.add_argument('--ticker', type=str, help='Ticker symbol for fetching social sentiment from StockTwits.')

    args = parser.parse_args()

    logger.setLevel(getattr(logging, args.log_level.upper(), logging.INFO))

    if args.input_file and os.path.exists(args.input_file):
        messages = load_messages_from_file(args.input_file)
    elif args.ticker:
        messages_df = get_social_sentiment(args.ticker)
        messages = messages_df.to_dict(orient='records')
    else:
        logger.error("Input file not provided or does not exist. Using default sample messages for analysis.")
        messages = [
            {'timestamp': '2024-05-23 22:42:23', 'message': 'This is a great stock!'},
            {'timestamp': '2024-05-23 22:43:23', 'message': 'Not sure about the future of this stock.'},
            {'timestamp': '2024-05-23 22:44:23', 'message': 'I think this stock is overvalued.'},
            # Add more sample messages as needed
        ]

    perform_sentiment_analysis(messages, sentiment_filename=args.sentiment_file, trends_filename=args.trends_file)

if __name__ == "__main__":
    main()
