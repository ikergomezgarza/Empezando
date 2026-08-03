import streamlit as st
from finvizfinance.quote import finvizfinance
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.valuation import Valuation
from finvizfinance.screener.financial import Financial
import numpy as np
from edgar import *
import yfinance as yf
from IPython.display import display

set_identity("ikergogiga@gmail.com")
import pandas as pd

st.write("# Hello world")


def get_cashdata(c_name):
    c = Company(c_name)
    fin = c.get_financials()
    cf = fin.cash_flow_statement()
    df = cf.to_dataframe()
    row = df.iloc[15]
    a = row.iloc[3]
    return a


def pricing_dcf(CF, r=0.1, n=10, g=0.05):
    DCF = CF
    for i in range(n):
        DCF += (CF * (1 + g) ** i) / (1 + r) ** i
    return DCF


if __name__ == "__main__":
    year = st.slider("Number of years", 0, 10)
    growth = st.slider("Growth_rate", 0.0, 0.25)
    rate = st.slider("Discount rate", 0.0, 0.1)

    CF = get_cashdata("AAPL")
    DCF = pricing_dcf(CF, r=rate, n=year, g=growth)

    st.write(DCF)
    st.text_input("Ticker", "MANH")

# streamlit run /Users/ikergg/Documents/Python learning/Proyectos/Empezando/proyects/learn_streamlit/l2_plotgraph.py
