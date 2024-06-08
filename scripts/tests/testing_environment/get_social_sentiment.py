# get_social_sentiment.py
import pandas as pd
import logging
from collect_messages import collect_messages

def meets_criteria(message):
    # Example filter function, adjust as needed
    return "stock" in message["message"]

def get_social_sentiment(ticker, max_scrolls=20, scroll_pause_time=1, screenshot_conditions=None):
    chrome_options = Options()
    # Add other options as needed
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        url = f'https://stocktwits.com/symbol/{ticker}'
        driver.get(url)
        time.sleep(3)  # Allow time for the page to load

        last_height = driver.execute_script("return document.body.scrollHeight")
        collected_messages = []

        screenshot_counter = 0

        for scroll in range(max_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

            if screenshot_conditions and screenshot_conditions(driver):
                driver.save_screenshot(f'screenshot_{screenshot_counter}.png')
                screenshot_counter += 1

            messages = driver.find_elements(By.XPATH, '//div[@class="message__content"]')
            timestamps = driver.find_elements(By.XPATH, '//div[@class="message__time"]')

            logger.info(f"Found {len(messages)} messages and {len(timestamps)} timestamps on scroll {scroll + 1}.")

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
