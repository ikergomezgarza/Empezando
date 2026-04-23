from Functions import (
    get_returns_cvar,
    cvar_efficient_frontier,
    cvar_weights, 
    adjusting_cvar_backtest, 
    static_cvar_backtest
)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cvxpy as cp
import streamlit as st
from datetime import datetime
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import plotly.graph_objects as go

import os
from dotenv import load_dotenv
load_dotenv()
ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")
client = StockHistoricalDataClient(ALPACA_KEY,  ALPACA_SECRET)

st.title("CVaR Model")
st.write("")

if "selections" not in st.session_state:
    st.session_state.selections = []

def add_ticker():
    ticker = st.session_state.ticker_input.upper()
    if ticker and ticker not in st.session_state.selections:
        try:
            request = StockBarsRequest(
                symbol_or_symbols=ticker,
                timeframe=TimeFrame.Day,
                start="2024-01-01",
                feed="iex"
            )
            bars = client.get_stock_bars(request).df
            if bars.empty:
                st.session_state.ticker_error = f"{ticker} not found"
            else:
                st.session_state.selections.append(ticker)
                st.session_state.ticker_error = ""
        except:
            st.session_state.ticker_error = f"{ticker} not found"
    st.session_state.ticker_input = ""
    
ticker= st.text_input("Ticker to add:", key="ticker_input", on_change=add_ticker)

if st.session_state.get("ticker_error"):
    st.error(st.session_state.ticker_error)
    
if ticker and ticker.upper() not in st.session_state.selections:
    st.session_state.selections.append(ticker.upper())

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Delete last"):
        if st.session_state.selections:
            st.session_state.selections = st.session_state.selections[:-1]

with col2:
    if st.button("Reset"):
        st.session_state.selections = []
        
with col3:
    if st.button("Use example"):
        st.session_state.selections = ["AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "GOOGL", "META", "JPM", "XOM", "NFLX"]

st.write("")
st.info(f"Current tickers:  {', '.join(st.session_state.selections)}")
st.write("")

col1, col2 = st.columns(2)
st.write("")

with col1: START_DATE = st.date_input("Start from:", "2024-01-01")
with col2: alpha = st.number_input("Alpha:", 0.0, 1.0, 0.05)

st.write("")
if st.button("Start the CVaR"):
    
    if not st.session_state.selections:
        st.error("You have to add tickers to the portfolio.")
        st.stop()
    
    data = {s: get_returns_cvar(s, START_DATE= START_DATE) for s in st.session_state.selections}
    df = pd.DataFrame(data)
    
    with st.spinner("Running CVaR optimization..."):
        frontier_df, frontier_full = cvar_efficient_frontier(df, alpha = alpha)
    
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=frontier_df["cvar"],
            y=frontier_df["target_return"],
            mode="lines",
            line=dict(color="#00ff88", width=2),
            name="CVaR Efficient Frontier",
            
        )
    )
    
    max_sharpe = frontier_df.loc[frontier_df["sharpe"].idxmax()]
    fig.add_trace(go.Scatter(
        x=[max_sharpe["cvar"]],
        y=[max_sharpe["target_return"]],
        mode="markers+text",
        marker=dict(size=10, color="yellow"),
        text=["Max Sharpe"],
        textposition="top right",
        name=f"Max Sharpe {round(max_sharpe["sharpe"],2)}",
    ))
    
    min_cvar = frontier_df.loc[frontier_df["cvar"].idxmin()]
    fig.add_trace(go.Scatter(
        x=[min_cvar["cvar"]],
        y=[min_cvar["target_return"]],
        mode="markers+text",
        marker=dict(size=10, color="cyan"),
        text=["Min CVaR"],
        textposition="top right",
        name=f"Min CVaR {round(max_sharpe["cvar"],4)}",
))
        
    fig.update_layout(
    xaxis_title="CVaR (Tail Risk)",
    yaxis_title="Expected Daily Return",
    )
    
    fig.update_layout(
    yaxis=dict(
        title="Expected Daily Return",
        tickformat=".2%"
    ))
    
    st.plotly_chart(fig, use_container_width=True)
   
    weights_df = cvar_weights(frontier_df, frontier_full)

    fig2 = go.Figure()
    

    for ticker in weights_df.columns:
        fig2.add_trace(go.Scatter(
            x=weights_df.index,
            y=weights_df[ticker],
            mode="lines",
            stackgroup="one",
            name=ticker,
        ))

    fig2.update_layout(
        xaxis_title="Target Return",
        yaxis_title="Weight",
        yaxis=dict(tickformat=".0%"),
        xaxis=dict(tickformat=".2%"),
        title="Portfolio Weights Across CVaR Frontier",
    )

    st.plotly_chart(fig2)
    
    st.subheader("Max Sharpe Portfolio")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Annual Return", f"{max_sharpe['annual_return']:.1%}")
    col2.metric("Annual Volatility", f"{max_sharpe['annual_std']:.1%}")
    col3.metric("Sharpe Ratio", f"{max_sharpe['sharpe']:.2f}")
    col4.metric("CVaR", f"{max_sharpe['cvar']:.2%}")

    st.write("")
    st.subheader("Min CVaR Portfolio")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Annual Return", f"{min_cvar['annual_return']:.1%}")
    col2.metric("Annual Volatility", f"{min_cvar['annual_std']:.1%}")
    col3.metric("Sharpe Ratio", f"{min_cvar['sharpe']:.2f}")
    col4.metric("CVaR", f"{min_cvar['cvar']:.2%}")
    
    max_sharpe_weights = frontier_full[frontier_df["sharpe"].idxmax()]["weights"]
    min_cvar_weights = frontier_full[frontier_df["cvar"].idxmin()]["weights"]

    # clean up numerical noise
    max_sharpe_weights = max_sharpe_weights.clip(lower=0)
    max_sharpe_weights = (max_sharpe_weights / max_sharpe_weights.sum()).round(4)

    min_cvar_weights = min_cvar_weights.clip(lower=0)
    min_cvar_weights = (min_cvar_weights / min_cvar_weights.sum()).round(4)
    
    max_sharpe_weights.name = None
    min_cvar_weights.name = None
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Max Sharpe Weights**")
        st.dataframe(max_sharpe_weights[max_sharpe_weights > 0.001].sort_values(ascending=False).map("{:.1%}".format).to_frame("Weight"))

    with col2:
        st.markdown("**Min CVaR Weights**")
        st.dataframe(min_cvar_weights[min_cvar_weights > 0.001].sort_values(ascending=False).map("{:.1%}".format).to_frame("Weight"))
        
    st.write("")
    st.title("Results of the model:")
    
    with st.spinner("Backtesting the portfolio against S&P 500"):
    
        spy_returns= get_returns_cvar("SPY") # Get S&P 500 for back testing
        spy_df = pd.DataFrame(data)
        
        cvar_series = adjusting_cvar_backtest(df)
        eq_series = static_cvar_backtest(df)
        eq_series_spy = static_cvar_backtest(spy_df)

        cvar_cumulative = (1 + cvar_series).cumprod()
        eq_cumulative = (1 + eq_series).cumprod()
        eq_cumulative_spy = (1 + eq_series_spy).cumprod()

        backtesting_df = pd.concat([cvar_cumulative, eq_cumulative, eq_cumulative_spy], axis = 1)
        backtesting_df.columns = ["CVaR adjusted", "CVaR", "S&P 500"]
        
        st.line_chart(df)
    
st.write("")
st.page_link("main.py", label="Back to Home")
    
