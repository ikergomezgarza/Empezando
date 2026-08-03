import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from edgar import *
import os
from dotenv import load_dotenv

load_dotenv()
set_identity(os.getenv("EMAIL"))
print("All imported")


def get_marketcap(c_name):
    ticker = yf.Ticker("AAPL")
    market_cap = ticker.info.get("marketCap")
    shares = ticker.info.get("sharesOutstanding")
    price = ticker.history(period="1d")["Close"].iloc[-1]
    print(
        f"Market cap is {market_cap:,.0f}, with {shares} shares valued at {price:.1f}$"
    )

    return market_cap


def get_cashdata(c_name):
    c = Company(c_name)  # ticker
    fin = c.get_financials()  # pulls latest 10-K/10-Q financials from XBRL
    cf = fin.cash_flow_statement()  # cash flow statement (DataFrame-like)
    df = cf.to_dataframe()
    row = df.iloc[15]
    a = row.iloc[3]
    return a


# get data of company outside to compute faster
def pricing_dfc(CF, r=0.1, n=10, g=0.05):
    DCF = CF
    for i in range(n):
        DCF += (CF * (1 + g) ** i) / (1 + r) ** i

    # print(DCF)

    # print(f"future value is {DCF/1000000000:.1f} Billions")
    return DCF


c_name = "AAPl"
years = 1
r = 0.1
val = int(0)
marketcap = get_marketcap(c_name)
cashflow = get_cashdata(c_name)


def check_years(cashflow, marketcap):
    years = 1
    for i in range(15):
        val = pricing_dfc(cashflow, 0.07, years)
        if val / marketcap > 1:
            print(
                f"At curent cashflow the company is valued at {years} years of cash flow"
            )
            return

        if years > 9:
            print(
                f"At curent cashflow the company is valued at {val / marketcap * 100:.2f}% of DCF after 10 years "
            )
            return

        years += 1


def check_rate(cashflow, marketcap):
    g = 0.1
    r = 0.05
    for i in range(200):
        val = pricing_dfc(cashflow, 0.05, 10, g)
        g += 0.01
        if val / marketcap > 1:
            print(
                f"At curent cashflow the company is valued at {g * 100:.0f}% rate of growth after 10 years"
            )
            return
        # print(r)
        # print(val/marketcap*100)
        g += 0.01

        if g > 1:
            print(
                f"At curentt cashflow with 100% growth the comapny is at {val / marketcap * 100:.0f}% of marketcap "
            )
            return


if __name__ == "__main__":
    c_name = "AAPl"
    apple_marketcap = get_marketcap(c_name)
    apple_cashflow = get_cashdata(c_name)

    check_years(apple_cashflow, apple_marketcap)
    check_rate(apple_cashflow, apple_marketcap)
