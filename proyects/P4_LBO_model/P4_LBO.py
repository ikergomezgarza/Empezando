import sys
import pandas as pd
import yfinance as yf

print("All imported")

# from Functions import *
sys.path.append("/Users/ikergg/Documents/Python learning/Proyectos/Empezando")


def ebitdas(c_name):
    ticker = yf.Ticker(c_name)
    inc = ticker.financials
    cf = ticker.cashflow

    year = str(inc.columns[0].year)

    operating_income = (
        inc.loc["Operating Income"].iloc[0] if "Operating Income" in inc.index else 0
    )

    dep_am = 0
    for tag in ["Depreciation And Amortization", "Depreciation"]:
        if tag in cf.index:
            dep_am = cf.loc[tag].iloc[0]
            break

    ebitda = operating_income + dep_am
    confidence = "high" if (operating_income != 0 and dep_am != 0) else "low"

    return {
        "operating_income": operating_income,
        "dep_am": dep_am,
        "ebitda": ebitda,
        "year": year,
        "confidence": confidence,
    }


def funds_table(
    ebitda_results,
    entry_multiple=10,
    pct_debt=0.70,
    pct_senior=0.60,
    transaction_fee_pct=0.02,
    financing_fee_pct=0.035,
    mgmt_rollover_pct=0.10,
    verbose=False,
    **kwargs,
):

    ebitda = ebitda_results["ebitda"]
    pct_sub = 1 - pct_senior

    # Enterprise Value
    TEV = ebitda * entry_multiple

    # Debt
    total_debt = TEV * pct_debt
    senior_debt = total_debt * pct_senior
    sub_debt = total_debt * pct_sub

    # Fees
    transaccion_fees = TEV * transaction_fee_pct
    financing_fees = total_debt * financing_fee_pct

    # Equity
    total_uses = TEV + transaccion_fees + financing_fees
    equity_requirement = total_uses - total_debt
    managment_rollover = equity_requirement * mgmt_rollover_pct
    sponsor_equity = equity_requirement - managment_rollover

    # Leverage
    total_debt_x = total_debt / ebitda
    senior_debt_x = senior_debt / ebitda

    # I would have store the data like this but AI organize it
    results = {
        "--USES-------------------": "",
        "TEV": TEV,
        "transaccion_fees": transaccion_fees,
        "financing_fees": financing_fees,
        "total_uses": total_uses,
        "--SOURCES-----------------": "",
        "senior_debt": senior_debt,
        "Sub/_HY_debt": sub_debt,
        "total_debt": total_debt,
        "managment_rollover": managment_rollover,
        "sponsor_equity": sponsor_equity,
        "Total_Sources": total_debt + managment_rollover + sponsor_equity,
        "--CHECKS------------------": "",
        "Total_Debt_/_EBITDA": f"{total_debt_x:.1f}x",
        "Senior_Debt_/_EBITDA": f"{senior_debt_x:.1f}x",
        "Equity_%": f"{(equity_requirement / total_uses):.1%}",
    }

    # AI did it for good visual representation
    if verbose == False:
        pass
    else:
        for k, v in results.items():
            if v == "":
                print(f"\n{k}")
            else:
                label = f"  {k:<30}"
                value = f"{v:>12,.0f}" if isinstance(v, float) else f"{v:>12}"
                print(label + value)

    return results


