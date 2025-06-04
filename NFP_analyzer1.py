# -*- coding: utf-8 -*-
"""
Created on Wed Jun  4 10:17:00 2025

@author: jbriz
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1a. Upload the news event time for the year - news_data
news_data = pd.read_csv('C:/Users/jbriz/CODE/2021_nfp_data.csv')  # Assuming CSV file with news data

# 1b. Update news_data column headers
news_data.columns = ['datetime', 'actual', 'forecast', 'good/bad']

# 2. Upload the 1min data for the currency pair - price_data_1m
price_data_1m = pd.read_csv('C:/Users/jbriz/CODE/DAT_MT_USDJPY_M1_2021.csv')  # Assuming CSV file with 1min data

# 3. Update price_data_1m column headers
price_data_1m.columns = ['date', 'time', 'Open', 'High', 'Low', 'Close', 'Vol']

# 4. Convert 1min data to 5min OHLC data - price_data_5m
price_data_1m['datetime'] = pd.to_datetime(price_data_1m['date'] + ' ' + price_data_1m['time'], format='%Y.%m.%d %H:%M')
price_data_5m = price_data_1m.resample('5T', on='datetime').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Vol': 'sum'}).reset_index()
price_data_5m = price_data_5m.dropna()

# 5. Convert price_data_5m to datetime, actual, forecast, good/bad, OHLC for 1hr before and 3hrs after news time
def create_ohlc_window(news_row):
    news_time = pd.to_datetime(news_row['datetime'], format='%Y.%m.%d %H:%M')
    start_time = news_time - timedelta(hours=1)  # 1 hour before
    end_time = news_time + timedelta(hours=3)    # 3 hours after
    time_range = pd.date_range(start=start_time, end=end_time, freq='5T')
    
    # Filter 5min data for the time window
    window_data = price_data_5m[price_data_5m['datetime'].isin(time_range)]
    
    # Create result row
    result = {
        'datetime': news_row['datetime'],
        'actual': news_row['actual'],
        'forecast': news_row['forecast'],
        'good/bad': news_row['good/bad']
    }
    
    # Add OHLC for each 5-minute interval
    for t in time_range:
        t_str = t.strftime('%H:%M')
        if not window_data.empty and any(window_data['datetime'] == t):
            row = window_data[window_data['datetime'] == t].iloc[0]
            result[f'O_{t_str}'] = row['Open']
            result[f'H_{t_str}'] = row['High']
            result[f'L_{t_str}'] = row['Low']
            result[f'C_{t_str}'] = row['Close']
        else:
            result[f'O_{t_str}'] = np.nan
            result[f'H_{t_str}'] = np.nan
            result[f'L_{t_str}'] = np.nan
            result[f'C_{t_str}'] = np.nan
    
    return result

# Apply the function to each row in news_data
result_df = pd.DataFrame([create_ohlc_window(row) for _, row in news_data.iterrows()])

# 6. Convert result to CSV
result_df.to_csv('nfp_JPY_output2021.csv', index=False)
print("CSV file 'nfp_ohlc_output.csv' has been generated.")