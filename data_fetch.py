#!/usr/bin/env python3
'''
data_fetch.py

Module to fetch historical S&P 500 market data from Yahoo Finance using yfinance.
'''

import os
import yfinance as yf
import pandas as pd
from typing import Dict, Any


def get_yf_data(start_date: str = '2000-01-01', end_date: str = None, save_csv: bool = False,
                   yf_ticker: str = '^GSPC') -> Dict[str, Any]:
    '''
    Fetches historical S&P 500 data from Yahoo Finance.

    Parameters:
        start_date (str): Date in 'YYYY-MM-DD' format for the start of data.
        end_date (str): Date in 'YYYY-MM-DD' format for the end of data. If None, uses today's date.
        save_csv (bool): Whether to save the DataFrame to a CSV file.
        csv_filename (str): Filename for saving the CSV.

    Returns:
        pd.DataFrame: Historical data with dates as index.
    '''
    try:
        asset = yf.Ticker(yf_ticker)
        info = asset.info
        assetname = info.get("longName") or info.get("shortName") or yf_ticker
    except Exception as e:
        print(f'Ticker "{yf_ticker}" not found.')

        return {'Error': e}

    csv_filename = f'{assetname}_data.csv'
    df = asset.history(start=start_date, end=end_date)
    df = df.reset_index()  # so that Date becomes a column

    if save_csv:
        df.to_csv(csv_filename, index=False)

    return {'name': assetname, 'historics': df}


if __name__ == '__main__':
    # Example: fetch data from 2000 to today and save it to CSV.
    result = get_yf_data(save_csv=True)
    if 'Error' in result.keys():
        print(result['Error'])
    else:
        print(f'Downloaded {len(result['historics'])} rows of data.')
