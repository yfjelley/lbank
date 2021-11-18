import ccxt
import yaml
import logging
from datetime import datetime
import os
import pandas as pd
import traceback
import sys

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(filename)s - %(funcName)s - [%(levelname)s] - %(message)s',
    datefmt='%y-%b-%d %H:%M:%S',
    filename='./auto_trader.log',
    filemode='a',
    level=logging.INFO
)


def load_config():
    logging.info('Try to fetch local configuration from ./config.yaml')
    if os.path.exists('./config.yaml'):
        cfg_file = open('./config.yaml', 'r')
        config = yaml.safe_load(cfg_file)
        logging.info('Basic config loaded')
        cfg_file.close()

        return config

    else:
        logging.error('!!! ./config.yaml not found. Run config_generator.py first')

        return None


def timestamp_to_datetime(timestamp):
    return datetime.strftime(datetime.fromtimestamp(timestamp), '%Y-%m-%d %H:%M:%S')


def get_now_datetime():
    return datetime.strftime(datetime.now(), '%Y-%m-%d_%H_%M_%S')


def get_decision(base_symbol, trade_symbol_list, last, alpha_change, beta_change):
    alpha_symbol = trade_symbol_list[0]
    beta_symbol = trade_symbol_list[1]
    if alpha_change > beta_change:
        if alpha_change > 0:
            return alpha_symbol
        else:
            return base_symbol
    elif alpha_change <= beta_change:
        if beta_change > 0:
            return beta_symbol
        else:
            return base_symbol

    return last


