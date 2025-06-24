# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 22:42:06 2025

trading USD CPI

@author: LK
"""

import MetaTrader5 as mt5
import time
import datetime
import pandas as pd
import pytz


# INPUTS
news_result = 1 # 1 - Good/green, 0 - Bad/red
news_time  = '3:30pm'

pairs = ['XAUUSD'] #,  'GBPUSD', 'EURUSD', 'USDJPY', 'AUDUSD', 'USDCAD']

# # LOGIN TO MT5
# account = 7002735 #187255335 #51610727
# mt5.initialize("C:/Program Files/MetaTrader 5 IC Markets (SC)/terminal64.exe")
# authorized=mt5.login(account, password="xxxxxxxx", server = "ICMarketsSC-MT5-2")

# 1. LOGIN TO MT5
account = 51962256
mt5.initialize("C:/Program Files/FxPro - MetaTrader 5/terminal64.exe")
authorized=mt5.login(account, password="1nojf!W@MEUAz8", server = "mt5-demo.icmarkets.com")

if authorized:
    print("Connected: Connecting to MT5 Client")
    # sleep(3)
else:
    print("Failed to connect at account #{}, error code: {}"
          .format(account, mt5.last_error()))
   
# establish connection to MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =",mt5.last_error())
    mt5.shutdown()
    
def get_rates(curr_pair, news_time):
    news_time = news_time.minute
    rates = mt5.copy_rates_from_pos(curr_pair, mt5.TIMEFRAME_M5, 0, 5)
    rates_frame = pd.DataFrame(rates)
    rates_frame['times'] = pd.to_datetime(rates_frame['time'], unit='s')
    rates_frame['mins'] = rates_frame['times'].dt.minute
    high = rates_frame.loc[rates_frame['mins'] == news_time, 'high'].values[0]
    low = rates_frame.loc[rates_frame['mins'] == news_time, 'low'].values[0]
    last_close = rates_frame.loc[rates_frame['mins'] == news_time, 'close'].values[0]
    # high = rates_frame['high']['mins'== news_time]
    # low = rates_frame['low']['mins'== news_time]
    return high, low, last_close
        
def pend_trade(symbol, trade_type, volume, comment, price, hi, lo, sl, tp, exp_mins):
    # price = (hi+lo)/2
    if trade_type == "Buy":
        trade_action = mt5.ORDER_TYPE_BUY_LIMIT if mt5.symbol_info_tick(symbol).ask > price else mt5.ORDER_TYPE_BUY_STOP
    elif trade_type == "Sell":
        trade_action = mt5.ORDER_TYPE_SELL_LIMIT if mt5.symbol_info_tick(symbol).bid < price else mt5.ORDER_TYPE_SELL_STOP
    # trade_action = mt5.ORDER_TYPE_BUY_LIMIT if trade_type == "Buy" else mt5.ORDER_TYPE_SELL_LIMIT
    # print('trade action: ', trade_action)
    point = mt5.symbol_info(symbol).point
    sl_val = 20
    exp_time = datetime.datetime.fromtimestamp(mt5.symbol_info(symbol).time)
    time_diff = datetime.datetime.timestamp(exp_time + datetime.timedelta(minutes=exp_mins))
    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": volume,
        "type": trade_action,
        "price": price,
        "deviation": 10,
        "sl": price - sl if trade_type == "Buy" else price + sl, #lo - (sl_val * point) if trade_type == "Buy" else hi + (sl_val * point),
        "tp": price + tp if trade_type == "Buy" else price - tp, #lo if trade_type == "Sell" else hi,
        "magic": 123,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_SPECIFIED,
        "expiration": round(time_diff),
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    try:
        # print(request)
        result = mt5.order_send(request)
        result.retcode == mt5.TRADE_RETCODE_DONE
        print(f"Pending trade: {symbol}, {volume} lots, {'Buy' if trade_type == 'Buy' else 'Sell'}")
    except Exception as e:
        print('E1b: ', e)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to Pend trade for {symbol}: {result.retcode}")
        pass

# CONDITIONS TO PLACE TRADES FOR VARIOUS PAIRS  
# trade_time = '03:35pm'
trade_mins = 5
# news_time  = '12:37pm'
tz = pytz.timezone('Europe/Nicosia')
mt5_now = datetime.datetime.now(tz) 

event_time = datetime.datetime.strptime(news_time, "%I:%M%p").time()
event_time = datetime.datetime.combine(mt5_now.date(), event_time)
event_time = tz.localize(datetime.datetime.combine(datetime.datetime.today(), event_time.time()))

trade_time =  event_time + datetime.timedelta(minutes=trade_mins)

if trade_time > datetime.datetime.now(tz):
    print('Eventime: ', event_time, ' || Tradetime: ', trade_time)
    print('Nowtime: ', datetime.datetime.now(tz))
    print('time to wait: ', (trade_time - (datetime.datetime.now(tz) - datetime.timedelta(seconds=2))).total_seconds(), ' seconds')
    time.sleep((trade_time - (datetime.datetime.now(tz) - datetime.timedelta(seconds=3))).total_seconds())
    # time.sleep(30)
# XAUUSD
for pair in pairs:
    hi, lo, close_price = get_rates(pair, trade_time)
    sl = 10
    tp = 30
    exp_mins = 10
    if news_result == 0: # bad for usd, buy xauusd
        close_price = close_price + 1
        pend_trade(pair, 'Buy', 1.0, 'auto CPI', close_price, hi, lo, sl, tp, exp_mins)
    elif news_result == 1: # good for usd, sell xauusd
        close_price = close_price - 1
        pend_trade(pair, 'Sell', 1.0, 'auto CPI', close_price, hi, lo, sl, tp, exp_mins)
    
    time.sleep(3)


