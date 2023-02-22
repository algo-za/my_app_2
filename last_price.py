import yfinance as yf
import pandas as pd

# Set initial values for ATR and trailing stop loss
atr_period = 14
atr_multiplier = 3
symbol = "SPY"
stock = yf.Ticker(symbol)
hist = stock.history(period="1mo")
hist["TR"] = hist.apply(lambda row: max(row["High"] - row["Low"], abs(row["High"] - pd.Series(row["Close"]).shift())),
                        axis=1)
hist["ATR"] = hist["TR"].rolling(atr_period).mean()
prev_close = hist["Close"][0]
trailing_stop = prev_close - (hist["ATR"][atr_period - 1] * atr_multiplier)

# Loop through each price update and track the trailing stop loss
for i in range(atr_period, len(hist)):
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
