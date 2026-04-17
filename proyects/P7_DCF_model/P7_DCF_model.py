import pandas as pd
from edgar import *
import yfinance as yf
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()
set_identity(os.getenv("EMAIL"))
print("All imported")


def get_company_dcf_data(ticker, verbose=False):

    company = Company(ticker)
    financials = company.get_financials()
    df_inc = company.income_statement().to_dataframe()
    df_cash = company.cashflow_statement().to_dataframe()
    df_bal = company.balance_sheet().to_dataframe()
    yfin_ticker = yf.Ticker(ticker)
    info = yfin_ticker.info

    # ── Find year column (handle FY and non-FY formats) ──────────────
    year_cols = [c for c in df_inc.columns if "FY" in c]
    if not year_cols:
        # fallback: take first numeric-looking column
        year_cols = [c for c in df_inc.columns if any(ch.isdigit() for ch in str(c))]
    if not year_cols:
        print(f" {ticker}: no year columns found. Columns: {df_inc.columns.tolist()}")
        return None
    year = year_cols[0]
    year_prev = year_cols[1]

    # ── Operating Income ─────────────────────────────────────────────
    a = df_inc.loc[df_inc.index.str.contains("OperatingIncomeLoss", na=False), year]
    operating_income = int(a.iloc[0]) if not a.empty else 0

    # ── D&A ──────────────────────────────────────────────────────────
    dep_am = 0
    for tag in [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "Depreciation",
    ]:
        a = df_cash.loc[df_cash.index.str.contains(tag, na=False), year]
        if not a.empty and pd.notna(a.iloc[0]):
            dep_am = a.iloc[0]
            break

    # ── EBITDA ───────────────────────────────────────────────────────
    ebitda = operating_income + dep_am

    # ── CAPEX ───────────────────────────────────────────────────────
    CAPEX = abs(yfin_ticker.cashflow.loc["Capital Expenditure"].iloc[0])
    for tag in ["PaymentsToAcquirePropertyPlantAndEquipment", "CapitalExpenditures"]:
        a = df_cash.loc[df_cash.index.str.contains(tag, na=False), year]
        if not a.empty and pd.notna(a.iloc[0]):
            CAPEX = a.iloc[0]
            break

    # ── NWC ───────────────────────────────────────────────────────
    assets_m = df_bal.loc[df_bal.index == "AssetsCurrent"]
    liab_m = df_bal.loc[df_bal.index == "LiabilitiesCurrent"]
    NWC = (
        (assets_m[year].iloc[0] - liab_m[year].iloc[0])
        if (not assets_m.empty and not liab_m.empty)
        else None
    )
    NWC_1 = (
        (assets_m[year_prev].iloc[0] - liab_m[year_prev].iloc[0])
        if (not assets_m.empty and not liab_m.empty)
        else None
    )
    NWC_change = NWC - NWC_1

    # ── TAX RATE ───────────────────────────────────────────────────────
    tax_m = df_inc.loc[df_inc.index == "IncomeTaxExpenseBenefit"]
    pretax_m = df_inc.loc[
        df_inc.index.str.contains(
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxes", na=False
        )
    ]
    tax_rate = (
        (tax_m[year].iloc[0] / pretax_m[year].iloc[0])
        if (not tax_m.empty and not pretax_m.empty and pretax_m[year].iloc[0] != 0)
        else None
    )
    tax_rate = 0.21 if (tax_rate < 0 or tax_rate > 0.40) else tax_rate

    # ──WACC EXTRA DATA ───────────────────────────────────────────────────────
    try:
        beta = round(calculate_beta(ticker), 2)
    except:
        beta = info["beta"]

    market_cap = info["marketCap"]
    total_debt = yfin_ticker.balance_sheet.loc["Total Debt"].iloc[0]

    try:
        interest_expense = yfin_ticker.financials.loc["Interest Expense"].iloc[0]
        interest_expense = 0 if np.isnan(interest_expense) else abs(interest_expense)
    except:
        interest_expense = 0
        print(f"interest expense missing — so 0 used for {ticker}")

    # ──TRESURY BOND PRICE ───────────────────────────────────────────────────────
    tnx = yf.Ticker("^TNX")
    data = tnx.history(period="1d")
    bond_10yr = data["Close"].iloc[-1] / 100

    # ──CASH ───────────────────────────────────────────────────────
    cash = yfin_ticker.balance_sheet.loc["Cash And Cash Equivalents"].iloc[0]
    shares = info["sharesOutstanding"]
    share_price = info["previousClose"]

    confidence = (
        "high"
        if (operating_income != 0 and dep_am != 0 and "2024" not in str(year))
        else "low"
    )

    if verbose:
        print(f"Using          {ticker}, {year} financial year")
        print(f"Confidence:    {confidence}, \n")

        print(f"Market cap:    {market_cap / 1e6:.1f}M")
        print(f"Shares:        {shares}")
        print(f"Share price:   {share_price}")
        print(f"Cash:          {cash / 1e6:.1f}M")
        print(f"InterestExp:   {interest_expense / 1e6:.1f}M,\n")
        print(f"Total debt:    {total_debt / 1e6:.1f}M,\n")

        print(f"EBITDA:        {ebitda / 1e6:.1f}M")
        print(f"Ebit:          {operating_income / 1e6:.1f}M")
        print(f"D&A:           {dep_am / 1e6:.1f}M ")
        print(f"CAPEX:         {CAPEX / 1e6:.1f}M")
        print(f"NWC change:    {NWC_change / 1e6:.1f}M")
        print(f"tax_rate:      {tax_rate:.1%}")
        print("-" * 50)
        print("")

    return {
        "operating_income": operating_income,
        "dep_am": dep_am,
        "ebitda": ebitda,
        "CAPEX": CAPEX,
        "NWC": NWC,
        "NWC_change": NWC_change,
        "tax_rate": tax_rate,
        "cash": cash,
        "market_cap": market_cap,
        "shares": shares,
        "share_price": share_price,
        "beta": beta,
        "total_debt": total_debt,
        "interest_expense": interest_expense,
        "bond_10yr": bond_10yr,
        "year": year,
        "confidence": confidence,
    }


