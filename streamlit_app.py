#!/usr/bin/env python3
'''
streamlit_app.py

Streamlit application that fetches historical asset data,
runs a paired knockout certificate simulation (including entry cost and spread),
and displays a performance graph with two y-axes:
  - Left axis: Combined knockout strategy portfolio value.
  - Right axis: Normalized asset performance.

Below the plot, a merged result table is shown that includes dates, knockout values, and normalized asset values.
'''

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from data_fetch import get_yf_data
from simulation import simulate_pair_strategy


def main():
    st.title('Paired Knockout Certificate Strategy Simulator')
    st.write('This app simulates a paired knockout certificate strategy on a given asset using historical data. '
             'The simulation models a user defined leveraged long certificate (with a downside knockout barrier) and a '
             'similar leveraged short certificate (with an upside knockout barrier). Both positions incur an entry cost '
             'and a spread. The chart below uses a separate axis for the normalized underlying asset for clarity, and '
             'the merged results table (including both knockout values and the underlying) is displayed below the plot.'
             'Common Yahoo Finance Tickers are ^GSPC for the S&P500, ^NDX for the Nasdaq 100 or ^GDAXI for the DAX. '
             'These can easily be found via Google or on Yahoo Finance.')

    # Sidebar: parameters for simulation.
    st.sidebar.header('Simulation Parameters')
    asset = st.sidebar.text_input('Yahoo Finance Ticker Symbol (e.g. ^GSPC)', value='^GSPC')
    start_date = st.sidebar.date_input('Simulation Start Date', datetime(2025, 4, 1))
    multiplier = st.sidebar.number_input('Leverage Multiplier (e.g. 3 for 3x)',
                                           min_value=1.0, value=10.0, step=0.5)
    long_barrier_pct = st.sidebar.number_input('Long Knockout Barrier (% drop from entry)',
                                               min_value=0.0, value=11.0, step=0.5) / 100
    short_barrier_pct = st.sidebar.number_input('Short Knockout Barrier (% rise from entry)',
                                                min_value=0.0, value=11.0, step=0.5) / 100
    initial_investment = st.sidebar.number_input('Initial Investment per Position ($)',
                                                   min_value=1.0, value=100.0, step=10.0)
    entry_cost = st.sidebar.number_input('Entry/Exit Cost ($)', min_value=0.0, value=5.0, step=0.5)
    spread = st.sidebar.number_input('Spread ($)', min_value=0.0, value=3.0, step=0.5)

    if st.sidebar.button('Run Simulation'):
        with st.spinner('Fetching historical data and running simulation...'):
            # Fetch historical data
            result = get_yf_data(start_date='2000-01-01', save_csv=False, yf_ticker=asset)
            if 'Error' in result.keys():
                st.error(f'Ticker not found: {asset}')
                st.stop()
            else:
                df = result['historics']
                asset_name = result['name']

            # Run paired knockout simulation
            sim_df = simulate_pair_strategy(
                df,
                start_date=start_date.strftime('%Y-%m-%d'),
                multiplier=multiplier,
                long_barrier_pct=long_barrier_pct,
                short_barrier_pct=short_barrier_pct,
                initial_investment=initial_investment,
                entry_cost=entry_cost,
                spread=spread
            )
            # For comparison: process the original asset data from the simulation start date onward
            df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.tz_convert(None)
            df = df.sort_values('Date').reset_index(drop=True)
            start_date_dt = pd.to_datetime(start_date.strftime('%Y-%m-%d'))
            comp_df = df[df['Date'] >= start_date_dt].copy().reset_index(drop=True)
            
            # Calculate the normalized close
            entry_price = comp_df.iloc[0]['Close']
            comp_df[f'Normalized {asset_name}'] = initial_investment * (comp_df['Close'] / entry_price)
            
            # Add normalized High/Low for the daily vertical lines
            comp_df['Normalized High'] = initial_investment * (comp_df['High'] / entry_price)
            comp_df['Normalized Low'] = initial_investment * (comp_df['Low'] / entry_price)
            
            # Merge the simulation results with the normalized asset data (including high/low)
            merged_df = pd.merge(
                sim_df,
                comp_df[['Date', f'Normalized {asset_name}', 'Normalized High', 'Normalized Low']],
                on='Date',
                how='left'
            )

        st.success('Simulation complete!')

        # Create a plot with two y-axes
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax2 = ax1.twinx()

        # Plot combined knockout strategy on the left axis
        ax1.plot(merged_df['Date'], merged_df['Combined Value'],
                 color='blue', label='Combined Knockout Portfolio')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Knockout Portfolio Value ($)', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')

        # Plot normalized asset line
        ax2.plot(merged_df['Date'], merged_df[f'Normalized {asset_name}'],
                 color='red', linestyle='--', label=f'Normalized {asset_name}')

        # Add horizontal lines for knockout levels on the normalized axis
        long_knockout_norm = initial_investment * (1 - long_barrier_pct)
        short_knockout_norm = initial_investment * (1 + short_barrier_pct)
        ax2.axhline(long_knockout_norm, color='grey', linestyle=':', label='Long Knockout Value')
        ax2.axhline(short_knockout_norm, color='grey', linestyle=':', label='Short Knockout Value')

        # Add horizontal line for the "in the money" value on the left axis
        in_the_money_value = 2 * (initial_investment + (entry_cost + spread))
        ax1.axhline(in_the_money_value, color='green', linestyle='-.', label='In the Money Value')
        # ---------------------

        ax2.set_ylabel(f'Normalized {asset_name} Value ($)', color='red')
        ax2.tick_params(axis='y', labelcolor='red')

        # Add legend for both axes
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

        ax1.set_title(f'Paired Knockout Strategy vs. Normalized {asset_name} Performance')
        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()
        st.pyplot(fig)

        # Always display the merged result table below the plot
        st.subheader('Simulation Results')
        st.dataframe(merged_df[['Date', 'Long Value', 'Short Value', 'Combined Value', 
                                f'Normalized {asset_name}']].reset_index(drop=True))

if __name__ == '__main__':
    main()
