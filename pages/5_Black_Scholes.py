from Functions import BlackScholes, opcion_chain, get_prices_opcions
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import math
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()
ALPACA_KEY    = st.secrets.get("ALPACA_KEY") or os.getenv("ALPACA_KEY")
ALPACA_SECRET = st.secrets.get("ALPACA_SECRET") or os.getenv("ALPACA_SECRET")

st.title("Black Scholes")
st.write("")

ticker = st.text_input("Ticker for the Option chain:", "AAPL")
prices= get_prices_opcions(ticker)
log_returns = np.diff(np.log(prices))
vol = round(np.std(log_returns) * np.sqrt(252), 4)

params={  
    "S" : prices[-1],
    "K" : prices[-1],
    "T" : 30,
    "r" :.035,
    "o" : vol
    }

col1, col2= st.columns([1,3])
option = st.radio("", ["Call", "Put"], horizontal=True, label_visibility="collapsed")
with col1:
    S = st.number_input("Current stock price", min_value=0., max_value=1000., value=prices[-1], step=1.)
    K = st.number_input("Strike price", min_value=0., max_value=1000., value=prices[-1], step=1.)
    T = st.number_input("Days till expiration", min_value=0, max_value=1000, value=30, step=1)
    r = st.number_input("risk free rate", min_value=0., max_value=1., value=.035, step=.005)
    o = st.number_input("Asset volatility", min_value=0., max_value=1., value=vol, step=.01)
    call = True if option == "Call" else False
    
with col2:
    
    @st.cache_data
    def compute_prices(S, K, T, r, o, call):
        prices = np.linspace(int(S * 3/4), int(S * 5/4), 200)
        vals = [BlackScholes(s, K, T, r, o, call=call).price() for s in prices]
        return prices, vals

    prices, vals = compute_prices(S, K, T, r, o, call)
    
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=prices, y=vals,
        mode="lines",
        line=dict(color="#00ff88", width=2),
        name="Option Price"
    ))

    fig.add_vline(x=S, line_dash="dash", line_color="red", annotation_text="Current Price")
    fig.add_vline(x=K, line_dash="dash", line_color="gray", annotation_text="Strike")

    fig.update_layout(
        title=f"{'Call' if call else 'Put'} Option Price",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Stock Price",
        yaxis_title="Option Value",
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)
    
    
def highlight_chain_col(col):
    if col.name == "strike":
        return ["background-color: rgba(255,255,0,0.2)"] * len(col)
    return [""] * len(col)

def highlight_in_money(row):
    styles = []
    for col in row.index:
        if row["strike"] < S and "(c)" in col:
            styles.append("background-color: rgba(144,238,144,0.4)")
        elif row["strike"] > S and "(p)" in col:
            styles.append("background-color: rgba(144,238,144,0.4)")
        else:
            styles.append("")
    return styles
    
st.write("")
st.write("")
st.write("")

bs= BlackScholes(S, K, T, r, o, call= call)
col0, col1, col2, col3, col4, col5 = st.columns(6)
with col0: st.metric("Price", round(bs.price(),3))
with col1: st.metric("Delta", round(bs.delta(),3))
with col2: st.metric("Gamma", round(bs.gamma(),3))
with col3: st.metric("Theta", round(bs.theta()/365,3))
with col4: st.metric("Vega", round(bs.vega(),3))
with col5: st.metric("Rho", round(bs.rho(),3))


st.write("")
chain = opcion_chain(S, K, T, r, o)
st.dataframe(chain.style.apply(highlight_in_money, axis=1)
                        .apply(highlight_chain_col, axis=0)
                        .format("{:.2f}"),
                        hide_index=True)

st.page_link("main.py", label="Back to Home")