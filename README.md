# USD CPI News Trading Bot for MetaTrader 5

This Python script automates trading of the USD Consumer Price Index (CPI) news event using the MetaTrader 5 platform. It places pending orders (Buy or Sell) on selected forex pairs based on whether the reported CPI figure is considered "good" (USD positive) or "bad" (USD negative) for the US Dollar.

The bot waits until shortly after the news release, reads the first few minutes of price action to determine an entry level, and then places a pending order with a predefined stop loss and take profit.

> **⚠️ Disclaimer**: This software is for educational and research purposes only. Trading forex and CFDs carries a high level of risk and may not be suitable for all investors. Never trade with money you cannot afford to lose. The author assumes no responsibility for any financial losses incurred while using this script.

## Features

- Connects to a local MetaTrader 5 terminal.
- Waits until a user‑specified news time + a configurable delay before acting.
- Fetches the 5‑minute candles around the news moment to obtain the high, low, and close prices.
- Places a **Buy Limit/Stop** or **Sell Limit/Stop** order depending on the news outcome.
- Orders include a fixed stop loss and take profit, and expire after a set number of minutes.
- Supports multiple symbols (e.g., XAUUSD, EURUSD, GBPUSD) via a list.

## Requirements

- Python 3.7+
- MetaTrader 5 terminal installed (e.g., IC Markets, FxPro)
- Python packages:
  - `MetaTrader5`
  - `pandas`
  - `pytz`

Install the required packages with:

```bash
pip install MetaTrader5 pandas pytz
```

## Configuration

Before running the script, you **must** edit the following variables inside the file:

| Variable       | Description                                                                                  |
|----------------|----------------------------------------------------------------------------------------------|
| `news_result`  | 1 = Good news (USD positive), 0 = Bad news (USD negative). Set this manually before run.    |
| `news_time`    | The time of the news release as a string, e.g., `'3:30pm'`.                                 |
| `pairs`        | List of symbols to trade, e.g., `['XAUUSD', 'EURUSD']`.                                     |
| `trade_mins`   | Minutes after the news time to place the pending order (e.g., `5`).                         |
| `sl`           | Stop loss in points (e.g., `10`).                                                            |
| `tp`           | Take profit in points (e.g., `30`).                                                          |
| `exp_mins`     | Order expiration in minutes after placement.                                                 |



## How It Works

1. **Connection** – The script initializes and logs into the MT5 terminal.
2. **Timing** – It calculates the exact datetime of the news event in the terminal’s timezone (Europe/Nicosia in the example). It then sleeps until the specified `trade_time` (news time + `trade_mins`).
3. **Fetching Rates** – Once the trade time is reached, it calls `get_rates()` to retrieve the last five 5‑minute candles. From these, it extracts the high, low, and close of the candle that corresponds to the news minute.
4. **Order Placement** – Based on `news_result`:
   - If `news_result == 0` (bad for USD → USD weak) → place a **Buy** pending order.
   - If `news_result == 1` (good for USD → USD strong) → place a **Sell** pending order.
   The entry price is set slightly away from the close price (±1 point) to avoid being filled immediately. The stop loss and take profit are absolute price levels calculated from the entry.
5. **Pending Order** – The order is placed with type `ORDER_TIME_SPECIFIED` and expires after `exp_mins` minutes.

## Usage

1. Configure the inputs (`news_result`, `news_time`, `pairs`, etc.) according to the upcoming CPI release.
2. Run the script **before** the news time (e.g., a few minutes early).
3. The script will wait and then automatically place the pending orders.
4. Monitor your MT5 platform to see the orders and manage them if necessary.

Example:

```bash
python cpi_news_trader.py
```

## Important Notes

- The script uses a hardcoded timezone (`Europe/Nicosia`). Make sure this matches your broker’s server time. Incorrect timezone will cause the bot to act at the wrong moment.
- The entry price logic (`close_price ± 1`) is simplistic. You may want to adjust this based on your own strategy or replace it with a more sophisticated algorithm.
- The script does **not** automatically detect whether the news was good or bad; you must set `news_result` manually. For a fully automated version, you would need a news feed API.
- Always test in a demo account before using real money.
- The script places market‑if‑touched orders (Buy Limit/Stop or Sell Limit/Stop). The actual order type (LIMIT vs STOP) is chosen based on whether the entry price is above or below the current market price – this logic can be refined.

## Potential Improvements

- Read credentials from environment variables.
- Add support for automatic news sentiment detection via RSS or economic calendar APIs.
- Use a configuration file (YAML/JSON) for all parameters.
- Implement logging instead of `print()` statements.
- Add error handling for missing candles or network issues.
- Allow dynamic lot sizing based on account balance or risk percentage.

## License

This project is open source and available under the [MIT License](LICENSE).

---

**Happy trading, and always manage your risk!**
