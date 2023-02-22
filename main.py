from ibapi.client import EClient
from ibapi.wrapper import EWrapper
import subprocess
import json
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time
import csv
import yfinance as yf

def run_loop():
    app.run()

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextorderId = None

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        print('The next valid order id is: ', self.nextorderId)

    def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId,
                    whyHeld, mktCapPrice):
        print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining,
              'lastFillPrice', lastFillPrice)

    def openOrder(self, orderId, contract, order, orderState):
        print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action,
              order.orderType, order.totalQuantity, orderState.status)

    def execDetails(self, reqId, contract, execution):
        print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId,
              execution.orderId, execution.shares, execution.lastLiquidity)

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

atr_stop_loss = get_current_price('ES=F') - last_atr
print(atr_stop_loss)


# Create an instance of the IBapi class
app = IBapi()
app.connect('127.0.0.1', 4002, 123)
app.nextorderId = None

# Start the socket in a thread
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

# Check if the API is connected via orderid
while True:
    if isinstance(app.nextorderId, int):
        print('connected')
        break
    else:
        print('waiting for connection')
        time.sleep(1)

# Listen for incoming webhook data
while True:
    url = "https://api.pipedream.com/sources/dc_2Eu7X4x/sse"
    auth_header = "Authorization: Bearer 360d90f4549def76cc1e370e71832b67"
    curl_cmd = ["curl", "-s", "-N", "-H", auth_header, url]
    proc = subprocess.Popen(curl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in proc.stdout:
    # Ignore any SSE data that isn't JSON-formatted
     if line.startswith(b"data: {"):
        # Strip the "data: " prefix from the line and parse the JSON-formatted data
        event_data = json.loads(line[6:])
        # Process the event data as needed
        data = event_data
        body = data['event']['body']
        symbol_fields = body.split(',')

        # Open the CSV file in "append" mode
        with open('filename.csv', 'a', newline='') as file:
            # Create a CSV writer object
            writer = csv.writer(file)
            # Write a new row to the CSV file
            row = [symbol_fields[0],
                   symbol_fields[1],
                   symbol_fields[2],
                   symbol_fields[3],
                   symbol_fields[4],
                   symbol_fields[5],
                   symbol_fields[6],
                   symbol_fields[7]]
            writer.writerow(row)

        with open('filename.csv', 'r') as file:
            csv_reader = csv.reader(file)
            data = list(csv_reader)

        symbol = 'AAPL'
        ticker = yf.Ticker(symbol)
        latest_price = ticker.info['regularMarketPrice']
        print(latest_price)

        second_to_last_row = data[-2]
        if symbol_fields[6] == second_to_last_row[6]:
            continue
        else:
            def options_order_1(symbol):
                # Create SELL Contract Object
                contract_1 = Contract()
                contract_1.symbol = second_to_last_row[0]
                contract_1.secType = second_to_last_row[1]
                contract_1.exchange = second_to_last_row[2]
                contract_1.currency = second_to_last_row[3]
                contract_1.lastTradeDateOrContractMonth = second_to_last_row[4]
                contract_1.strike = second_to_last_row[5]
                contract_1.right = second_to_last_row[6]
                contract_1.multiplier = second_to_last_row[7]
                return contract_1

            # Define the BUY Contract and Order Objects
            def options_order_2(symbol):
                # Create BUY Contract Object
                contract_2 = Contract()
                contract_2.symbol = symbol_fields[0]
                contract_2.secType = symbol_fields[1]
                contract_2.exchange = symbol_fields[2]
                contract_2.currency = symbol_fields[3]
                contract_2.lastTradeDateOrContractMonth = symbol_fields[4]
                contract_2.strike = symbol_fields[5]
                contract_2.right = symbol_fields[6]
                contract_2.multiplier = symbol_fields[7]
                return contract_2

            # Create SELL Order Object
            contract_1 = options_order_1(second_to_last_row[0])
            order_1 = Order()
            order_1.action = 'SELL'
            order_1.totalQuantity = 1
            order_1.orderType = 'MKT'
            order_1.eTradeOnly = ''
            order_1.firmQuoteOnly = ''
            # Place the SELL Order
            app.placeOrder(app.nextorderId, contract_1, order_1)

            # Wait for the first order to be filled before placing the second order
            time.sleep(3)

            # Place BUY order
             # Create BUY Order Object
            contract_2 = options_order_2(symbol_fields[0])
            order_2 = Order()
            order_2.action = 'BUY'
            order_2.totalQuantity = 1
            order_2.orderType = 'MKT'
            order_2.eTradeOnly = ''
            order_2.firmQuoteOnly = ''
            # Place the BUY Order
            app.nextorderId += 1
            app.placeOrder(app.nextorderId, contract_2, order_2)
            app.nextorderId += 1
        time.sleep(3)