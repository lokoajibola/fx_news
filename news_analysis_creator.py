# -*- coding: utf-8 -*-
"""
Created on Sun Jun  1 15:04:21 2025

@author: LK
"""
import pandas as pd

# File paths for input CSVs (adjust these paths as needed)
gbpusd_file = 'C:/Users/MY PC/Desktop/fxcode/DAT_MT_EURUSD_M1_2024.csv'
nfp_file = 'C:/Users/MY PC/Desktop/fxcode/2024_nfp_data.csv'

# Load the GBP/USD data
gbpusd_df = pd.read_csv(gbpusd_file)
gbpusd_df['datetime'] = pd.to_datetime(gbpusd_df['date'] + ' ' + gbpusd_df['time'], format='%Y.%m.%d %H:%M')

# Load the NFP data
nfp_df = pd.read_csv(nfp_file)

# Map "Better" to "Good" and "Worse" to "Bad"
nfp_df['good/bad'] = nfp_df['good/bad'].replace({'Better': 'Good', 'Worse': 'Bad'})

# Function to extract 5-minute close prices for a given NFP date
def extract_nfp_prices(nfp_datetime_str):
    # Parse NFP datetime (in GMT)
    nfp_datetime = pd.to_datetime(nfp_datetime_str, format='%Y.%m.%d %H:%M')

    # Determine time range in GMT (7:30 AM to 11:30 AM EST/EDT)
    # If release is at 13:30 GMT, it's EST (GMT-5); if 12:30 GMT, it's EDT (GMT-4)
    release_hour = int(nfp_datetime_str.split(' ')[1].split(':')[0])
    if release_hour == 13:  # EST (e.g., January to March)
        start_time = nfp_datetime.replace(hour=12, minute=30)  # 7:30 AM EST = 12:30 GMT
        end_time = nfp_datetime.replace(hour=16, minute=30)    # 11:30 AM EST = 16:30 GMT
    else:  # EDT (e.g., April to December)
        start_time = nfp_datetime.replace(hour=11, minute=30)  # 7:30 AM EDT = 11:30 GMT
        end_time = nfp_datetime.replace(hour=15, minute=30)    # 11:30 AM EDT = 15:30 GMT

    time_range = pd.date_range(start=start_time, end=end_time, freq='5min')

    # Filter GBP/USD data for the NFP date
    date_str = nfp_datetime.strftime('%Y.%m.%d')
    daily_data = gbpusd_df[gbpusd_df['date'] == date_str].copy()
    if daily_data.empty:
        return None

    # Merge with time range and fill close prices
    price_df = pd.DataFrame({'datetime': time_range})
    price_df = price_df.merge(daily_data[['datetime', 'close']], on='datetime', how='left')
    price_df['close'] = price_df['close'].ffill().bfill()  # Interpolate missing data

    return price_df['close'].tolist()

# Define column names for 5-minute intervals (in EST/EDT, but extracted in GMT)
time_labels = pd.date_range(start='2024-01-01 07:30', end='2024-01-01 11:30', freq='5min')
price_columns = [f"{t.hour}.{t.minute:02d} close" for t in time_labels]

# Process each NFP date
results = []
for _, row in nfp_df.iterrows():
    prices = extract_nfp_prices(row['Datetime'])
    if prices is not None:
        result_row = {
            'Datetime': row['Datetime'],
            'actual': row['actual'],
            'forecast': row['forecast'],
            'good/bad': row['good/bad']
        }
        for col, price in zip(price_columns, prices):
            result_row[col] = price
        results.append(result_row)

# Create DataFrame and save to CSV
output_df = pd.DataFrame(results)
output_df.to_csv('nfp_eurusd_output.csv', index=False)
print("CSV file 'nfp_usdjpy_output.csv' has been generated.")