def fcf_data(c_name):
    ticker = yf.Ticker(c_name)
    cf = ticker.cashflow
    bal = ticker.balance_sheet
    inc = ticker.financials

    year = cf.columns[0]
    year_prev = cf.columns[1]

    CAPEX = 0
    for tag in ["Capital Expenditure", "Purchase Of Property Plant And Equipment"]:
        if tag in cf.index:
            CAPEX = abs(cf.loc[tag].iloc[0])
            break

    NWC = None
    NWC_1 = None
    if "Current Assets" in bal.index and "Current Liabilities" in bal.index:
        NWC = bal.loc["Current Assets"].iloc[0] - bal.loc["Current Liabilities"].iloc[0]
        NWC_1 = (
            bal.loc["Current Assets"].iloc[1] - bal.loc["Current Liabilities"].iloc[1]
        )

    NWC_change = (NWC - NWC_1) if (NWC is not None and NWC_1 is not None) else 0

    tax_rate = None
    if "Tax Provision" in inc.index and "Pretax Income" in inc.index:
        pretax = inc.loc["Pretax Income"].iloc[0]
        tax = inc.loc["Tax Provision"].iloc[0]
        tax_rate = tax / pretax if pretax != 0 else None

    if CAPEX == 0 or NWC is None:
        tax_rate = 0.25
        confidence = "low"
    else:
        confidence = "high"

    return {
        "CAPEX": CAPEX,
        "NWC": NWC,
        "NWC_change": NWC_change,
        "tax_rate": tax_rate or 0.25,
        "year": str(year.year),
        "confidence": confidence,
    }


def fcf_model(ebitdas_data, fcf_data, ebitda_growth=0.05, years=5, nwc_pct=0.02):

    ebitda = ebitdas_data["ebitda"]
    dep_am = ebitdas_data["dep_am"]
    tax_rate = fcf_data["tax_rate"] or 0.25
    capex = fcf_data["CAPEX"]
    nwc_change = fcf_data["NWC_change"]
    nwc_pct_historical = nwc_change / ebitda  # historical ratio
    nwc_pct_capped = min(nwc_pct_historical, nwc_pct)  # cap at parameter defau

    years_list = []
    ebitda_list = []
    ebit_list = []
    nopat_list = []
    fcf_list = []

    for year in range(1, years + 1):  # ← years + 1 so it goes 1 to 5 inclusive
        ebitda_yr = ebitda * (1 + ebitda_growth) ** (year - 1)
        ebit = ebitda_yr - dep_am
        tax = ebit * tax_rate
        nopat = ebit - tax
        fcf = nopat + dep_am - capex - (ebitda_yr * nwc_pct_capped)

        years_list.append(year)
        ebitda_list.append(round(ebitda_yr))
        ebit_list.append(round(ebit))
        nopat_list.append(round(nopat))
        fcf_list.append(round(fcf))

    return {
        "years_list": years_list,
        "ebitda_list": ebitda_list,
        "ebit_list": ebit_list,
        "nopat_list": nopat_list,
        "fcf_list": fcf_list,
    }


def debt_schedule(
    funds_results,
    fcf_results,
    senior_rate=0.07,
    sub_rate=0.10,
    amort_pct=0.05,
    sweep_pct=0.5,
    years=5,
    **kwargs,
):

    origianl_senior = funds_results["senior_debt"]
    beginning_senior = origianl_senior
    original_sub = funds_results["Sub/_HY_debt"]
    beginning_sub = original_sub
    fcf_list = fcf_results["fcf_list"]

    senior_beginning_list = []
    senior_ending_list = []
    senior_interest_list = []
    sub_ending_list = []
    sub_interest_list = []
    total_interest_list = []
    total_debt_list = []

    for i in range(years):
        mandatory_amort = -min(origianl_senior * amort_pct, beginning_senior)
        cash_after_amort = fcf_list[i] + mandatory_amort
        optional_sweep = -min(
            max(cash_after_amort, 0) * sweep_pct, beginning_senior + mandatory_amort
        )
        ending_senior = beginning_senior + mandatory_amort + optional_sweep
        interest_senior = ((beginning_senior + ending_senior) / 2) * senior_rate

        ending_sub = beginning_sub
        interest_sub = ((beginning_sub + ending_sub) / 2) * sub_rate

        beginning_senior = ending_senior
        beginning_sub = ending_sub

        senior_beginning_list.append(round(beginning_senior))
        senior_ending_list.append(round(ending_senior))
        senior_interest_list.append(round(interest_senior))
        sub_ending_list.append(round(ending_sub))
        sub_interest_list.append(round(interest_sub))
        total_interest_list.append(round(interest_senior + interest_sub))
        total_debt_list.append(round(ending_senior + ending_sub))

    return {
        "senior_beginning_list": senior_beginning_list,
        "senior_ending_list": senior_ending_list,
        "senior_interest_list": senior_interest_list,
        "sub_ending_list": sub_ending_list,
        "sub_interest_list": sub_interest_list,
        "total_interest_list": total_interest_list,
        "total_debt_list": total_debt_list,
    }


