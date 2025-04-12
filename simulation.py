#!/usr/bin/env python3
'''
simulation.py

Module for simulating the performance of a paired knockout certificate strategy using
historical S&P 500 data.

This version simulates two positions:
  - A long certificate (e.g. 3x long) with a knockout barrier defined as a drop 
    below a specified percentage (e.g. 10% drop from the entry price).
  - A short certificate (e.g. 3x short) with a knockout barrier defined as a rise 
    above a specified percentage (e.g. 10% rise from the entry price).

For each certificate, daily returns are compounded until the knockout barrier is hit;
if hit, the position's value becomes zero for all subsequent days.

Both positions are initiated on the same start date with an initial capital that is reduced 
by the entry cost and spread. The simulation returns a DataFrame with Date, Long Value, 
Short Value, and Combined Portfolio Value.
'''

import pandas as pd
from datetime import datetime


def simulate_pair_strategy(df: pd.DataFrame,
                           start_date: str,
                           multiplier: float = 3.0,
                           long_barrier_pct: float = 0.10,
                           short_barrier_pct: float = 0.10,
                           initial_investment: float = 100.0,
                           entry_cost: float = 5.0,
                           spread: float = 3.0) -> pd.DataFrame:
    '''
    Simulates the performance of a paired knockout certificate strategy.

    Parameters:
        df (pd.DataFrame): Historical market data containing at least 'Date', 'Close', 'High', and 'Low'.
        start_date (str): The entry date in 'YYYY-MM-DD' format.
        multiplier (float): Leverage factor (e.g. 3.0 for 3× exposure).
        long_barrier_pct (float): Knockout barrier for the long position (e.g. 0.10 for 10% drop).
        short_barrier_pct (float): Knockout barrier for the short position (e.g. 0.10 for 10% rise).
        initial_investment (float): Starting capital allocated to each certificate.
        entry_cost (float): Fixed cost to enter each position.
        spread (float): Transaction spread cost for each position.

    Returns:
        pd.DataFrame: DataFrame with columns 'Date', 'Long Value', 'Short Value', and 'Combined Value'.
    '''
    # Convert 'Date' to datetime (assume UTC) and sort the DataFrame
    df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.tz_convert(None)
    df = df.sort_values('Date').reset_index(drop=True)
    
    start_date_dt = pd.to_datetime(start_date)
    sim_df = df[df['Date'] >= start_date_dt].copy().reset_index(drop=True)
    
    if sim_df.empty:
        raise ValueError('No data available from the specified start date.')
    
    # Use the entry price from the 'Close' on the entry date
    entry_price = sim_df.iloc[0]['Close']
    
    # Deduct entry cost and spread from the initial investment for each certificate
    net_investment = initial_investment - (entry_cost + spread)
    
    # Initialize the columns for the two positions with net_investment at day 0
    sim_df['Long Value'] = 0.0
    sim_df['Short Value'] = 0.0
    sim_df['Combined Value'] = 0.0
    
    # Set knockout thresholds based on the entry price
    long_knockout_level = entry_price * (1 - long_barrier_pct)
    short_knockout_level = entry_price * (1 + short_barrier_pct)
    
    # Initialize active flags for both positions
    long_active = True
    short_active = True
    
    # Initialize the first day
    sim_df.at[0, 'Long Value'] = net_investment
    sim_df.at[0, 'Short Value'] = net_investment
    sim_df.at[0, 'Combined Value'] = net_investment * 2
    
    # Simulate day-by-day performance
    for i in range(1, len(sim_df)):
        current_close = sim_df.at[i, 'Close']
        previous_close = sim_df.at[i - 1, 'Close']
        # Calculate the daily return based on closing prices
        daily_return = (current_close / previous_close) - 1

        # For the long certificate: Use the day's low to check for knockout
        if long_active:
            if sim_df.at[i, 'Low'] <= long_knockout_level:
                sim_df.at[i, 'Long Value'] = 0.0
                long_active = False
            else:
                prev_long = sim_df.at[i - 1, 'Long Value']
                sim_df.at[i, 'Long Value'] = prev_long * (1 + multiplier * daily_return)
        else:
            sim_df.at[i, 'Long Value'] = 0.0
        
        # For the short certificate: Use the day's high to check for knockout
        if short_active:
            if sim_df.at[i, 'High'] >= short_knockout_level:
                sim_df.at[i, 'Short Value'] = 0.0
                short_active = False
            else:
                prev_short = sim_df.at[i - 1, 'Short Value']
                sim_df.at[i, 'Short Value'] = prev_short * (1 - multiplier * daily_return)
        else:
            sim_df.at[i, 'Short Value'] = 0.0
        
        # Combined portfolio is the sum of long and short positions
        sim_df.at[i, 'Combined Value'] = sim_df.at[i, 'Long Value'] + sim_df.at[i, 'Short Value']
    
    return sim_df[['Date', 'Long Value', 'Short Value', 'Combined Value']]


if __name__ == '__main__':
    # Example usage:
    data_file = 'sp500_data.csv'
    try:
        data = pd.read_csv(data_file)
    except FileNotFoundError:
        print('Data file not found. Please run data_fetch.py first.')
        exit(1)
    
    results = simulate_pair_strategy(data,
                                     start_date='2025-04-01',
                                     multiplier=10.0,
                                     long_barrier_pct=0.02,
                                     short_barrier_pct=0.02,
                                     initial_investment=100.0,
                                     entry_cost=5.0,
                                     spread=3.0)
    print(results.head())
