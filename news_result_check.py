# -*- coding: utf-8 -*-
"""
Created on Wed May 28 04:12:40 2025

1. download report from mt5
2. move report to google sheets
3. separate the into deals and positions
4. add the comments column to positions
5. copy back to excel and separate comments column
6. save as book1.csv in same folder as this code

@author: LK
"""

import pandas as pd

# Load your data (replace with your actual data source)
df = pd.read_csv('Book1.csv')  # Or pd.read_excel(), etc.


# Group by 'comment' and calculate count & total profit
result = df.groupby('comment').agg(
    Trade_Count=('Profit', 'size'),  # Count of trades per comment
    Total_Profit=('Profit', 'sum')   # Sum of Profit per comment
).reset_index()

# Group by Symbol and Comment, then aggregate Count and Sum of Profit
result2 = df.groupby(['Symbol', 'comment']).agg(
    Count=('Profit', 'size'),  # Count occurrences
    Total_Profit=('Profit', 'sum')  # Sum Profit
).reset_index()

# Group by Symbol and Comment, then sum Profit
profit_summary = df.groupby(['Symbol', 'comment'])['Profit'].sum().reset_index()