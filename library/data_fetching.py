#C:\DaDudeKC\Trade Analyzer\scripts\data_fetching.py

import logging
import pandas as pd
import requests
import yfinance as yf
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from textblob import TextBlob
import time  # Added this import
from datetime import datetime


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

API_KEY = 'b81af850e99047739efe9718abd432ce'  # Replace with your actual API key

def setup_driver():
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def close_popups(driver, check_interval=5, timeout=80):
    end_time = time.time() + timeout
    popups = [
        {'name': 'cookie notification', 'xpath': '//button[contains(text(), "Your Privacy Rights")]', 'log_message': 'Closed cookie notification'},
        {'name': 'consent pop-up', 'xpath': '//button[text()="Confirm My Choices"]', 'log_message': 'Closed consent pop-up'}
    ]
    while time.time() < end_time:
        for popup in popups:
            try:
                button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, popup['xpath'])))
                if button:
                    button.click()
                    logger.info(popup['log_message'])
            except TimeoutException:
                logger.info(f"No {popup['name']} to close or it took too long to appear")
            except WebDriverException as e:
                logger.error(f"Error interacting with {popup['name']}: {e}")
        try:
            alert = driver.switch_to.alert
            alert.accept()
            logger.info('Closed unexpected alert')
        except:
            pass
        time.sleep(check_interval)
    logger.info('Finished checking for pop-ups')


def fetch_social_sentiment(ticker, max_scrolls=20, scroll_pause_time=1):
    driver = setup_driver()
    try:
        url = f"https://stocktwits.com/symbol/{ticker}"
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        time.sleep(5)
        close_popups(driver)
        collected_messages = []
        for _ in range(max_scrolls):
            try:
                messages_section = WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "message__content")]')))
                logger.info('Messages section is loaded')
            except TimeoutException as e:
                logger.error(f"Timeout waiting for messages section: {e}")
                break
            messages = driver.find_elements(By.XPATH, '//div[contains(@class, "message__content")]')
            timestamps = driver.find_elements(By.XPATH, '//div[contains(@class, "message__timestamp")]')
            for message, timestamp in zip(messages, timestamps):
                try:
                    timestamp_text = timestamp.text
                    if "am" in timestamp_text.lower() or "pm" in timestamp_text.lower():
                        timestamp_obj = datetime.strptime(timestamp_text, '%I:%M %p - %b %d, %Y')
                    else:
                        timestamp_obj = datetime.strptime(timestamp_text, '%b %d, %Y')
                    content = message.text
                    analysis = TextBlob(content)
                    sentiment = analysis.sentiment.polarity
                    message_data = {'timestamp': timestamp_obj, 'message': content, 'sentiment': sentiment}
                except ValueError as e:
                    logger.error(f"Error parsing timestamp: {e}")
                    continue
                collected_messages.append(message_data)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
        if len(collected_messages) > 0:
            logger.info(f"Collected {len(collected_messages)} messages.")
        else:
            logger.warning("No messages collected.")
        return pd.DataFrame(collected_messages)
    except WebDriverException as e:
        logger.error(f"WebDriver exception: {e}")
        return pd.DataFrame()
    finally:
        driver.quit()

def fetch_messages(driver, max_messages=50, max_scrolls=20, scroll_pause_time=1):
    attempt = 0
    retries = 3
    collected_messages = []
    while attempt < retries:
        try:
            logger.info('Navigating to StockTwits TSLA page...')
            driver.get('https://stocktwits.com/symbol/TSLA')
            close_popups(driver)
            wait = WebDriverWait(driver, 60)
            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            for _ in range(max_scrolls):
                try:
                    messages_section = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "message")]')))
                    logger.info('Messages section is loaded')
                except TimeoutException as e:
                    logger.error(f"Timeout waiting for messages section: {e}")
                    raise
                messages = driver.find_elements(By.XPATH, '//div[contains(@class, "message__content")]')
                timestamps = driver.find_elements(By.XPATH, '//div[contains(@class, "message__timestamp")]')
                for message, timestamp in zip(messages, timestamps):
                    try:
                        timestamp_text = timestamp.text
                        if "am" in timestamp_text.lower() or "pm" in timestamp_text.lower():
                            timestamp_obj = datetime.strptime(timestamp_text, '%I:%M %p - %b %d, %Y')
                        else:
                            timestamp_obj = datetime.strptime(timestamp_text, '%b %d, %Y')
                        message_data = {'message': message.text, 'timestamp': timestamp_obj}
                    except ValueError as e:
                        logger.error(f"Error parsing timestamp: {e}")
                        continue
                    if message_data not in collected_messages:
                        collected_messages.append(message_data)
                        if len(collected_messages) >= max_messages:
                            return collected_messages
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause_time)
            if len(collected_messages) > 0:
                return collected_messages
        except TimeoutException as e:
            logger.error(f"Timeout occurred: {e}")
        except NoSuchElementException as e:
            logger.error(f"Element not found: {e}")
        except WebDriverException as e:
            logger.error(f"WebDriver exception: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        finally:
            attempt += 1
            if attempt < retries and len(collected_messages) == 0:
                logger.info(f"Retrying... ({attempt}/{retries})")
                time.sleep(5)
            else:
                if len(collected_messages) > 0:
                    break
                logger.error("Max retries reached. Exiting...")
    return collected_messages

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


def get_stock_data(ticker, start_date, end_date, interval):
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    data.reset_index(inplace=True)
    logger.info(f"Stock data columns: {data.columns}")
    if 'Datetime' in data.columns:
        data['Datetime'] = pd.to_datetime(data['Datetime'], errors='coerce').dt.tz_localize(None)
    elif 'Date' in data.columns:
        data['Datetime'] = pd.to_datetime(data['Date'], errors='coerce').dt.tz_localize(None)
    else:
        data['Datetime'] = pd.to_datetime(data.index, errors='coerce').dt.tz_localize(None)
    return data

def get_news_data(ticker, api_key=API_KEY):
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