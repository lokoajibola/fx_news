# -*- coding: utf-8 -*-
"""
Created on Tue Jun 24 03:25:48 2025

AI prompt for the analysis of the result
news event: UK COre CPI
currency pair: GBPUSD
news time: O_0

now backtest on the attached data. optimize and come up with a post news strategy that 
would be most profitable and uses sl and tp. I would like to know the lot size for the trades, the risk, drawdown, 
no of wins and loss. please note that the column having O, H, L, or C before the 
time refer to Open, High, Low or Close respectively. C_0 is the price at 4 minutes 59seconds post news
O_+5 is the price at 5minutes post news. use points and pips when working with the 
difference in prices. I cannot enter the trade by news time due to news delays and market 
volatility. Also ensure the High and Low validation is done for the entry, exit sl and tp.

@author: LK
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# Save as
# file2 = 'USD_RetailSales_data.csv'
file2 = 'CAD_CPI_data.csv'
curr_pair = 'CADJPY'

# 1a. Upload the news event time for the year - news_data
news_data = pd.read_csv('C:/Users/MY PC/Desktop/fxcode/' + file2)  # Assuming CSV file with news data

# 1b. Update news_data column headers
news_data.columns = ['datetime', 'actual', 'forecast', 'good/bad']

# 2. Upload the 1min data for the currency pair - price_data_1m
price_data_1 = pd.read_csv('C:/Users/MY PC/Desktop/fxcode/DAT_MT_' + curr_pair + '_M1_2021.csv')
price_data_1.columns = ['date', 'time', 'Open', 'High', 'Low', 'Close', 'Vol']
price_data_2 = pd.read_csv('C:/Users/MY PC/Desktop/fxcode/DAT_MT_' + curr_pair + '_M1_2022.csv')
price_data_2.columns = ['date', 'time', 'Open', 'High', 'Low', 'Close', 'Vol']
price_data_3 = pd.read_csv('C:/Users/MY PC/Desktop/fxcode/DAT_MT_' + curr_pair + '_M1_2023.csv')
price_data_3.columns = ['date', 'time', 'Open', 'High', 'Low', 'Close', 'Vol']
price_data_4 = pd.read_csv('C:/Users/MY PC/Desktop/fxcode/DAT_MT_' + curr_pair + '_M1_2024.csv')
price_data_4.columns = ['date', 'time', 'Open', 'High', 'Low', 'Close', 'Vol']
# 3. Update price_data_1m column headers
price_data_1m = pd.concat([price_data_1, price_data_2, price_data_3, price_data_4], ignore_index=True)
price_data_1m.columns = ['date', 'time', 'Open', 'High', 'Low', 'Close', 'Vol']

# 4. Convert 1min data to 5min OHLC data - price_data_5m
price_data_1m['datetime'] = pd.to_datetime(price_data_1m['date'] + ' ' + price_data_1m['time'], format='%Y.%m.%d %H:%M')
price_data_5m = price_data_1m.resample('5T', on='datetime').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Vol': 'sum'}).reset_index()
price_data_5m = price_data_5m.dropna()

# 5. Convert price_data_5m to datetime, actual, forecast, good/bad, OHLC for 1hr before, news time as 0, and 3hrs after news time
def create_ohlc_window(news_row):
    news_time = pd.to_datetime(news_row['datetime'], format='%Y.%m.%d %H:%M')
    start_time = news_time - timedelta(hours=1)  # 1 hour before
    end_time = news_time + timedelta(hours=3)    # 3 hours after
    time_range = pd.date_range(start=start_time, end=end_time, freq='5T')
    
    # Define offsets: -60 to 0 (including 0) and +5 to +180
    time_offsets = list(range(-60, 0, 5)) + [0] + list(range(5, 185, 5))
    
    # Filter 5min data for the time window
    window_data = price_data_5m[(price_data_5m['datetime'] >= start_time) & (price_data_5m['datetime'] <= end_time)]
    
    # Create result row
    result = {
        'datetime': news_row['datetime'],
        'actual': news_row['actual'],
        'forecast': news_row['forecast'],
        'good/bad': news_row['good/bad']
    }
    
    # Add OHLC for each offset
    for offset in time_offsets:
        target_time = news_time + pd.Timedelta(minutes=offset)
        if offset == 0:
            # For news time (0 offset), use the 5-min candle starting at news_time
            candle_start = target_time
            candle_end = target_time + pd.Timedelta(minutes=5)
            candle_data = window_data[(window_data['datetime'] >= candle_start) & (window_data['datetime'] < candle_end)]
        else:
            # Round target_time to the nearest 5-minute boundary
            minutes = target_time.minute
            nearest_5min_offset = (minutes // 5) * 5  # Nearest 5-minute mark
            candle_time = target_time.replace(minute=nearest_5min_offset, second=0, microsecond=0)
            candle_data = window_data[window_data['datetime'] == candle_time]
        
        for prefix, col_name in [('O', 'Open'), ('H', 'High'), ('L', 'Low')]:
            result_col = f"{prefix}_{offset}"
            if not candle_data.empty:
                result[result_col] = candle_data[col_name].iloc[0]
            else:
                result[result_col] = np.nan
        
        # Special handling for Close: use the next 5-min candle's close for offset 0
        if offset == 0:
            next_candle_time = target_time + pd.Timedelta(minutes=5)
            next_candle_data = window_data[window_data['datetime'] == next_candle_time]
            col_name = f"C_{offset}"
            if not next_candle_data.empty:
                result[col_name] = next_candle_data['Close'].iloc[0]
            else:
                result[col_name] = np.nan
        else:
            col_name = f"C_{offset}"
            if not candle_data.empty:
                result[col_name] = candle_data['Close'].iloc[0]
            else:
                result[col_name] = np.nan
    
    return result

# Apply the function to each row in news_data
result_df = pd.DataFrame([create_ohlc_window(row) for _, row in news_data.iterrows()])

# 6. Convert result to CSV
file3 = curr_pair + file2
result_df.to_csv(file3, index=False)
print("CSV file has been generated: ", file3)