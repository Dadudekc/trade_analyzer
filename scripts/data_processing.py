# C:\DaDudeKC\Trade Analyzer\scripts\data_processing.py

import pandas as pd
import logging
from textblob import TextBlob
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def perform_sentiment_analysis(sentiment_data):
    sentiment_data['sentiment'] = sentiment_data['message'].apply(lambda text: TextBlob(text).sentiment.polarity)
    return sentiment_data

def save_messages_to_csv(messages, filename='data/collected_messages.csv'):
    df = pd.DataFrame(messages)
    df.to_csv(filename, index=False, encoding='utf-8')
    logger.info(f"Messages saved to {filename}")

def load_trade_data(file_path):
    try:
        logger.info(f"Loading data from: {file_path}")
        data = pd.read_csv(file_path)
        logger.info("Initial data loaded:")
        logger.info(data.head())

        if 'date' not in data.columns:
            raise KeyError("'date' column is missing in the CSV file.")
        data['date'] = pd.to_datetime(data['date'], errors='coerce')
        logger.info("Data after converting 'date' column to datetime:")
        logger.info(data.head())

        data = data[data['date'].notna()]
        logger.info("Data after dropping rows with invalid dates:")
        logger.info(data.head())

        required_columns = ['date', 'symbol', 'action', 'quantity', 'price']
        for col in required_columns:
            if col not in data.columns:
                raise KeyError(f"'{col}' column is missing in the CSV file.")

    except Exception as e:
        logger.error(f"Error loading CSV file: {e}")
        return None
    return data

def identify_expired_options(data):
    logger.info("Identifying expired options...")
    bto = data[data['action'] == 'buy']
    stc = data[data['action'] == 'sell']

    merged = pd.merge(bto, stc, on=['symbol', 'quantity'], suffixes=('_buy', '_sell'))
    expired_worthless = bto[~bto.index.isin(merged.index)]
    expired_worthless.loc[:, 'total_loss'] = expired_worthless['price'] * expired_worthless['quantity']
    total_loss_expired_worthless = expired_worthless['total_loss'].sum()

    logger.info("Expired options identified:")
    logger.info(expired_worthless)

    return total_loss_expired_worthless, expired_worthless

def calculate_held_options_value(held_options_info):
    logger.info("Calculating held options value...")
    try:
        total_value_held_options = 0.0
        for i in range(len(held_options_info['symbol'])):
            symbol = held_options_info['symbol'][i]
            quantity = held_options_info['quantity'][i]
            price = held_options_info['price'][i]
            gain_percentage = held_options_info['gain_percentage'][i]
            try:
                quantity = float(quantity)
                price = float(price)
                gain_percentage = float(gain_percentage)
                current_value = quantity * price * (1 + gain_percentage / 100)
                total_value_held_options += current_value

                logger.info(f"Option {i+1}: Symbol: {symbol}, Quantity: {quantity}, Price: {price}, Gain Percentage: {gain_percentage}, Current Value: {current_value}")
            except ValueError as ve:
                logger.error(f"Invalid data for option {i+1}: {ve}")
                continue

        logger.info(f"Total value of held options: {total_value_held_options}")
        return total_value_held_options
    except Exception as e:
        logger.error(f"Error calculating held options value: {e}")
        return 0.0

def filter_data_by_date(data, start_date, end_date):
    try:
        logger.info(f"Filtering data from {start_date} to {end_date}...")
        data['date'] = pd.to_datetime(data['date'], errors='coerce')
        filtered_data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]
        logger.info("Data after date filtering:")
        logger.info(filtered_data.head())
        return filtered_data
    except Exception as e:
        logger.error(f"Error filtering data by date: {e}")
        return data

def get_adjusted_date_range_for_small_intervals(interval, end_date):
    end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')

    if interval == '1m':
        start_date_dt = end_date_dt - timedelta(days=1)
    elif interval == '5m':
        start_date_dt = end_date_dt - timedelta(days=5)
    elif interval == '15m':
        start_date_dt = end_date_dt - timedelta(days=15)
    elif interval == '30m':
        start_date_dt = end_date_dt - timedelta(days=30)
    elif interval == '1h':
        start_date_dt = end_date_dt - timedelta(days=60)
    elif interval == '1d':
        start_date_dt = end_date_dt - timedelta(days=365)
    elif interval == '1wk':
        start_date_dt = end_date_dt - timedelta(days=365 * 5)
    else:
        raise ValueError(f"Unsupported interval: {interval}")

    return start_date_dt.strftime('%Y-%m-%d'), end_date