def get_kline_dict(exchange_market, base_symbol, time_frame, size, symbol_list):
    def resolve_timeframe_to_m(timeframe):
        if timeframe[-1] == 'm':
            return int(timeframe[:-1])
        elif timeframe[-1] == 'h':
            return int(timeframe[:-1]) * 60
        elif timeframe[-1] == 'd':
            return int(timeframe[:-1]) * 24 * 60

        return None

    def get_kline(market, _symbol, _time_frame, size):
        if market.name == 'Huobi':
            return market.fetch_ohlcv(symbol=_symbol, timeframe=_time_frame, limit=size + 1)
        elif market.name == 'LBank':
            # Millisecond
            now_timestamp = int(datetime.now().timestamp() * 1000)
            now_timestamp = now_timestamp - now_timestamp % 300000
            since = now_timestamp - size * resolve_timeframe_to_m(time_frame) * 60000
            return market.fetch_ohlcv(symbol=_symbol, timeframe=_time_frame, since=since)

        raise Exception('No market is designated.')

    kline_dict = {}
    for symbol in symbol_list:
        kline_list = get_kline(exchange_market, symbol + '/' + base_symbol, time_frame, size)[:-1]
        last_kline_list = get_kline(exchange_market, symbol + '/' + base_symbol, time_frame, size + 1)[:-2]
        dt = pd.DataFrame(columns=['datetime', 'open', 'close', 'change', 'consecutive_change'])
        for first, second in zip(last_kline_list, kline_list):
            dt = dt.append(
                {
                    'datetime': timestamp_to_datetime(second[0] // 1000),
                    'open': second[1],
                    'close': second[4],
                    'change': (second[4] - second[1]) / second[1],
                    'consecutive_change': (second[4] - first[4]) / first[4]
                },
                ignore_index=True
            )

        dt['datetime'] = pd.to_datetime(dt['datetime'])
        dt.sort_values(by='datetime', ascending=True, inplace=True)
        dt.reset_index(drop=True, inplace=True)
        kline_dict[symbol] = dt
        folder_path = './threshold_csv/'
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
            logging.info('Mkdir {}'.format(folder_path))
        dt.to_csv(folder_path + '{}_ohlcv.csv'.format(symbol), index=False)

    return kline_dict


if __name__ == "__main__":
    try:
        logging.info('********** Start backtester **********')
        config = load_config()
        logging.info('Try to fetch local configuration from ./config.yaml')
        if not config:
            raise Exception('./config.yaml not found. Run config_generator.py first')

        exchange_symbol = config['exchange']
        api_key = config['api_key']
        secret_key = config['secret_key']
        base_symbol = config['base_symbol']
        alpha_symbol = config['alpha_symbol']
        beta_symbol = config['beta_symbol']
        alpha_symbol_base = alpha_symbol + '/' + base_symbol
        beta_symbol_base = beta_symbol + '/' + base_symbol
        alpha_long_symbol = config['alpha_long_symbol']
        beta_long_symbol = config['beta_long_symbol']
        # alpha_short_symbol = config['alpha_short_symbol']
        # beta_short_symbol = config['beta_short_symbol']
        kline_list = [alpha_symbol, beta_symbol]
        time_frame = config['time_frame']
        # fluctuation_section_length = int(config['fluctuation_section_length'])
        # shift_threshold = int(config['shift_threshold'])
        window_size = int(config['window_size'])
        # sample_size = eval(config['sample_size'])

        symbol_list = [
            alpha_symbol,
            beta_symbol,
            alpha_long_symbol,
            beta_long_symbol,
        ]
        trade_symbol_list = [
            alpha_long_symbol,
            beta_long_symbol,
        ]

        logging.info('Generating {}'.format(exchange_symbol))
        if exchange_symbol == 'huobi_pro':
            logging.info('Generating huobi_pro')
            exchange_market = ccxt.huobipro({
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {
                    'createMarketBuyOrderRequiresPrice': False
                }
            })
        elif exchange_symbol == 'lbank':
            logging.info('Generating lbank')
            exchange_market = ccxt.lbank({
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
            })
        else:
            exchange_market = None

        if len(sys.argv) > 1:
            size = sys.argv[1]
            if len(sys.argv) > 2:
                window_size = int(sys.argv[2])
        else:
            size = input('Input size of backtest(1152):')
        if not size:
            size = '1152'
        size = int(size)
        if exchange_market.name == 'Huobi':
            size = min(size, 2000 - 4)
        else:
            size = min(size, 1000 - 4)

        logging.info('Backtest on {} items of history data'.format(size))
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)

        kline_test_dict = get_kline_dict(exchange_market, base_symbol, time_frame, window_size + 1, symbol_list)
        kline_dict = get_kline_dict(exchange_market, base_symbol, time_frame, size + 1, symbol_list)
        kline_dict[beta_symbol]['change'] = -kline_dict[beta_symbol]['change']
        kline_dict[beta_symbol]['consecutive_change'] = -kline_dict[beta_symbol]['consecutive_change']
        kline_dict[beta_symbol]['close'] = -kline_dict[beta_symbol]['close']
        logging.info('{}'.format(len(kline_dict[alpha_symbol])))
        # logging.info(kline_dict)
        init_balance = 100.0
        balance_list = [init_balance]
        hold_list = [base_symbol]
        fee_rate = 0.001
        df_columns = [
            'datetime',
            alpha_symbol,
            alpha_symbol + '_c_change',
            beta_symbol,
            beta_symbol + '_c_change',
            alpha_long_symbol,
            alpha_long_symbol + '_c_change',
            beta_long_symbol,
            beta_long_symbol + '_c_change',
            'hold',
            'balance'
        ]
        overall_df = pd.DataFrame(columns=df_columns)

        for i in range(window_size):
            logging.info('{} / {}'.format(i, size))
            row = [
                kline_dict[alpha_symbol].iloc[i]['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                kline_dict[alpha_symbol].iloc[i]['close'],
                kline_dict[alpha_symbol].iloc[i]['consecutive_change'],
                kline_dict[beta_symbol].iloc[i]['close'],
                kline_dict[beta_symbol].iloc[i]['consecutive_change'],
                kline_dict[alpha_long_symbol].iloc[i]['close'],
                kline_dict[alpha_long_symbol].iloc[i]['consecutive_change'],
                kline_dict[beta_long_symbol].iloc[i]['close'],
                kline_dict[beta_long_symbol].iloc[i]['consecutive_change'],
                base_symbol,
                100.0
            ]
            overall_df = overall_df.append(pd.DataFrame([row], columns=df_columns))

        for i in range(window_size, size):
            logging.info('{} / {}'.format(i, size))
            kline_dict_slice = {}
            current_kline_dict = {}
            selected_symbol = None
            hold_symbol = hold_list[-1]
            if hold_symbol in [alpha_long_symbol]:
                selected_symbol = alpha_symbol
                selected_symbol_base = alpha_symbol_base
            elif hold_symbol in [beta_long_symbol]:
                selected_symbol = beta_symbol
                selected_symbol_base = beta_symbol_base
            elif hold_symbol == base_symbol:
                selected_symbol = beta_symbol
                selected_symbol_base = beta_symbol_base

            last_row = overall_df.iloc[-1]
            last_hold = hold_list[-1]
            alpha_change = kline_dict[alpha_symbol].iloc[i - 1 - window_size:i - 1]['consecutive_change'].sum()
            beta_change = kline_dict[beta_symbol].iloc[i - 1 - window_size:i - 1]['consecutive_change'].sum()
            curr_hold = get_decision(
                base_symbol=base_symbol,
                trade_symbol_list=trade_symbol_list,
                last=hold_list[-1],
                alpha_change=alpha_change,
                beta_change=beta_change,
            )
            hold_list.append(curr_hold)

            curr_balance = balance_list[-1]
            if last_hold == curr_hold:
                if curr_hold == base_symbol:
                    pass
                else:
                    curr_balance *= (1 + kline_dict[curr_hold].iloc[i]['consecutive_change'])
            else:
                if curr_hold in trade_symbol_list and last_hold in trade_symbol_list:
                    curr_balance *= (1 - fee_rate) * (1 - fee_rate) \
                                    * (1 + kline_dict[curr_hold].iloc[i]['consecutive_change'])
                else:
                    curr_balance *= (1 - fee_rate)
                    if curr_hold in trade_symbol_list:
                        curr_balance *= (1 + kline_dict[curr_hold].iloc[i]['consecutive_change'])
            balance_list.append(curr_balance)
            logging.info('Current hold: {}, Current balance: {}'.format(curr_hold, curr_balance))

            curr_row = pd.DataFrame([[
                kline_dict[alpha_symbol].iloc[i]['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                kline_dict[alpha_symbol].iloc[i]['close'],
                kline_dict[alpha_symbol].iloc[i]['consecutive_change'],
                kline_dict[beta_symbol].iloc[i]['close'],
                kline_dict[beta_symbol].iloc[i]['consecutive_change'],
                kline_dict[alpha_long_symbol].iloc[i]['close'],
                kline_dict[alpha_long_symbol].iloc[i]['consecutive_change'],
                kline_dict[beta_long_symbol].iloc[i]['close'],
                kline_dict[beta_long_symbol].iloc[i]['consecutive_change'],
                curr_hold,
                curr_balance
            ]], columns=df_columns)
            overall_df = overall_df.append(curr_row)
            overall_df.reset_index(drop=True, inplace=True)

        folder_path = './backtest.csv/'
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
            logging.info('Mkdir {}'.format(folder_path))

        file_path = folder_path + '{}_{}_{}_,window={},size={},max={},min={},backtest_balance.csv'.format(
            get_now_datetime(),
            alpha_long_symbol,
            beta_long_symbol,
            window_size,
            size,
            overall_df['balance'].max(),
            overall_df['balance'].min()
        )
        with open(file_path, 'w', newline='') as backtest_file:
            overall_df.to_csv(backtest_file, index=False)
            backtest_file.close()

        logging.info('All done. Results have been output to {}'.format(file_path))


    except:
        logging.error('!!! {}'.format(traceback.format_exc()))


