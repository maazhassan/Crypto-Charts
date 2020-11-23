import os
import shutil
import numpy as np
import pandas as pd
import pickle
import quandl
import requests
from datetime import datetime, date
import plotly.graph_objs as go


def get_quandl_data(quandl_id):
    cache_path = '{}.pkl'.format(quandl_id).replace('/','-')
    cache_path = 'data/' + cache_path
    try:
        f = open(cache_path, 'rb')
        df = pickle.load(f)   
        print('Loaded {} from cache'.format(quandl_id))
    except (OSError, IOError) as e:
        print('Downloading {} from Quandl'.format(quandl_id))
        df = quandl.get(quandl_id, returns="pandas")
        df.to_pickle(cache_path)
        print('Cached {} at {}'.format(quandl_id, cache_path))
    return df


# Download and cache JSON data, return as a dataframe.
def get_json_data(json_url, filename):
    cache_path = 'data/' + filename
    try:        
        f = open(cache_path, 'rb')
        df = pickle.load(f)   
        print('Loaded {} from cache'.format(json_url))
    except (OSError, IOError) as e:
        print('Downloading {}'.format(json_url))
        df = pd.read_json(json_url)
        df.to_pickle(cache_path)
        print('Cached {} at {}'.format(json_url, cache_path))
    return df


# Retrieve cryptocurrency data from poloniex
def get_polo_data(base_polo_url, poloniex_pair, start, end, period):
    json_url = base_polo_url.format(poloniex_pair, start, end, period)
    data_df = get_json_data(json_url, poloniex_pair)
    data_df = data_df.set_index('date')
    return data_df


def merge_dfs_on_column(dataframes, labels, col):
    series_dict = {}
    for index in range(len(dataframes)):
        series_dict[labels[index]] = dataframes[index][col]
        
    return pd.DataFrame(series_dict)


def update_exchange_rate():
    r = requests.get('https://api.exchangeratesapi.io/latest?base=USD')
    r = r.json()
    rate = str(r['rates']['CAD'])
    f = open('data/rate.txt', 'w')
    f.write(rate)
    f.close()


def update_date():
    today = date.today()
    f = open('data/date.txt', 'w')
    f.write(str(today))
    f.close()


def read_exchange_rate():
    f = open('data/rate.txt', 'r')
    rate = float(f.readline())
    return rate


def check_date():
    f = open('data/date.txt', 'r')
    prev = f.readline()
    if date.fromisoformat(prev) != date.today():
        folder = os.path.join(os.path.dirname(__file__), 'data/')
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
        
        update_exchange_rate()
        update_date()
    

def create_btc_dataset():
    exchanges = ['KRAKEN', 'BITFLYER', 'BITSTAMP', 'LAKE', 'CEX']
    exchange_data = {}
    rate = read_exchange_rate()

    for exchange in exchanges:
        exchange_code = 'BCHARTS/{}USD'.format(exchange)
        btc_exchange_df = get_quandl_data(exchange_code)
        btc_exchange_df['Weighted Price'] = btc_exchange_df['Weighted Price'] * rate
        exchange_data[exchange] = btc_exchange_df

    # Merge the datasets, remove 0 values, and calculate the average
    btc_cad_datasets = merge_dfs_on_column(list(exchange_data.values()), list(exchange_data.keys()), 'Weighted Price')
    btc_cad_datasets.replace(0, np.nan, inplace=True)
    btc_cad_datasets['price_cad'] = btc_cad_datasets.mean(axis=1)
    return btc_cad_datasets


def create_alt_dataset(code, bitcoin_data):
    base_polo_url = 'https://poloniex.com/public?command=returnChartData&currencyPair={}&start={}&end={}&period={}'
    start = int(datetime.strptime('2015-01-01', '%Y-%m-%d').timestamp())
    end = int(datetime.now().timestamp())
    period = 86400
    coinpair = 'BTC_{}'.format(code)
    altcoin_data = get_polo_data(base_polo_url, coinpair, start, end, period)
    altcoin_data['price_cad'] = altcoin_data['weightedAverage'] * bitcoin_data['price_cad']
    return altcoin_data


def graph_single(dataset):
    btc_trace = go.Scatter(x=dataset.index, y=dataset['price_cad'])
    fig = go.Figure(btc_trace)
    fig.show()


def main():
    check_date()
    bitcoin_df = create_btc_dataset()

    choice = int(input("\nType 1 for bitcoin and 2 for any altcoin (-1 to exit): "))

    while choice != -1:
        if choice == 1:
            graph_single(bitcoin_df)
        elif choice == 2:
            altcode = str(input("Enter altcoin code: "))
            try:
                altcoin_df = create_alt_dataset(altcode, bitcoin_df)
                graph_single(altcoin_df)
            except:
                print("\nInvalid code.")
        else:
            print("\nInvalid choice.")

        choice = int(input("\nType 1 for bitcoin and 2 for any altcoin (-1 to exit): "))

main()
