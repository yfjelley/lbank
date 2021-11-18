import ccxt
from datetime import datetime
import logging
import traceback
import os
import random
import time
lots = '1000|10000'
loop = "3|10"

api_key = "516ab98d-271b-4499-b4ee-eb1772cf3773"
secret_key = "MIICdQIBADANBgkqhkiG9w0BAQEFAASCAl8wggJbAgEAAoGBAK/qIg4o0Rl8MLcEX68DzuEdC+jIkjEVLJtrzsW75myJKYdmDPK8mp0m0DZGwHWGDfVxYvARuAdaXeJguHSPFcXHMSirPQ1ZsnTFd1NxqoVhmpOy56iXHd4BjTuybQ4U1v9BauyxZXZFeZSBuqUAsDo9JxMsVVrc88uAggtzEPddAgMBAAECgYAo+37blZ7BNTGUMayo9VYpE79GiBOm46v0uXT+k/vmpT3LkXbKxi2vFu/C9VC5EHYIDFZkX3xkGiVtK+NNJFiJytbXPHCZsJXS1kI2wZ2CpmPjxmLQZpdnV71VJMeURQRsCIEeYFggsI3k2QR3u+SSLAiCfow5CIOFV2JlY/KYgQJBAPpXIH6Ei4rNXuhHJMN4tVcA9FwxMPmxRFi+9eRHJr3stlWsPZdn1lg3fl0g6y30tyoOwfnXHDB1yniOqI6Ie5UCQQCz5EIzbijbCtrGgGENOds+VZQqzn+BZJYvqz+IUVis0XOx6aBjlv4lfDYV9SCiCSR/f+U7os3aOTpTaDTYMVqpAkAjU2giclG+pHxgCqoFa2Mrg9b3q3ldwsYCP/Ay5ldxNZYFQOjwFJcKm8oZGiwVsBKovKxitRglPnnzyS2/70KBAkA7NQtc5groXSA4aRSIR9yTHZOQqzpoGfUcZ16XvT5UUvOjQOObI50uNT2P6If/DMdId425HRJnmqJJxWhvJ39RAkB7g7p4xCPIohtIFptWWtIpDaMTMA6COCH3CECaJLiLZ4zrLw54+/DDyPAfCeUITebDlXKxQ5S9Biqqmzgl2hP2"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(filename)s - %(funcName)s - [%(levelname)s] - %(message)s',
    datefmt='%y-%b-%d %H:%M:%S',
    filename='./auto_trader.log',
    filemode='a',
    level=logging.INFO
)


class AutoTrader:
    def __init__(self):
        self.api_key = api_key
        self.secret_key = secret_key
        self.symbol = 'DBC/USDT'

        self.loop = [float(item) for item in loop.split('|')]
        # 每次挂单数量
        self.lots = [float(item) for item in lots.split('|')]
        self.exchange_market = ccxt.lbank({
            'apiKey': self.api_key,
            'secret': self.secret_key,
            'enableRateLimit': True,
            'options': {
                'createMarketBuyOrderRequiresPrice': False
            },
            'proxies': {'https': "http://127.0.0.1:51330", 'http': "http://127.0.0.1:51330"}
        })


    def trade(self):
        while True:
            order_book = self.exchange_market.fetch_order_book(self.symbol)

            amount = random.randint(self.lots[0], self.lots[1])
            price = int(random.uniform(order_book['bids'][0][0], order_book['asks'][0][0]) *pow(10, 6))/pow(10, 6)
            print(amount, price)
            ret = self.exchange_market.create_limit_buy_order(
                symbol=self.symbol, amount=amount, price=price
            )
            ret = self.exchange_market.create_limit_sell_order(
                symbol=self.symbol, amount=amount, price=price
            )
            delay = random.randint(self.loop[0], self.loop[1])
            time.sleep(delay)


if __name__ == '__main__':
    t = AutoTrader()
    t.trade()
