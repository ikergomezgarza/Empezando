from Functions import BlackScholes
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import math
import matplotlib.pyplot as plt

st.title("Greeks")

params={  
    "S" : 100,
    "K" : 100,
    "T" : 30,
    "r" :.035,
    "o" :.2
    }

col1, col2= st.columns(2)

with col1:
    S = st.number_input("Current stock price", min_value=0, max_value=1000, value=100, step=1)
    K = st.number_input("Strike price", min_value=0, max_value=1000, value=100, step=1)
    T = st.number_input("Days till expiration", min_value=0, max_value=1000, value=30, step=1)
    r = st.number_input("risk free rate", min_value=0., max_value=1., value=.035, step=.005)
    o = st.number_input("Asset volatility", min_value=0., max_value=1., value=.2, step=.01)
    option = st.radio("Select option", ["Call", "Put"])
    call = True if option == "Call" else False
    
with col2:
    
    @st.cache_data
    def compute_prices(S, K, T, r, o, call):
        prices = np.linspace(int(S * 3/4), int(S * 5/4), 200)
        vals = [BlackScholes(s, K, T, r, o, call=call).price() for s in prices]
        return prices, vals

    prices, vals = compute_prices(S, K, T, r, o, call)
    
    fig, ax = plt.subplots()
    ax.plot(prices,vals)

    st.pyplot(fig)