def returns(
    fcf_results,
    debt_results,
    funds_results,
    exit_multiple=9,
    years=5,
    verbose=False,
    **kwargs,
):

    ebitda_last_year = fcf_results["ebitda_list"][-1]
    remaining_debt = debt_results["total_debt_list"][-1]
    sponsor_equity = funds_results["sponsor_equity"]

    exit_tev = ebitda_last_year * exit_multiple
    equity_value = exit_tev - remaining_debt
    MoM = equity_value / sponsor_equity
    IRR = (MoM) ** (1 / years) - 1

    if verbose == False:
        pass
    else:
        if IRR > 0.2:
            print(f" IRR: {IRR:.1%} — acceptable")
        else:
            print(f" IRR: {IRR:.1%} — not acceptable")

        if MoM > 2.5:
            print(f" MoM: {MoM:.2f}x — acceptable")
        else:
            print(f" MoM: {MoM:.2f}x — not acceptable")

    return {"IRR": IRR, "MoM": MoM, "exit_tev": exit_tev, "equity_value": equity_value}


def evaluate_company(c_name, entry_multiple=10):
    try:
        a = ebitdas(c_name)
        b = fcf_data(c_name)
        c = fcf_model(a, b)
        d = funds_table(a, entry_multiple=entry_multiple)
        e = debt_schedule(d, c)
        f = returns(c, e, d)

        return {
            "ticker": c_name,
            "year": a["year"],
            "ebitda_M": round(a["ebitda"] / 1e6, 1),
            "capex_M": round(b["CAPEX"] / 1e6, 1),
            "nwc_change_M": round(b["NWC_change"] / 1e6, 1),
            "tax_rate": round(b["tax_rate"] * 100, 1),
            "TEV_M": round(d["TEV"] / 1e6, 1),
            "sponsor_equity_M": round(d["sponsor_equity"] / 1e6, 1),
            "IRR": round(f["IRR"] * 100, 1),
            "MoM": round(f["MoM"], 2),
            "pass": f["IRR"] > 0.20,
            "confidence": a["confidence"],
        }
    except Exception as ex:
        print(f"⚠️ {c_name} failed: {ex}")
        return None


def compare_entries_exits(c_name, params, verbose=False):

    a = ebitdas(c_name)
    b = fcf_data(c_name)

    c = fcf_model(
        a,
        b,
        ebitda_growth=params.get("ebitda_growth", 0.05),
        years=params.get("years", 5),
    )

    total = []

    for i in range(5, 11):
        rows = []
        for j in range(5, 11):
            local_params = params.copy()
            local_params["entry_multiple"] = j
            local_params["exit_multiple"] = i

            d = funds_table(a, **local_params)
            e = debt_schedule(d, c, **local_params)
            f = returns(c, e, d, **local_params)

            rows.append(round(f["IRR"] * 100, 1))

        total.append(rows)

    df = pd.DataFrame(
        total,
        columns=[f"Entry {x}" for x in range(5, 11)],
        index=[f"Exit {x}" for x in range(5, 11)],
    )

    return df


def highlight_irr(val):
    if val >= 25:
        return "background-color: #d4edda ; color: black "
    elif val >= 20:
        return "background-color: #fff3cd; color: black"
    else:
        return "background-color: #f8d7da; color: black "