def forecast_unlevered_FCF(c_data, year=5, g=0.05, verbose=False):

    fcf_list = []

    FCF = (
        c_data["operating_income"] * (1 - c_data["tax_rate"])
        + c_data["dep_am"]
        - c_data["NWC_change"]
        - c_data["CAPEX"]
    )

    FCF_normalized = c_data["ebitda"] - c_data["CAPEX"]

    for i in range(1, year + 1):
        yr_fcf = FCF_normalized * (1 + g) ** i
        fcf_list.append(yr_fcf)

    if verbose:
        print(f"{'Year 0 (actual)':<20} ", end=" ")
        print(f"{'Year 0 (normalized)':<20} ", end=" ")
        for i in range(len(fcf_list)):
            print(f"{'Year ' + str(i + 1):<20}", end=" ")
        print("")

        print(f"{round(FCF / 1e6):<20} ", end=" ")
        print(f"{round(FCF_normalized / 1e6):<20} ", end=" ")
        for i in range(len(fcf_list)):
            val = round(fcf_list[i] / 1e6)
            print(f"{val:<20}", end=" ")
        print("\n")
        print("-" * 50)
        print("\n")

    return fcf_list


def get_wacc(c_data, equity_risk_premium=0.05, verbose=False):

    cost_of_equity = c_data["bond_10yr"] + c_data["beta"] * equity_risk_premium

    cost_debt = c_data["interest_expense"] / c_data["total_debt"]
    cost_debt_aftertax = cost_debt * (1 - c_data["tax_rate"])

    enterprise_value = c_data["market_cap"] + c_data["total_debt"]

    WACC = (c_data["market_cap"] / enterprise_value) * cost_of_equity + (
        c_data["total_debt"] / enterprise_value
    ) * cost_debt_aftertax

    if verbose:
        print(f"Parameters   ")
        print(f"Bond rate:                 {c_data['bond_10yr']:.1%}")
        print(f"Beta:                      {c_data['beta']}")
        print(f"equity_risk_premium:       {equity_risk_premium:.1%}")
        print(f"cost_of_equity:            {cost_of_equity:.1%},\n")
        print(f"cost_debt:                 {cost_debt:.2%}")
        print(f"cost_debt_aftertax:        {cost_debt_aftertax:.2%},\n")
        print(f"enterprise_value:          {enterprise_value / 1e6:.1f}M")
        print(f"WACC:                      {WACC:.1%}")
        print("-" * 50)
        print("")

    return WACC


