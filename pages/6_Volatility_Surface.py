import requests
import streamlit as st
import re
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from Functions import get_prices_opcions, get_all_chains, parse_chain, filter_surface_df, surface_vol_builder, smile_vol
#from Functions import other_surface_builder, surface_plotly



ticker = st.text_input("Ticker for the Option Volatility:", "AAPL")


data       = get_all_chains(ticker)
df         = parse_chain(data)
prices     = get_prices_opcions(ticker)
S          = prices[-1]



st.write("")
st.title("Volatility Surface")
st.write("")
st.write("Contrary to the Black Scholes model the volatility is not constant across diferent strike prices")
st.write("The closer to in the money the higher the lower the volatility it has, and also the longer the time to expiracie the more volatility the price can be")
st.write("")

params= {"strike_range" : .05, "n_expiracies": 10}
maximum = sorted(df["expiry"].unique())

col1, col2 = st.columns(2)
with col1: strike_range = st.slider("Strike range %",            0.0, 0.1,     0.05,   step= .01)
with col2: n_expirancies= st.slider("Number of expiracies",      0,   len(maximum),     10,     step= 1)
params= {"strike_range" : strike_range, "n_expiracies": n_expirancies}    
    
surface_df  = filter_surface_df(df, S, **params)
surface_fig = surface_vol_builder(surface_df)
smile_fig   = smile_vol(surface_df, S)


st.plotly_chart(surface_fig, use_container_width=True)
st.write("(If the 3d graph looks incomplete try reducing the number of expiracies contracts or the strike range)")
st.write("")

st.title("The Smile")
st.write("")
st.write("The left side (OTM puts) has higher volatility because investors buys puts as protection,so there is more demand there for more upside or downside swings, and calls OTM are not as bought ")
st.plotly_chart(smile_fig, use_container_width=True)

st.write("")
#st.write("")
#st.write("Looking at other ways to plot, have to refine the data colecting for more smooth curvature")
#fig = other_surface_builder(surface_df)
#st.pyplot(fig)

#fig = surface_plotly(surface_df)
#st.plotly_chart(fig, use_container_width=True)

st.page_link("main.py", label="Back to Home")