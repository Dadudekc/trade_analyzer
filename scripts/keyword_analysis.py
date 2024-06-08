import pandas as pd
import re
from collections import Counter
import logging
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import sqlite3
from datetime import datetime
import os


# Ensure NLTK data is downloaded
nltk.download('stopwords')
nltk.download('punkt')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def clean_message(message):
    """
    Clean the message by removing URLs, stock symbols, special characters, and stopwords.
    
    Args:
        message (str): The input message string to be cleaned.
        
    Returns:
        str: The cleaned message.
    """
    try:
        # Remove URLs
        message = re.sub(r'http\S+|www\S+|https\S+', '', message, flags=re.MULTILINE)
        
        # Remove stock symbols and special characters
        message = re.sub(r'\$\w+', '', message)
        message = re.sub(r'[^A-Za-z0-9\s]', '', message)
        
        # Tokenize and remove stopwords
        stop_words = set(stopwords.words('english'))
        word_tokens = word_tokenize(message.lower())
        filtered_message = [word for word in word_tokens if word not in stop_words]
        
        return ' '.join(filtered_message)
    except Exception as e:
        logger.error(f"Error cleaning message: {e}")
        return ""

def perform_keyword_analysis(messages):
    """
    Perform keyword analysis on a list of messages and return the most common keywords.
    
    Args:
        messages (list): List of dictionaries containing messages.
        
    Returns:
        DataFrame: DataFrame containing the most common keywords and their frequencies.
    """
    words = []
    try:
        for message_data in messages:
            message = message_data['message']
            cleaned_message = clean_message(message)
            words.extend(cleaned_message.split())
        
        common_words = Counter(words).most_common(20)
        common_words_df = pd.DataFrame(common_words, columns=['word', 'frequency'])
        return common_words_df
    except Exception as e:
        logger.error(f"Error performing keyword analysis: {e}")
        return pd.DataFrame(columns=['word', 'frequency'])

def save_to_csv(data, filename):
    """
    Save DataFrame to a CSV file.
    
    Args:
        data (DataFrame): DataFrame to be saved.
        filename (str): The output CSV filename.
    """
    try:
        data.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Data saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving data to CSV: {e}")

def save_to_db(data, db_connection, table_name):
    """
    Save DataFrame to a SQL database.
    
    Args:
        data (DataFrame): DataFrame to be saved.
        db_connection (sqlite3.Connection): Database connection object.
        table_name (str): The name of the table to save data.
    """
    try:
        data.to_sql(table_name, db_connection, if_exists='append', index=False)
        logger.info(f"Data saved to {table_name} table in database")
    except Exception as e:
        logger.error(f"Error saving data to database: {e}")

def main():
    ticker = input("Enter the stock ticker symbol: ").strip().upper()
    date_str = datetime.now().strftime('%Y-%m-%d')
    folder_path = os.path.join("data", ticker, date_str)
    db_path = "path_to_your_database.db"

    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        return

    # Read data from CSV
    sentiment_csv_path = os.path.join(folder_path, 'sentiment_data.csv')
    try:
        sentiment_data = pd.read_csv(sentiment_csv_path)
    except FileNotFoundError as e:
        logger.error(f"Sentiment data CSV file not found: {e}")
        return

    # Perform keyword analysis
    messages = [{'message': row['content']} for index, row in sentiment_data.iterrows()]
    keyword_analysis_df = perform_keyword_analysis(messages)

    # Save results to CSV and database
    keyword_csv_path = os.path.join(folder_path, 'common_keywords.csv')
    save_to_csv(keyword_analysis_df, keyword_csv_path)
    save_to_db(keyword_analysis_df, conn, 'common_keywords')

    conn.close()

if __name__ == "__main__":
    main()