def terminal_value(last_fcf, wacc, g_longterm=0.025):

    TV = last_fcf * (1 + g_longterm) / (wacc - g_longterm)

    return TV


def discount_FCF_WACC(fcf_list, WACC, g_longterm=0.025, verbose=False):

    fcf_projected = [fcf / (1 + WACC) ** i for i, fcf in enumerate(fcf_list, 1)]
    TV = terminal_value(fcf_list[-1], WACC, g_longterm=g_longterm)
    pv_TV = TV / (1 + WACC) ** 5
    enterprise_value = sum(fcf_projected) + pv_TV

    if verbose:
        print(f"Terminal Value:    {round(TV / 1e6, 2)}M")

    return enterprise_value


def final_details(c_data, enterprise_value, verbose=False):

    equity_value = enterprise_value - c_data["total_debt"] + c_data["cash"]
    intrinsic_price = equity_value / c_data["shares"]

    if verbose:
        print(f"intrinsic price:      {round(intrinsic_price, 2)} $")
        print(f"current price:        {round(c_data['share_price'], 2)} $")
        print(
            f"diference price:      {round(c_data['share_price'] - intrinsic_price, 2)} $"
        )

    return intrinsic_price


def calculate_beta(ticker, market="^GSPC", period="1y"):

    stock = yf.Ticker(ticker).history(period=period)["Close"].pct_change()
    mkt = yf.Ticker(market).history(period=period)["Close"].pct_change()

    df = pd.DataFrame({"market": mkt, "stock": stock}).dropna()

    covariance = df.cov().iloc[0, 1]
    variance = df["market"].var()

    return covariance / variance


def sensitivity_DCF(ticker, verbose=False):

    total = []
    c_data = get_company_dcf_data(ticker, verbose=verbose)

    g_vals = np.arange(0.05, 0.45, 0.05)
    wacc_vals = np.arange(0.05, 0.21, 0.01)

    for i in g_vals:
        rows = []

        for j in wacc_vals:
            fcf_list = forecast_unlevered_FCF(c_data, g=i, verbose=False)
            enterprise_value = discount_FCF_WACC(
                fcf_list, WACC=j, g=i, verbose=False, g_longterm=0.025
            )
            intrinsic_price = final_details(c_data, enterprise_value, verbose=False)
            rows.append(round(intrinsic_price, 2))

        total.append(rows)

    df = pd.DataFrame(
        total,
        columns=[f"{w:.0%}" for w in wacc_vals],
        index=[f"{g:.0%}" for g in g_vals],
    )

    current_price = c_data["share_price"]

    def highlight_dcf(val):
        if val > current_price * 1.1:
            return "background-color: #d4edda !important; color: black !important"
        elif val < current_price * 0.9:
            return "background-color: #f8d7da !important; color: black !important"
        else:
            return "background-color: #fff3cd !important; color: black !important"

    print(f"\n[{ticker}] Current Price: ${current_price}")
    return df.style.map(highlight_dcf).format("{:.2f}")


def DCF_Model(ticker, verbose=False, g=0.1):

    c_data = get_company_dcf_data(ticker, verbose=verbose)

    fcf_list = forecast_unlevered_FCF(c_data, g=g, verbose=verbose)

    WACC = get_wacc(c_data, verbose=verbose)

    enterprise_value = discount_FCF_WACC(
        fcf_list, WACC, g=g, verbose=verbose, g_longterm=0.025
    )

    intrinsic_price = final_details(c_data, enterprise_value, verbose=verbose)

    sensitivity_DCF("META", verbose=verbose)

    return intrinsic_price


if __name__ == "__main__":
    DCF_Model("META", verbose=True)
