# -*- coding: utf-8 -*-
"""
Created on Wed Jun 25 09:54:10 2025
!!!!!!!!!!!!!!!!!!!!!!!     AUD CPI AUDUSD   !!!!!!!!!!!!!!!!!!!!
Entry:
Wait 5 minutes after the news release.
Calculate delta = C_5 - O_0 (close at 5 minutes post-news minus open at news time).
If delta > 10 pips, enter a long position at O_10.
If delta < -10 pips, enter a short position at O_10.
If |delta| ≤ 10 pips, no trade is entered (to filter out noise).
Note: 1 pip in AUDUSD = 0.0001 (e.g., a move from 0.6500 to 0.6501 is 1 pip).
Take Profit (TP):
Long trade: TP = O_10 + 30 pips.
Short trade: TP = O_10 - 30 pips.
Stop Loss (SL):
Long trade: SL = O_10 - 15 pips.
Short trade: SL = O_10 + 15 pips.
Exit:
Monitor each 5-minute candle from t=10 to t=70 (60 minutes after entry).
For a long trade:
If H_t ≥ TP, exit at TP.
If L_t ≤ SL, exit at SL.
If neither is hit by t=70, close at C_70.
For a short trade:
If L_t ≤ TP, exit at TP.
If H_t ≥ SL, exit at SL.
If neither is hit by t=70, close at C_70.
Lot Size: 1 standard lot (100,000 units of AUDUSD).
Profit/loss in pips is calculated, convertible to USD (1 pip ≈ 10 USD per lot, depending on exchange rate).
Risk: Maximum loss per trade is 15 pips (SL), or 150 USD per lot at current rates.
@author: jbriz
"""
import MetaTrader5 as mt5
import time
import datetime
import pandas as pd
import pytz


# INPUTS
news_result = 0 # 1 - Good/green, 0 - Bad/red
news_time  = '5:06pm' #'3:30pm'

pairs = ['AUDUSD'] #,  'GBPUSD', 'EURUSD', 'USDJPY', 'AUDUSD', 'USDCAD']

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
    rates = mt5.copy_rates_from_pos(curr_pair, mt5.TIMEFRAME_M1, 0, 15)
    rates_frame = pd.DataFrame(rates)
    rates_frame['times'] = pd.to_datetime(rates_frame['time'], unit='s')
    rates_frame['mins'] = rates_frame['times'].dt.minute
    news_open = rates_frame.loc[rates_frame['mins'] == news_time, 'open'].values[0]
    high = rates_frame.loc[rates_frame['mins'] == news_time, 'high'].values[0]
    low = rates_frame.loc[rates_frame['mins'] == news_time, 'low'].values[0]
    last_close = rates_frame.loc[rates_frame['mins'] == news_time+5, 'close'].values[0]
    # high = rates_frame['high']['mins'== news_time]
    # low = rates_frame['low']['mins'== news_time]
    return high, low, last_close, news_open

def open_trade(symbol, trade_type, volume, comment, sl, tp):
    trade_action = mt5.ORDER_TYPE_BUY if trade_type == "Buy" else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if trade_type == "Buy" else mt5.symbol_info_tick(symbol).bid
    point = mt5.symbol_info(symbol).point
    # sl_val = 80 # if impact == 'L' else 120
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": trade_action,
        "price": price,
        "deviation": 10,
              
        # "tp": price * 1.0005 if trade_type == "Buy" else price * 0.9995, # 0.05%
        "sl": price - (sl * point) if trade_type == "Buy" else price + (sl * point),
        # "sl": price * 0.999 if trade_type == "Buy" else price * 1.001, # 0.1%
            
        "tp": price - (tp * point) if trade_type == "Sell" else price + (tp * point),
        "magic": 123,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    try:
        result = mt5.order_send(request)
        result.retcode == mt5.TRADE_RETCODE_DONE
        print(f"Opened trade: {symbol}, {volume} lots, {'Buy' if trade_type == 'Buy' else 'Sell'}")
    except Exception as e:
        print('E1: ', e)
        # if result.retcode != mt5.TRADE_RETCODE_DONE:
        #     print(f"Failed to open trade for {symbol}: {result.retcode}")
        pass
      
def close_position(position):
    
        tick = mt5.symbol_info_tick(position.symbol)
    
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_BUY if position.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL,
            "price": tick.ask if position.type == 1 else tick.bid,  
            "deviation": 20,
            "magic": 100,
            "comment": "python script close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
    
        result = mt5.order_send(request)
        print("CLOSE TRADE DONE - ", result.request.symbol)
        return result

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
close_mins = 7
# news_time  = '12:37pm'
tz = pytz.timezone('Europe/Nicosia')
mt5_now = datetime.datetime.now(tz) 

event_time = datetime.datetime.strptime(news_time, "%I:%M%p").time()
event_time = datetime.datetime.combine(mt5_now.date(), event_time)
event_time = tz.localize(datetime.datetime.combine(datetime.datetime.today(), event_time.time()))

trade_time =  event_time + datetime.timedelta(minutes=trade_mins)

close_time =  event_time + datetime.timedelta(minutes=close_mins)

if trade_time > datetime.datetime.now(tz):
    print('Eventime: ', event_time, ' || Tradetime: ', trade_time)
    print('Nowtime: ', datetime.datetime.now(tz))
    print('time to wait: ', (trade_time - (datetime.datetime.now(tz) - datetime.timedelta(seconds=2))).total_seconds(), ' seconds')
    time.sleep((trade_time - (datetime.datetime.now(tz) - datetime.timedelta(seconds=3))).total_seconds())
    # time.sleep(30)
    # XAUUSD
    for pair in pairs:
        hi, lo, close_price, news_open = get_rates(pair, event_time)
        point = mt5.symbol_info(pair).point
        delta = close_price - news_open
        sl = 10
        tp = 30
        exp_mins = 10
        # if news_result == 0: # bad for usd, buy xauusd
        if delta > 10 * point:
            close_price = close_price + 1
            # pend_trade(pair, 'Buy', 1.0, 'auto CPI', close_price, hi, lo, sl, tp, exp_mins)
            open_trade(pair, 'Buy', 1.0, 'auto CPI', sl, tp)
        elif delta > 10 * point: # news_result == 1: # good for usd, sell xauusd
            close_price = close_price - 1
            # pend_trade(pair, 'Sell', 1.0, 'auto CPI', close_price, hi, lo, sl, tp, exp_mins)
            open_trade(pair, 'Sell', 1.0, 'auto CPI', sl, tp)
        time.sleep(3)


if close_time > datetime.datetime.now(tz):
    
    positions = mt5.positions_get()
    for position in positions:
        close_result = close_position(position)