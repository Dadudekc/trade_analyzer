import os
import time
import re
import pandas as pd
import logging
from bs4 import BeautifulSoup
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import pytesseract

# Path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Setup logging
def setup_logging(level=logging.INFO):
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    return logger

logger = setup_logging()

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
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='message']")))

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

    data.to_csv(file_path, index=False)
    logger.info(f"Data saved to {file_path}")

def display_data(stock_data, headlines, sentiment_data, folder_path):
    stock_df = pd.DataFrame(stock_data)
    headlines_df = pd.DataFrame({'headline': headlines})

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
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='message']")))

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
                timestamp = timestamp_elem['datetime']
                content = content_elem.get_text(strip=True)
                if "am" in timestamp.lower() or "pm" in timestamp.lower():
                    timestamp = datetime.strptime(timestamp, '%I:%M %p - %b %d, %Y')
                else:
                    timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
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

def login_if_needed(driver, username, password):
    print("Checking if login is needed...")
    # Check if the login form is present
    try:
        driver.find_element(By.ID, "user_email")
        driver.find_element(By.ID, "user_password")
        
        # Perform login actions
        print("Logging in...")
        driver.find_element(By.ID, "user_email").send_keys(username)
        driver.find_element(By.ID, "user_password").send_keys(password)
        driver.find_element(By.NAME, "commit").click()
        
        # Wait for the login to complete
        time.sleep(5)
        print("Login successful.")
    except Exception as e:
        # Login form not present, no need to log in
        print("Login not needed.")
        pass

def take_screenshot(driver, filename):
    driver.save_screenshot(filename)
    print(f"Screenshot saved as {filename}")

def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, config='--psm 6')  # Use a specific page segmentation mode
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {image_path}. Error: {e}")
        return ""

def clean_extracted_text(text):
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    return cleaned_text

def scroll_and_capture_screenshots(driver, scroll_count=3, scroll_delay=2, output_dir="screenshots"):
    os.makedirs(output_dir, exist_ok=True)
    screenshots = []
    for i in range(scroll_count):
        filename = os.path.join(output_dir, f"screenshot_{i+1}.png")
        take_screenshot(driver, filename)
        screenshots.append(filename)
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(scroll_delay)
        print(f"Scrolled and captured screenshot {i+1}/{scroll_count}")
    return screenshots

def main():
    username = "your_username"
    password = "your_password"
    ticker = input("Enter the stock ticker symbol: ")
    date_str = datetime.now().strftime('%Y-%m-%d')
    folder_path = os.path.join("data", ticker, date_str)

    # Fetch social sentiment data from StockTwits
    stocktwits_html = get_social_sentiment(ticker, max_scrolls=100)

    # Extract messages and sentiments from StockTwits
    sentiment_data = extract_messages_and_sentiments(stocktwits_html)

    # Initialize the WebDriver
    print("Initializing WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-logging")  # Disable logging
    chrome_options.add_argument("--log-level=3")  # Suppress only critical messages

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    print("WebDriver initialized.")

    # Retry getting the page source
    url = f"https://stocktwits.com/symbol/{ticker}"
    print(f"Fetching page source for {url} with retries...")
    fetch_html_content(url)
    
    # Check if login is needed and perform login if required
    login_if_needed(driver, username, password)
    
    # Allow the page to load completely
    print("Waiting for the page to load completely...")
    time.sleep(5)
    
    # Scroll and capture multiple screenshots
    print("Scrolling and capturing screenshots...")
    screenshots = scroll_and_capture_screenshots(driver, scroll_count=5, scroll_delay=3)
    
    # Extract and clean text from each screenshot
    for screenshot in screenshots:
        extracted_text = extract_text_from_image(screenshot)
        cleaned_text = clean_extracted_text(extracted_text)
        print(f"Cleaned Extracted Text from {screenshot}: {cleaned_text}")
    
    # Display data
    display_data([], [], sentiment_data, folder_path)

    # Close the driver
    driver.quit()
    print("Driver closed.")

if __name__ == "__main__":
    main()
