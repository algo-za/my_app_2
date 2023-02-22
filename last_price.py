import yfinance as yf
import pandas as pd

def request_data(symbol):
    data = yf.download(tickers=symbol, period='30d', interval='5m')
    return data

def calculate_atr(data):
    atr_period = 14
    multiplier = 2.8
    data['TR'] = data[['High', 'Low', 'Close']].diff().abs().max(axis=1).shift(1, fill_value=0)
    data['ATR'] = data['TR'].rolling(window=atr_period).mean() * multiplier
    return data

symbol_data = request_data('ES=F')
symbol_data = calculate_atr(symbol_data)
last_atr = symbol_data['ATR'].iloc[-1]
print(last_atr)

def get_current_price(symbol):
    ticker = yf.Ticker(symbol)
    todays_data = ticker.history(period='1D')
    return todays_data['Close'][0]
print(get_current_price('ES=F'))

atr_period = 14 # defining the variable atr_period
hist = symbol_data
trailing_stop = hist["Close"].iloc[atr_period - 1] - (hist["ATR"].iloc[atr_period - 1] * 3)
atr_multiplier = 3

# Loop through each price update and track the trailing stop loss
for i in range(atr_period, len(hist)):
    current_price = get_current_price('ES=F')
    symbol_data = pd.concat([symbol_data, pd.DataFrame({'Close': [current_price], 'ATR': [last_atr]})], ignore_index=True)
    symbol_data = calculate_atr(symbol_data)

    curr_close = hist["Close"][i]
    curr_atr = hist["ATR"][i]

    # Check if current price is higher than trailing stop loss
    if curr_close > trailing_stop:
        # Continue with trade
        print("Price is higher than trailing stop loss, continuing with trade")

        # Recalculate ATR and update trailing stop loss if necessary
        hist_subset = hist.iloc[i - atr_period + 1:i + 1]
        curr_atr = hist_subset["TR"].rolling(atr_period).mean().iloc[-1]
        new_trailing_stop = curr_close - (curr_atr * atr_multiplier)
        if new_trailing_stop > trailing_stop:
            trailing_stop = new_trailing_stop
            print(f"New trailing stop loss is {trailing_stop}")

    # Check if current price is lower than trailing stop loss
    elif curr_close < trailing_stop:
        # Close the position
        print("Price is lower than trailing stop loss, closing position")
        break
