from Functions import (
    get_returns_cvar,
    cvar_efficient_frontier,
    cvar_weights
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
START_DATE = st.date_input("Start from:")

st.write("")
st.info(f"Current tickers:  {', '.join(st.session_state.selections)}")

st.write("")
if st.write("Start the CVaR"):
    
    data = {s: get_returns_cvar(s, START_DATE= "2024-01-01") for s in st.session_state.selections}
    df = pd.DataFrame(data)
    
    frontier_df, frontier_full = cvar_efficient_frontier(df)
    
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
    
st.write("")
st.page_link("main.py", label="Back to Home")
    
