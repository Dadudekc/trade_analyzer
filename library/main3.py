import os
import time
import pandas as pd
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import yfinance as yf
import requests
from requests.exceptions import HTTPError, ReadTimeout
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError
import sqlite3

# Setup logging
def setup_logging(level=logging.INFO):
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    return logger

logger = setup_logging()

def setup_database(db_name="trade_analyzer.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create tables with unique constraints
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS StockData (
        id INTEGER PRIMARY KEY,
        ticker TEXT,
        date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        adj_close REAL,
        volume INTEGER,
        UNIQUE(ticker, date)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS NewsHeadlines (
        id INTEGER PRIMARY KEY,
        ticker TEXT,
        date TEXT,
        headline TEXT,
        UNIQUE(ticker, headline)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SentimentData (
        id INTEGER PRIMARY KEY,
        ticker TEXT,
        timestamp TEXT,
        content TEXT,
        textblob_sentiment REAL,
        vader_sentiment REAL,
        UNIQUE(ticker, timestamp, content)
    )
    ''')

    conn.commit()
    conn.close()

setup_database()

def fetch_html_content(url, max_scrolls=100, scroll_pause_time=2):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
    chrome_options.add_argument('log-level=3')  # Suppress logging

    service = ChromeService(ChromeDriverManager().install())

    with webdriver.Chrome(service=service, options=chrome_options) as driver:
        try:
            logger.info(f"Fetching URL: {url}")
            driver.get(url)
            time.sleep(5)  # Allow time for the page to load

            last_height = driver.execute_script("return document.body.scrollHeight")
            collected_html = driver.page_source

            for scroll in range(max_scrolls):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause_time)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                collected_html = driver.page_source

            logger.info("Collected HTML content")
            return collected_html
        except Exception as e:
            logger.error(f"Failed to fetch HTML content from {url}. Error: {e}.")
            return ""

def analyze_sentiment(data):
    analyzer = SentimentIntensityAnalyzer()
    data['textblob_sentiment'] = data['content'].apply(lambda x: TextBlob(x).sentiment.polarity)
    data['vader_sentiment'] = data['content'].apply(lambda x: analyzer.polarity_scores(x)['compound'])
    return data

def save_data_to_csv(data, folder_path, filename):
    file_path = os.path.join(folder_path, filename)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Append new data to the existing CSV
    if os.path.exists(file_path):
        existing_data = pd.read_csv(file_path)
        data = pd.concat([existing_data, data]).drop_duplicates().reset_index(drop=True)

    data.to_csv(file_path, index=False)
    logger.info(f"Data saved to {file_path}")

def insert_stock_data(conn, ticker, stock_data):
    cursor = conn.cursor()
    for index, row in stock_data.iterrows():
        try:
            cursor.execute('''
            INSERT OR IGNORE INTO StockData (ticker, date, open, high, low, close, adj_close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ticker, row['Date'].strftime('%Y-%m-%d'), row['Open'], row['High'], row['Low'], row['Close'], row['Adj Close'], row['Volume']))
        except sqlite3.IntegrityError as e:
            logger.warning(f"Skipping duplicate entry: {e}")
    conn.commit()

def insert_news_headlines(conn, ticker, headlines):
    cursor = conn.cursor()
    for headline in headlines:
        try:
            cursor.execute('''
            INSERT OR IGNORE INTO NewsHeadlines (ticker, date, headline)
            VALUES (?, ?, ?)
            ''', (ticker, datetime.now().strftime('%Y-%m-%d'), headline))
        except sqlite3.IntegrityError as e:
            logger.warning(f"Skipping duplicate entry: {e}")
    conn.commit()

def insert_sentiment_data(conn, ticker, sentiment_data):
    cursor = conn.cursor()
    for index, row in sentiment_data.iterrows():
        try:
            cursor.execute('''
            INSERT OR IGNORE INTO SentimentData (ticker, timestamp, content, textblob_sentiment, vader_sentiment)
            VALUES (?, ?, ?, ?, ?)
            ''', (ticker, row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), row['content'], row['textblob_sentiment'], row['vader_sentiment']))
        except sqlite3.IntegrityError as e:
            logger.warning(f"Skipping duplicate entry: {e}")
    conn.commit()

def display_data(stock_data, headlines, sentiment_data, folder_path):
    stock_df = pd.DataFrame(stock_data)
    headlines_df = pd.DataFrame({'headline': headlines}) if headlines else pd.DataFrame(columns=['headline'])

    save_data_to_csv(stock_df, folder_path, 'stock_data.csv')
    save_data_to_csv(headlines_df, folder_path, 'news_headlines.csv')
    save_data_to_csv(sentiment_data, folder_path, 'sentiment_data.csv')

    print("\nStock Data:")
    print(stock_df if not stock_df.empty else "No stock data available.")
    print("\nNews Headlines:")
    print(headlines_df if not headlines_df.empty else "No news headlines available.")
    print("\nSentiment Data:")
    if not sentiment_data.empty:
        print(sentiment_data[['timestamp', 'content', 'textblob_sentiment', 'vader_sentiment']])
    else:
        print("No sentiment data available.")

def get_social_sentiment(ticker, max_scrolls=100, scroll_pause_time=2):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
    chrome_options.add_argument('log-level=3')  # Suppress logging

    service = ChromeService(ChromeDriverManager().install())

    with webdriver.Chrome(service=service, options=chrome_options) as driver:
        url = f"https://stocktwits.com/symbol/{ticker}"

        try:
            logger.info(f"Fetching StockTwits data for ticker: {ticker}")
            driver.get(url)
            time.sleep(5)  # Allow time for the page to load

            last_height = driver.execute_script("return document.body.scrollHeight")
            collected_html = driver.page_source

            for scroll in range(max_scrolls):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause_time)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                collected_html = driver.page_source

            logger.info(f"Collected HTML length: {len(collected_html)}")
            return collected_html
        except Exception as e:
            logger.error(f"Failed to fetch StockTwits data for {ticker}. Error: {e}.")
            return ""

