# C:\DaDudeKC\Trade Analyzer\scripts\model_training.py

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime, timedelta

# Setup logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def load_best_r2_score(filename: str) -> float:
    """
    Load the best R² score from a file.
    
    Args:
        filename (str): The file path to load the R² score from.
        
    Returns:
        float: The best R² score.
    """
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as file:
                return float(file.read())
        except ValueError as e:
            logger.error(f"Error reading R² score from file: {e}")
            return float('-inf')
    return float('-inf')

def save_best_r2_score(filename: str, r2: float) -> None:
    """
    Save the best R² score to a file.
    
    Args:
        filename (str): The file path to save the R² score to.
        r2 (float): The R² score to save.
    """
    with open(filename, 'w') as file:
        file.write(str(r2))

def save_best_model(model, filename: str, r2: float, best_r2: float) -> float:
    """
    Save the model to a file if it has a better R² score than the current best.
    
    Args:
        model: The model to save.
        filename (str): The file path to save the model to.
        r2 (float): The current R² score of the model.
        best_r2 (float): The best R² score so far.
        
    Returns:
        float: The updated best R² score.
    """
    if r2 > best_r2:
        joblib.dump(model, filename)
        logger.info(f"New best model saved to {filename} with R²: {r2:.2f}")
        save_best_r2_score(filename.replace('.pkl', '_r2.txt'), r2)
        return r2
    return best_r2

def next_weekday(d: datetime) -> datetime:
    """
    Get the next weekday date from the given date.
    
    Args:
        d (datetime): The current date.
        
    Returns:
        datetime: The next weekday date.
    """
    days_ahead = 1 if d.weekday() < 4 else 3 if d.weekday() == 4 else 2
    return d + timedelta(days=days_ahead)

def get_adjusted_date_range_for_small_intervals(interval: str, end_date: str) -> (str, str):
    """
    Get the adjusted date range based on the interval and end date.
    
    Args:
        interval (str): The interval type (e.g., '1m', '5m', etc.).
        end_date (str): The end date.
        
    Returns:
        tuple: The start date and end date as strings.
    """
    end_date = pd.to_datetime(end_date)
    if interval == '1m':
        start_date = end_date - pd.DateOffset(days=7)
    elif interval == '5m':
        start_date = end_date - pd.DateOffset(days=30)
    elif interval == '15m':
        start_date = end_date - pd.DateOffset(days=60)
    elif interval == '30m':
        start_date = end_date - pd.DateOffset(days=90)
    elif interval == '1h':
        start_date = end_date - pd.DateOffset(days=180)
    elif interval == '1d':
        start_date = end_date - pd.DateOffset(years=1)
    else:  # interval == '1wk'
        start_date = end_date - pd.DateOffset(years=5)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def train_and_evaluate_model(
    merged_data: pd.DataFrame, 
    interval: str, 
    best_r2_file: str, 
    predictions: dict, 
    errors: dict
) -> (float, float, datetime):
    """
    Train and evaluate the model on the given data and interval, saving the best model.
    
    Args:
        merged_data (pd.DataFrame): The merged data containing features and target.
        interval (str): The interval type (e.g., '1m', '5m', etc.).
        best_r2_file (str): The file path to save the best R² score.
        predictions (dict): Dictionary to store predictions.
        errors (dict): Dictionary to store errors.
        
    Returns:
        tuple: The best R² score, predicted price, and prediction date.
    """
    try:
        # Feature engineering
        features = ['Open', 'High', 'Low', 'Volume', 'sentiment']
        X = merged_data[features]
        y = merged_data['Close']

        # Data normalization
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        # Model training
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        # Model evaluation
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        errors[interval] = {'MAE': mae, 'R²': r2}
        logger.info(f"Model performance on test set ({interval}): MAE = {mae:.2f}, R² = {r2:.2f}")

        # Save the best model
        best_r2 = load_best_r2_score(best_r2_file)
        best_r2 = save_best_model(model, f'data/best_model_{interval}.pkl', r2, best_r2)

        # Predict the closing price for the next period
        future_time = X.iloc[-1, :].values.reshape(1, -1)  # Use the last row's features
        future_time_scaled = scaler.transform(future_time)
        predicted_price = model.predict(future_time_scaled)

        # Calculate the prediction date
        last_date = merged_data['Datetime'].max()
        prediction_date = next_weekday(last_date)

        predictions[interval] = (predicted_price[0], prediction_date)

        return best_r2, predicted_price[0], prediction_date
    except Exception as e:
        logger.error(f"Error in train_and_evaluate_model: {e}")
        return float('-inf'), float('-inf'), datetime.min
