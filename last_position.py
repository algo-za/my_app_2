from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract


class MyWrapper(EWrapper):
    def position(self, account, contract, pos, avgCost):
        # This method will be called when a position update is received
        print(f"Position: {pos} {contract.symbol} @ {avgCost}")


class MyClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)


wrapper = MyWrapper()
client = MyClient(wrapper)

# Connect to the TWS or IB Gateway
client.connect("localhost", 4002, clientId=0)

# Request the current positions
client.reqPositions()

# Start the message loop to receive updates
client.run()

# Disconnect from the TWS or IB Gateway
client.disconnect()
