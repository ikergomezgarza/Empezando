import pandas as pd
from finvizfinance.quote import finvizfinance
import yfinance as yf
from IPython.display import display
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.valuation import Valuation
from finvizfinance.screener.financial import Financial

print("All instaled")


def company_data(ticker):
    stock = finvizfinance(ticker)
    stock_dict = stock.ticker_fundament()

    return stock_dict


def get_company_area(stock_dict):

    stock_areas = {
        "sector": stock_dict["Sector"],
        "industry": stock_dict["Industry"],
        "index": stock_dict["Index"].split(", "),
    }

    return stock_areas


def get_index_companies(stock_areas):

    indexes = {}

    # hardcoded because they are only 4 opcions and dificult to get around it
    index_map = {
        "DJIA": "DJIA",
        "NDX": "NASDAQ 100",
        "S&P 500": "S&P 500",
        "RUT": "RUSSELL 2000",
    }

    for i in stock_areas["index"]:
        # converts the return of the index to find it in screnner
        mapped = index_map.get(i)
        if mapped is None:
            continue

        foverview = Overview()
        filters_dict = {"Index": mapped}
        foverview.set_filter(filters_dict=filters_dict)
        data = foverview.screener_view()

        indexes[mapped] = data

    return indexes


def get_competition(stock_areas):

    # Get them and filter them
    fvaluation = Valuation()
    filters_dict = {"Sector": stock_areas["sector"]}
    fvaluation.set_filter(filters_dict=filters_dict)
    # Get DF
    all_competition_df = fvaluation.screener_view()

    fvaluation = Valuation()
    filters_dict = {
        "Sector": stock_areas["sector"],
        "Industry": stock_areas["industry"],
    }
    fvaluation.set_filter(filters_dict=filters_dict)
    direct_competition_df = fvaluation.screener_view()

    indexes_dfs = get_index_companies(stock_areas)

    return {
        "all competition": all_competition_df,
        "direct competition": direct_competition_df,
        "index competition": indexes_dfs,
    }


def filter_df(df, market_cap, past_sales_5, eps_next_5):

    if len(df) > 10:
        df = df[
            (df["Market Cap"] > market_cap / 3) & (df["Market Cap"] < market_cap * 3)
        ]

    if len(df) > 10 and past_sales_5 != 0 and "Sales Past 5Y" in df.columns:
        df["Sales Past 5Y"] = (
            df["Sales Past 5Y"].str.replace("%", "").str.replace("-", "0").astype(float)
        )
        df = df[abs(df["Sales Past 5Y"] - past_sales_5) < 10]

    if len(df) > 10 and eps_next_5 != 0 and "EPS Next 5Y" in df.columns:
        df["EPS Next 5Y"] = (
            df["EPS Next 5Y"].str.replace("%", "").str.replace("-", "0").astype(float)
        )
        df = df[abs(df["EPS Next 5Y"] - eps_next_5) < 10]

    return df


def clean_dfs(all_dfs, ticker):

    # Values to evaluate

    df_all_competition = all_dfs["all competition"]
    try:
        market_cap = df_all_competition[df_all_competition["Ticker"] == ticker][
            "Market Cap"
        ].iloc[0]
    except Exception:
        market_cap = 0

    if "Sales Past 5Y" in df_all_competition.columns:
        try:
            past_sales_5 = df_all_competition[df_all_competition["Ticker"] == ticker][
                "Sales Past 5Y"
            ].iloc[0]
            past_sales_5 = past_sales_5.replace("%", "").replace("-", "0")
            past_sales_5 = float(past_sales_5)
        except Exception:
            past_sales_5 = 0
    else:
        past_sales_5 = 0

    if "EPS Next 5Y" in df_all_competition.columns:
        try:
            eps_next_5 = df_all_competition[df_all_competition["Ticker"] == ticker][
                "EPS Next 5Y"
            ].iloc[0]
            eps_next_5 = eps_next_5.replace("%", "").replace("-", "0")
            eps_next_5 = float(eps_next_5)
        except Exception:
            eps_next_5 = 0
    else:
        eps_next_5 = 0

    df = filter_df(df_all_competition, market_cap, past_sales_5, eps_next_5)

    all_dfs["all competition"] = df

    # for the indexes
    df_indexes = all_dfs["index competition"]

    for i in df_indexes:
        df = filter_df(df_indexes[i], market_cap, past_sales_5, eps_next_5)
        all_dfs[i] = df

    all_dfs.pop("index competition")

    for i in all_dfs:
        df = all_dfs[i]["Ticker"]
        all_dfs[i] = df

    return all_dfs


