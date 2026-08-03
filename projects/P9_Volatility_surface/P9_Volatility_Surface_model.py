import requests
import streamlit as st
import re
import plotly.graph_objects as go
from IPython.display import display
import pandas as pd
import re
import matplotlib.pyplot as plt
from Functions import get_price


def get_all_chains(ticker):
    r = requests.get(
        f"https://cdn.cboe.com/api/global/delayed_quotes/options/{ticker}.json"
    )
    data = r.json()

    return data


def parse_chain(data):
    options = data["data"]["options"]
    rows = []
    for o in options:
        # parse option string e.g. AAPL260413C00185000
        match = re.match(r"([A-Z]+)(\d{6})([CP])(\d{8})", o["option"])
        if not match:
            continue
        ticker, expiry, call_put, strike = match.groups()
        rows.append(
            {
                "expiry": f"20{expiry[:2]}-{expiry[2:4]}-{expiry[4:]}",
                "strike": int(strike) / 1000,
                "type": "call" if call_put == "C" else "put",
                "mid": (o["bid"] + o["ask"]) / 2,
                "iv": o["iv"],
                "delta": o["delta"],
                "gamma": o["gamma"],
                "theta": o["theta"],
                "vega": o["vega"],
                "volume": o["volume"],
                "oi": o["open_interest"],
            }
        )
    return pd.DataFrame(rows)


def filter_surface_df(df, S, strike_range=0.05, n_expiracies=10):

    df = df[
        (df["strike"] >= S * (1 - strike_range))
        & (df["strike"] <= S * (1 + strike_range))
    ]

    next_10 = sorted(df["expiry"].unique())

    next_10 = next_10[:n_expiracies] if n_expiracies <= len(next_10) else next_10

    df = df[df["expiry"].isin(next_10)]

    OTM_puts = df[(df["type"] == "put") & (df["strike"] < S)]
    OTM_calls = df[(df["type"] == "call") & (df["strike"] > S)]

    surface_df = pd.concat([OTM_puts, OTM_calls]).sort_values(["expiry", "strike"])
    surface_df = surface_df[["expiry", "strike", "iv"]]

    return surface_df


def surface_vol_builder(surface_df):

    surface_df["days"] = (
        pd.to_datetime(surface_df["expiry"]) - pd.Timestamp.today()
    ).dt.days

    pivot = surface_df.pivot_table(index="days", columns="strike", values="iv")

    fig = go.Figure(
        data=[
            go.Surface(
                x=pivot.columns.values,  # strikes
                y=pivot.index.values,  # days
                z=pivot.values,  # IV matrix
                colorscale="Viridis",
            )
        ]
    )

    fig.update_layout(
        title="Volatility Surface",
        scene=dict(
            xaxis_title="Strike", yaxis_title="Days to Expiry", zaxis_title="IV"
        ),
        template="plotly_dark",
    )

    return fig


def smile_vol(surface_df, S):
    next_1 = sorted(surface_df["expiry"].unique())[:1]
    df = surface_df[surface_df["expiry"].isin(next_1)]

    smile = df[["strike", "iv"]].reset_index(drop=True)

    fig, ax = plt.subplots()
    ax.plot(smile["strike"], smile["iv"])
    ax.axvline(x=S, color="red", linestyle="--", alpha=0.7, label=f"S = {S}")
    ax.set_xlabel("Strike")
    ax.set_ylabel("IV")
    ax.set_title(f"Vol Smile — {next_1[0]}")

    return fig


def full_surface_pipeline(ticker, **kwargs):

    data = get_all_chains(ticker)
    df = parse_chain(data)
    prices = get_price(ticker)
    S = prices[-1]

    surface_df = filter_surface_df(df, S, **kwargs)
    surface_fig = surface_vol_builder(surface_df)
    smile_fig = smile_vol(surface_df)

    return surface_fig, smile_fig, surface_df