def extract_messages_and_sentiments(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    messages = []

    logger.info("Extracting messages and sentiments from HTML content.")
    
    for message_div in soup.find_all('div', class_='RichTextMessage_body__4qUeP'):
        try:
            timestamp_elem = message_div.find_previous('time', class_='StreamMessage_timestamp__VVDmF')
            content_elem = message_div

            if timestamp_elem and content_elem:
                timestamp = datetime.strptime(timestamp_elem['datetime'], '%Y-%m-%dT%H:%M:%SZ')
                content = content_elem.get_text(strip=True)
                messages.append({'timestamp': timestamp, 'content': content})
        except Exception as e:
            logger.warning(f"Failed to extract message content. Error: {e}")
            continue

    if not messages:
        logger.warning("No messages found in the provided HTML content.")
    else:
        logger.info(f"Extracted {len(messages)} messages.")

    sentiment_data = pd.DataFrame(messages)
    if not sentiment_data.empty:
        sentiment_data = analyze_sentiment(sentiment_data)
    else:
        sentiment_data = pd.DataFrame(columns=['timestamp', 'content', 'textblob_sentiment', 'vader_sentiment'])

    return sentiment_data

def fetch_trends_data(pytrends, keyword, retries=5):
    attempt = 0
    while attempt < retries:
        try:
            pytrends.build_payload([keyword], cat=0, timeframe='today 5-y', geo='', gprop='')
            trends_data = pytrends.interest_over_time()
            if 'isPartial' in trends_data.columns:
                trends_data = trends_data.drop(columns=['isPartial'])
            trends_data.reset_index(inplace=True)
            return trends_data
        except TooManyRequestsError:
            logger.error("Too many requests to Google Trends. Retrying...")
            attempt += 1
            time.sleep(2 ** attempt)  # Exponential backoff
        except ReadTimeout:
            logger.error("Read timeout when fetching Google Trends data. Retrying...")
            attempt += 1
            time.sleep(2 ** attempt)  # Exponential backoff
    logger.error("Failed to fetch Google Trends data after multiple attempts.")
    return pd.DataFrame()

def get_stock_data(ticker, start_date="2022-01-01", end_date=None, interval="1d"):
    end_date = end_date or datetime.now().strftime('%Y-%m-%d')
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    data.reset_index(inplace=True)
    logger.info(f"Stock data columns: {data.columns}")
    if 'Datetime' in data.columns:
        data['Datetime'] = pd.to_datetime(data['Datetime'], errors='coerce').dt.tz_localize(None)
    elif 'Date' in data.columns:
        data['Datetime'] = pd.to_datetime(data['Date'], errors='coerce').dt.tz_localize(None)
    return data

def get_news_data(ticker, api_key):
    url = f'https://newsapi.org/v2/everything?q={ticker}&apiKey={api_key}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        news_data = [{'date': article['publishedAt'], 'headline': article['title'], 'content': article.get('description', '')} for article in articles]
        return pd.DataFrame(news_data)
    except HTTPError as e:
        if response.status_code == 401:
            logger.error(f"Failed to fetch news data for {ticker} due to authorization issues. Status code: {response.status_code}.")
        else:
            logger.error(f"Failed to fetch news data for {ticker}. Status code: {response.status_code}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException occurred: {e}. Skipping this data source.")
    return pd.DataFrame()

def main():
    ticker = input("Enter the stock ticker symbol: ").strip().upper()
    date_str = datetime.now().strftime('%Y-%m-%d')
    folder_path = os.path.join("data", ticker, date_str)
    api_key = "b81af850e99047739efe9718abd432ce"  # Replace with your News API key

    # Fetch social sentiment data from StockTwits
    stocktwits_html = get_social_sentiment(ticker, max_scrolls=100)

    # Extract messages and sentiments from StockTwits
    sentiment_data = extract_messages_and_sentiments(stocktwits_html)

    # Fetch stock data and news headlines
    stock_data = get_stock_data(ticker)
    news_headlines = get_news_data(ticker, api_key)

    # Extract headlines
    headlines = news_headlines['headline'].tolist() if not news_headlines.empty else []

    # Save to database
    conn = sqlite3.connect("trade_analyzer.db")
    insert_stock_data(conn, ticker, stock_data)
    insert_news_headlines(conn, ticker, headlines)
    insert_sentiment_data(conn, ticker, sentiment_data)
    conn.close()

    # Display and save the data to CSV
    display_data(stock_data, headlines, sentiment_data, folder_path)

if __name__ == "__main__":
    main()
