#!/usr/bin/env python3
'''
streamlit_app.py

Streamlit application that fetches historical S&P 500 data,
runs a paired knockout certificate simulation (including entry cost and spread),
and displays a performance graph with two y-axes:
  - Left axis: Combined knockout strategy portfolio value.
  - Right axis: Normalized S&P 500 performance.

Below the plot, a merged result table is shown that includes dates, knockout values, and normalized S&P 500 values.
'''

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from data_fetch import get_sp500_data
from simulation import simulate_pair_strategy


def main():
    st.title('Paired Knockout Certificate Strategy Simulator')
    st.write('This app simulates a paired knockout certificate strategy on the S&P 500 using historical data. '
             'The simulation models a 3× leveraged long certificate (with a downside knockout barrier) and a 3× '
             'leveraged short certificate (with an upside knockout barrier). Both positions incur an entry cost '
             'and a spread. The chart below uses a separate axis for the normalized S&P 500 for clarity, and '
             'the merged results table (including both knockout values and the S&P 500) is displayed below the plot.')

    # Sidebar: parameters for simulation.
    st.sidebar.header('Simulation Parameters')
    start_date = st.sidebar.date_input('Simulation Start Date', datetime(2020, 1, 1))
    multiplier = st.sidebar.number_input('Leverage Multiplier (e.g. 3 for 3x)',
                                           min_value=1.0, value=3.0, step=0.5)
    long_barrier_pct = st.sidebar.number_input('Long Knockout Barrier (% drop from entry)',
                                               min_value=0.0, value=10.0, step=0.5) / 100
    short_barrier_pct = st.sidebar.number_input('Short Knockout Barrier (% rise from entry)',
                                                min_value=0.0, value=10.0, step=0.5) / 100
    initial_investment = st.sidebar.number_input('Initial Investment per Position ($)',
                                                   min_value=1.0, value=100.0, step=10.0)
    entry_cost = st.sidebar.number_input('Entry Cost ($)', min_value=0.0, value=5.0, step=0.5)
    spread = st.sidebar.number_input('Spread ($)', min_value=0.0, value=3.0, step=0.5)

    if st.sidebar.button('Run Simulation'):
        with st.spinner('Fetching historical data and running simulation...'):
            # Fetch historical data
            df = get_sp500_data(start_date='2000-01-01', save_csv=False)
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
            # For comparison: process the original S&P500 data from the simulation start date onward
            df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.tz_convert(None)
            df = df.sort_values('Date').reset_index(drop=True)
            start_date_dt = pd.to_datetime(start_date.strftime('%Y-%m-%d'))
            comp_df = df[df['Date'] >= start_date_dt].copy().reset_index(drop=True)
            
            # Calculate the normalized close
            entry_price = comp_df.iloc[0]['Close']
            comp_df['Normalized S&P500'] = initial_investment * (comp_df['Close'] / entry_price)
            
            # Add normalized High/Low for the daily vertical lines
            comp_df['Normalized High'] = initial_investment * (comp_df['High'] / entry_price)
            comp_df['Normalized Low'] = initial_investment * (comp_df['Low'] / entry_price)
            
            # Merge the simulation results with the normalized S&P500 data (including high/low)
            merged_df = pd.merge(
                sim_df,
                comp_df[['Date', 'Normalized S&P500', 'Normalized High', 'Normalized Low']],
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

        # ---------------------
        # Plot vertical bars for daily High-Low on the right axis:
        ax2.vlines(
            merged_df['Date'], 
            merged_df['Normalized Low'], 
            merged_df['Normalized High'],
            color='gray', 
            alpha=0.6, 
            linewidth=1, 
            label='Daily High-Low'
        )
        # Plot normalized S&P 500 line
        ax2.plot(merged_df['Date'], merged_df['Normalized S&P500'],
                 color='red', linestyle='--', label='Normalized S&P 500')

        # Add horizontal lines for knockout levels on the normalized axis
        long_knockout_norm = initial_investment * (1 - long_barrier_pct)
        short_knockout_norm = initial_investment * (1 + short_barrier_pct)
        ax2.axhline(long_knockout_norm, color='grey', linestyle=':', label='Long Knockout Value')
        ax2.axhline(short_knockout_norm, color='grey', linestyle=':', label='Short Knockout Value')

        # Add horizontal line for the "in the money" value on the left axis
        in_the_money_value = 2 * (initial_investment - (entry_cost + spread))
        ax1.axhline(in_the_money_value, color='green', linestyle='-.', label='In the Money Value')
        # ---------------------

        ax2.set_ylabel('Normalized S&P 500 Value ($)', color='red')
        ax2.tick_params(axis='y', labelcolor='red')

        # Add legend for both axes
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

        ax1.set_title('Paired Knockout Strategy vs. Normalized S&P 500 Performance')
        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()
        st.pyplot(fig)

        # Always display the merged result table below the plot
        st.subheader('Simulation Results')
        st.dataframe(merged_df[['Date', 'Long Value', 'Short Value', 'Combined Value', 
                                'Normalized S&P500']].reset_index(drop=True))


if __name__ == '__main__':
    main()