def all_values(all_dfs_clean, ticker):

    table_dfs = {}

    for key in all_dfs_clean:
        table = []
        for t in all_dfs_clean[key]:  # t is each ticker string
            try:
                yfin = yf.Ticker(t).info
                market_cap = yfin.get("marketCap")
                total_debt = yfin.get("totalDebt", 0)
                total_cash = yfin.get("totalCash", 0)
                net_debt = total_debt - total_cash
                enterprise_value = yfin.get("enterpriseValue")
                minority_interest = enterprise_value - market_cap - net_debt
                total_revenue = yfin.get("totalRevenue")
                ebitda = yfin.get("ebitda")
                ev_revenue = enterprise_value / total_revenue
                ev_ebitda = enterprise_value / ebitda
                shares = yfin.get("sharesOutstanding")
                price = yfin.get("previousClose")

                temporal_dict = {
                    "ticker": t,  # peer ticker not subject
                    "market cap": market_cap,
                    "net debt": net_debt,
                    "minority interest": minority_interest,
                    "enterprise value": enterprise_value,
                    "total revenue": total_revenue,
                    "ebitda": ebitda,
                    "ev/revenue": ev_revenue,
                    "ev/ebitda": ev_ebitda,
                    "shares": shares,
                    "price": price,
                }

            except Exception:
                continue
            table.append(temporal_dict)

        table_dfs[key] = pd.DataFrame(table)

    return table_dfs


def build_table(all_dataframes, ticker):

    b = next(iter(all_dataframes))
    c = all_dataframes[b].columns

    for i in c:
        if i == "price" or i == "shares":
            pass
        else:
            print(f"{i:<20}|", end=" ")

    print("")
    print("_" * 20 * (len(c) - 1))

    for dictionary in all_dataframes:
        print("")
        print(dictionary)

        df = all_dataframes[dictionary]
        row = df[df["ticker"] == ticker].iloc[0]

        df_no_ticker = df[df["ticker"] != ticker]

        for i in c:  # Means
            if i == "ticker":
                print(f"{'Mean':<20}|", end=" ")

            elif i == "ev/revenue" or i == "ev/ebitda":
                mean = round(df_no_ticker[i].mean(), 2)
                print(f"{mean:<20}|", end=" ")

            elif i == "price" or i == "shares":
                continue

            else:
                mean = round(df_no_ticker[i].mean() / 1e6)
                print(f"{mean:<20}|", end=" ")

        print("")

        for i in c:  # Median
            if i == "ticker":
                print(f"{'Median':<20}|", end=" ")

            elif i == "ev/revenue" or i == "ev/ebitda":
                median = round(df_no_ticker[i].median(), 2)
                print(f"{median:<20}|", end=" ")

            elif i == "price" or i == "shares":
                continue

            else:
                median = round(df_no_ticker[i].median() / 1e6)
                print(f"{(median):<20}|", end=" ")

        print("")

        for i in c:  # Ticker
            if i == "ticker":
                print(f"{ticker:<20}|", end=" ")

            elif i == "ev/revenue" or i == "ev/ebitda":
                val = round(row[i], 2)
                print(f"{val:<20}|", end=" ")

            elif i == "price" or i == "shares":
                continue

            else:
                val = round(row[i] / 1e6)
                print(f"{(val):<20}|", end=" ")

        print("")
        print("- " * int(20 / 2) * (len(c) - 1))

        df_no_ticker = df_no_ticker.copy()
        ev_ex = row["ebitda"] * df_no_ticker["ev/ebitda"].median()
        row["enterprise value"] = ev_ex
        row["market cap"] = ev_ex - row["net debt"] - row["minority interest"]
        row["ev/ebitda"] = df_no_ticker["ev/ebitda"].median()

        for i in c:  # Expected
            if i == "ticker":
                print(f"{'Expected':<20}|", end=" ")

            elif i == "ev/revenue" or i == "ev/ebitda":
                val = round(row[i], 2)
                print(f"{round(val, 2):<20}|", end=" ")

            elif i == "price" or i == "shares":
                continue

            else:
                val = round(row[i] / 1e6)
                print(f"{(round(val, 2)):<20}|", end=" ")

        print("\n", "_" * 20 * (len(c) - 1))


def relative_valuation(ticker):

    stock_dict = company_data(ticker)
    print("Company data done")
    stock_areas = get_company_area(stock_dict)
    print("Company areas done")
    all_dfs = get_competition(stock_areas)
    print("Company competition done")
    all_dfs_clean = clean_dfs(all_dfs, ticker)
    print("Company df clean done")
    all_dataframes = all_values(all_dfs_clean, ticker)
    print("Company all values done")
    build_table(all_dataframes, ticker)


if __name__ == "__main__":
    relative_valuation("AAPL")
