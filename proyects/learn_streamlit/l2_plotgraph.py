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
import plotly.express as px


def compound_interest(C0, i=0.05, n=50):

    data = {}
    for year in range(n):
        CF = C0 * (1 + i) ** year
        data[year] = CF

    df = pd.DataFrame(data.items(), columns=["Year", "Value"])
    print(df)

    return df


# . streamlit run /Users/ikergg/Documents/Python learning/Proyectos/Empezando/proyects/learn_streamlit/l2_plotgraph.py

if __name__ == "__main__":
    st.write("# Hello world")

    initial = st.slider("Initial money", 0, 1000)
    rate = st.slider("Interest rate", 0.0, 1.0)

    df = compound_interest(initial, i=rate)
    fig = px.line(df, x="Year", y="Value", markers=True, title="Values Over Years")
    st.plotly_chart(fig)
