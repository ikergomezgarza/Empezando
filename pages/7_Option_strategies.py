from Functions import (
    BlackScholes, OptionPricing, MarketData,
    get_prices_opcions, get_all_chains, parse_chain,
    real_BS_data, chain_buy_sell
)

import streamlit as st
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

load_dotenv()

ALPACA_KEY    = st.secrets.get("ALPACA_KEY") or os.getenv("ALPACA_KEY")
ALPACA_SECRET = st.secrets.get("ALPACA_SECRET") or os.getenv("ALPACA_SECRET")

st.title("Option strategies")
st.write("")

col1,col2= st.columns(2)

with col1:  ticker = st.text_input("Ticker for the Option chain:", "AAPL")

md = MarketData(ticker)
md.load()

S = md.S

expiries = md.expiries
days = [(pd.to_datetime(e) - pd.Timestamp.today().normalize()).days for e in expiries]

choose_expirie = [
    expiries[i] + "  ( " + str(days[i]) + " days left)"
    for i in range(len(expiries))
]

with col2: expirie_selected = st.selectbox("Select expiries", choose_expirie)

idx = choose_expirie.index(expirie_selected)
date = expiries[idx]
day = days[idx]

T = day

chain = chain_buy_sell(md.df, date)


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


if "selections" not in st.session_state:
    st.session_state.selections = []

col1, col2= st.columns(2)
with col1: st.info("Call:       Bid to buy, Ask to sell")
with col2: st.info("Put:        Bid to buy, Ask to sell")

select = st.dataframe(
    chain.style.apply(highlight_in_money, axis=1).apply(highlight_chain_col, axis=0).format("{:.2f}"),
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-cell"
)

user_input = select["selection"]["cells"] or []

for key, i in user_input:
    if i in ["ask (c)", "bid (c)", "ask (p)", "bid (p)"]:
        
        trade= 1
        call= True
        
        types= i.split(" ")
        if types[0]== "ask":
            trade *= -1
        if types[1] == "(p)":
            call= False
        
        item = {
            
            "strike": chain.loc[key, "strike"],
            "trade": trade,
            "call": call,
            "day": day,
            "premium": chain.loc[key, i]
            
        }
        
        if item not in st.session_state.selections:
            st.session_state.selections.append(item)

if st.button("Reset options to buy"):
    st.session_state.selections = []

#st.write(st.session_state.selections)
st.write("")
st.write(f"Current orders: {ticker}")

for i in st.session_state.get("selections", []):
    cont = "Call" if i.get("call", True) else "Put"
    trd = "Sell" if i.get("trade", 1) == -1 else "Buy"
    
    st.info(f"{trd} a  {i["strike"]} {cont} option at {i["premium"]}$ that expires in {i["day"]} day")

contracts= OptionPricing(md, st.session_state.selections)

st.write("")
col1, col2= st.columns([1,4])
with col2:
    fig= contracts.plot_stremlit()
    st.plotly_chart(fig, use_container_width=True)

with col1:
    if len(st.session_state.selections) != 0:
        breaks_evens = ", ".join(map(str, contracts.break_even()))
        st.error(f"Max loss: {contracts.max_loss()}$")
        st.success(f"Max porfit: {contracts.max_profit()}$")
        st.info(f" Break even: {breaks_evens} stock price")
        
       #"st.info(f"Max loss: {contracts.max_loss()}, ax porfit: {contracts.max_profit()}, Break even: {breaks_evens}")

st.write("")
st.page_link("main.py", label="Back to Home")