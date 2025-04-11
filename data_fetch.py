#!/usr/bin/env python3
'''
data_fetch.py

Module to fetch historical S&P 500 market data from Yahoo Finance using yfinance.
'''

import os
import yfinance as yf
import pandas as pd


def get_sp500_data(start_date: str = '2000-01-01', end_date: str = None, save_csv: bool = False,
                   csv_filename: str = 'sp500_data.csv') -> pd.DataFrame:
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
    # '^GSPC' is the ticker for the S&P 500
    sp500 = yf.Ticker('^GSPC')
    df = sp500.history(start=start_date, end=end_date)
    df = df.reset_index()  # so that Date becomes a column
    if save_csv:
        df.to_csv(csv_filename, index=False)
    return df


if __name__ == '__main__':
    # Example: fetch data from 2000 to today and save it to CSV.
    df = get_sp500_data(save_csv=True)
    print(f'Downloaded {len(df)} rows of data.')
