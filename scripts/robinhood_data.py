#C:\DaDudeKC\Trade Analyzer\scripts\robinhood_data.py

import robin_stocks.robinhood as rh
import pandas as pd
import json

def login_robinhood(username, password):
    """
    Logs into Robinhood account.

    Args:
        username (str): Robinhood username.
        password (str): Robinhood password.
    """
    rh.login(username, password)

def download_robinhood_data(username, password):
    """
    Downloads all stock orders (open and past) from Robinhood account and saves them to a CSV file.

    Args:
        username (str): Robinhood username.
        password (str): Robinhood password.

    Returns:
        pd.DataFrame: DataFrame containing all stock orders.
    """
    login_robinhood(username, password)
    
    open_orders = rh.orders.get_all_open_stock_orders()
    past_orders = rh.orders.get_all_stock_orders()
    
    if past_orders:
        print("Detailed Order Structure:")
        print(json.dumps(past_orders[0], indent=2))
    else:
        print("No past orders found.")
    
    orders = open_orders + past_orders
    
    if not orders:
        print("No orders found.")
        return pd.DataFrame()
    
    data = []
    for order in orders:
        instrument_data = rh.stocks.get_instrument_by_url(order['instrument'])
        symbol = instrument_data['symbol']
        
        if order['executions']:
            execution_price = float(order['executions'][0]['price'])
        else:
            execution_price = float(order['price']) if order['price'] else 0.0
        
        data.append([
            order['updated_at'],
            symbol,
            order['side'],
            float(order['quantity']),
            execution_price,
            order['state']
        ])
        
    df = pd.DataFrame(data, columns=['date', 'symbol', 'action', 'quantity', 'price', 'status'])
    df.to_csv('robinhood_data.csv', index=False)
    return df

# Example usage
if __name__ == "__main__":
    username = 'your_robinhood_username'
    password = 'your_robinhood_password'
    df = download_robinhood_data(username, password)
    print(df.head())
