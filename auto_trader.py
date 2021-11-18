import ccxt
from datetime import datetime
import logging
import traceback
import os
import random
import time
lots = '1000|10000'
loop = "3|10"


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
