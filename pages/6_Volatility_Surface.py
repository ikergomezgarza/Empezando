import yfinance as yf
import streamlit as st

@st.cache_data(ttl=3600)
def get_option_chain(ticker, expiry):
    tk = yf.Ticker(ticker)
    chain = tk.option_chain(expiry)
    return chain.calls, chain.puts

@st.cache_data(ttl=3600)
def get_expiries(ticker):
    return yf.Ticker(ticker).options  # list of available expiry dates

# page
ticker = st.text_input("Ticker", "AAPL").upper()
expiries = get_expiries(ticker)

expiry = st.selectbox("Expiry", expiries)
calls, puts = get_option_chain(ticker, expiry)

st.write(calls)