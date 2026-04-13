# Functions.py
from finvizfinance.quote import finvizfinance
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.valuation import Valuation
from finvizfinance.screener.financial import Financial
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time
from datetime import datetime, timedelta
import random
from scipy.stats import norm
import math
import matplotlib.pyplot as plt
HEADERS = {"User-Agent": "ikergogiga@gmail.com"}
import os
from dotenv import load_dotenv
import streamlit as st
import re
import plotly.graph_objects as go

load_dotenv()
ALPACA_KEY    = st.secrets.get("ALPACA_KEY") or os.getenv("ALPACA_KEY")
ALPACA_SECRET = st.secrets.get("ALPACA_SECRET") or os.getenv("ALPACA_SECRET")
FRED_KEY = st.secrets.get("FRED_KEY") or os.getenv("FRED_KEY")

# ── P2: Free Cash Flow ────────────────────────────────────────────────────────

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


# ── P3: Check years of valuation ────────────────────────────────────────────────────────────────

def check_years(cashflow, marketcap):
    years= 1
    for i in range(15):
        val= pricing_dcf(cashflow, .07, years) 
        if val/marketcap > 1:
            print(f"At curent cashflow the company is valued at {years} years of cash flow")
            return 
    
        if years>9:
            print(f"At curent cashflow the company is valued at {val/marketcap*100:.2f}% of DCF after 10 years ")
            return 
            
        years += 1 

def check_rate(cashflow, marketcap):   
    g=.1
    r=.05
    for i in range(200):
        val= pricing_dcf(cashflow, .05, 10, g) 
        g += .01 
        if val/marketcap > 1:
            print(f"At curent cashflow the company is valued at {g*100:.0f}% rate of growth after 10 years")
            return  
        #print(r)
        #print(val/marketcap*100)    
        g += .01
        
        if g>1:
            print(f"At curentt cashflow with 100% growth the comapny is at {val/marketcap*100:.0f}% of marketcap ")
            return 
            
# ── P4: LBO Model ────────────────────────────────────────────────────────────────

# -- Litst of funccions
# ebitdas(c_name)
# def funds_table(ebitda)
# fcf_data(c_name)
# fcf_model (ebitdas_data, fcf_data)
# def debt_schedule(funds_results, fcf_results)
# def returns(fcf_results, debt_results, funds_results, exit_multiple= 9, years= 5 ):
# def evaluate_company(c_name, entry_multiple=10)
 #def compare_entries_exits(c_name):

def get_cik(ticker):
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=HEADERS)
    data = r.json()
    for item in data.values():
        if item["ticker"].upper() == ticker.upper():
            return str(item["cik_str"]).zfill(10)
    raise Exception(f"Ticker {ticker} not found in SEC database")

def get_facts(ticker):
    cik = get_cik(ticker)
    print(f"{ticker} -> CIK: {cik}")  # debug
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS)
    return r.json()["facts"]["us-gaap"]

def get_latest_value(facts, concept):
    if concept not in facts:
        return 0
    units = facts[concept]["units"]
    key = list(units.keys())[0]
    entries = [e for e in units[key] if e.get("form") == "10-K" and "frame" not in e]
    if not entries:
        entries = [e for e in units[key] if e.get("form") == "10-K"]
    if not entries:
        return 0
    entries = sorted(entries, key=lambda x: x["end"], reverse=True)
    return entries[0]["val"]

def get_annual_value(facts, concept):
    if concept not in facts:
        return 0
    units = facts[concept]["units"]
    key = list(units.keys())[0]
    entries = [e for e in units[key] if e.get("form") == "10-K" and e.get("start") is not None]
    entries = [e for e in entries if 
               300 < (pd.to_datetime(e["end"]) - pd.to_datetime(e["start"])).days < 400]
    if not entries:
        return 0
    entries = sorted(entries, key=lambda x: x["end"], reverse=True)
    print(f"{concept}: {entries[0]}")  # debug
    return entries[0]["val"]

def ebitdas(c_name):
    facts = get_facts(c_name)

    operating_income = get_latest_value(facts, "OperatingIncomeLoss")
    
    dep_am = 0
    for tag in ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation"]:
        val = get_latest_value(facts, tag)
        if val != 0:
            dep_am = val
            break

    ebitda = operating_income + dep_am
    year = "latest"
    confidence = "high" if (operating_income != 0 and dep_am != 0) else "low"

    return {
        "operating_income": operating_income,
        "dep_am":           dep_am,
        "ebitda":           ebitda,
        "year":             year,
        "confidence":       confidence
    }
    
def funds_table(ebitda_results, entry_multiple=10, 
                pct_debt=0.70, pct_senior=0.60, 
                transaction_fee_pct=0.02, financing_fee_pct=0.035,
                mgmt_rollover_pct=0.10, verbose= False,  **kwargs):
    
    ebitda= ebitda_results["ebitda"]
    pct_sub= 1 - pct_senior
    
    #Enterprise Value
    TEV= ebitda * entry_multiple
    
    #Debt
    total_debt=          TEV*pct_debt
    senior_debt=         total_debt * pct_senior
    sub_debt=            total_debt * pct_sub
    
    #Fees
    transaccion_fees=    TEV * transaction_fee_pct
    financing_fees=      total_debt* financing_fee_pct
    
    #Equity
    total_uses =         TEV +transaccion_fees + financing_fees 
    equity_requirement = total_uses- total_debt
    managment_rollover=  equity_requirement * mgmt_rollover_pct
    sponsor_equity =     equity_requirement-managment_rollover
    
    #Leverage
    total_debt_x=        total_debt/ebitda
    senior_debt_x=       senior_debt/ebitda
    
    #I would have store the data like this but AI organize it
    results={
        "--USES-------------------":"",
        "TEV": TEV,
        "transaccion_fees":transaccion_fees,
        "financing_fees": financing_fees,
        "total_uses": total_uses,
        "--SOURCES-----------------":"",
        "senior_debt":senior_debt,
        "Sub/_HY_debt": sub_debt,
        "total_debt": total_debt,
        "managment_rollover":managment_rollover,
        "sponsor_equity":sponsor_equity,
        "Total_Sources":total_debt+ managment_rollover + sponsor_equity,
        "--CHECKS------------------":"",
        "Total_Debt_/_EBITDA": f"{total_debt_x:.1f}x",
        "Senior_Debt_/_EBITDA": f"{senior_debt_x:.1f}x",
        "Equity_%": f"{(equity_requirement / total_uses):.1%}",
        }
    
    #AI did it for good visual representation
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
    facts = get_facts(c_name)

    CAPEX = get_latest_value(facts, "PaymentsToAcquirePropertyPlantAndEquipment")
    if CAPEX == 0:
        CAPEX = get_latest_value(facts, "CapitalExpendituresIncurredButNotYetPaid")

    assets  = get_latest_value(facts, "AssetsCurrent")
    liabs   = get_latest_value(facts, "LiabilitiesCurrent")
    NWC     = assets - liabs if (assets and liabs) else None

    tax     = get_latest_value(facts, "IncomeTaxExpenseBenefit")
    pretax  = get_latest_value(facts, "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest")
    tax_rate = (tax / pretax) if (pretax and pretax != 0) else 0.25

    confidence = "high" if (CAPEX != 0 and NWC is not None) else "low"
    if confidence == "low":
        tax_rate = 0.25

    return {
        "CAPEX":      CAPEX,
        "NWC":        NWC or 0,
        "NWC_change": 0,
        "tax_rate":   tax_rate,
        "year":       "latest",
        "confidence": confidence
    }   
      
def fcf_model (ebitdas_data, fcf_data, ebitda_growth= .05, years= 5, nwc_pct=.02):
    
    ebitda = ebitdas_data["ebitda"]
    dep_am= ebitdas_data["dep_am"]
    tax_rate= fcf_data["tax_rate"] or .25
    capex= fcf_data["CAPEX"]
    nwc_change = fcf_data["NWC_change"]
    nwc_pct_historical = nwc_change / ebitda  # historical ratio
    nwc_pct_capped = min(nwc_pct_historical, nwc_pct)  # cap at parameter defau
    
    years_list=[]
    ebitda_list= []
    ebit_list= []
    nopat_list=[]
    fcf_list=[]

    for year in range(1, years + 1):   # ← years + 1 so it goes 1 to 5 inclusive
        ebitda_yr  = ebitda * (1 + ebitda_growth) ** (year - 1)
        ebit       = ebitda_yr - dep_am
        tax        = ebit * tax_rate
        nopat      = ebit - tax
        fcf        = nopat + dep_am - capex - (ebitda_yr * nwc_pct_capped)

        years_list.append(year)
        ebitda_list.append(round(ebitda_yr))
        ebit_list.append(round(ebit))
        nopat_list.append(round(nopat))
        fcf_list.append(round(fcf))

    return {
        "years_list" : years_list,
        "ebitda_list": ebitda_list,
        "ebit_list": ebit_list,
        "nopat_list": nopat_list,
        "fcf_list": fcf_list,
        }

def debt_schedule(funds_results, fcf_results, 
                  senior_rate= .07, sub_rate= .10,
                  amort_pct=.05, sweep_pct= .5, years= 5, **kwargs):
    
    origianl_senior= funds_results["senior_debt"]
    beginning_senior= origianl_senior
    original_sub= funds_results["Sub/_HY_debt"]
    beginning_sub= original_sub
    fcf_list= fcf_results["fcf_list"]
    
    senior_beginning_list = []
    senior_ending_list    = []
    senior_interest_list  = []
    sub_ending_list       = []
    sub_interest_list     = []
    total_interest_list   = []
    total_debt_list       = []
    
    for i in range(years):

        mandatory_amort= - min(origianl_senior * amort_pct, beginning_senior)
        cash_after_amort= fcf_list[i]+mandatory_amort
        optional_sweep = -min(max(cash_after_amort, 0) * sweep_pct, beginning_senior + mandatory_amort)
        ending_senior= beginning_senior + mandatory_amort + optional_sweep
        interest_senior= ((beginning_senior+ ending_senior)/2) * senior_rate
        
        ending_sub= beginning_sub 
        interest_sub= ((beginning_sub + ending_sub)/2) *sub_rate
        
        beginning_senior = ending_senior
        beginning_sub    = ending_sub
        
        senior_beginning_list.append(round(beginning_senior))
        senior_ending_list.append(round(ending_senior))
        senior_interest_list.append(round(interest_senior))
        sub_ending_list.append(round(ending_sub))
        sub_interest_list.append(round(interest_sub))
        total_interest_list.append(round(interest_senior + interest_sub))
        total_debt_list.append(round(ending_senior + ending_sub))
        

    
    return {
        "senior_beginning_list" : senior_beginning_list,
        "senior_ending_list": senior_ending_list,
        "senior_interest_list": senior_interest_list,
        "sub_ending_list": sub_ending_list,
        "sub_interest_list": sub_interest_list,
        "total_interest_list" : total_interest_list,
        "total_debt_list": total_debt_list,
        }
    
def returns(fcf_results, debt_results, funds_results, exit_multiple= 9, years= 5, verbose= False, **kwargs ):
    
    ebitda_last_year= fcf_results["ebitda_list"][-1]
    remaining_debt= debt_results["total_debt_list"][-1]
    sponsor_equity= funds_results[ "sponsor_equity"]
    
    exit_tev= ebitda_last_year* exit_multiple
    equity_value= exit_tev - remaining_debt
    MoM= equity_value/ sponsor_equity
    IRR= (MoM)**(1/years)-1
    
    if verbose == False: 
        pass
    else:
        if IRR > .2:
            print(f" IRR: {IRR:.1%} — acceptable")
        else:
            print(f" IRR: {IRR:.1%} — not acceptable")
            
        if MoM > 2.5:
            print(f" MoM: {MoM:.2f}x — acceptable")
        else:
            print(f" MoM: {MoM:.2f}x — not acceptable")
 
    return {                        
        "IRR":          IRR,
        "MoM":          MoM,
        "exit_tev":     exit_tev,
        "equity_value": equity_value
    }
    
def evaluate_company(c_name, entry_multiple=10):    
    try:
        a = ebitdas(c_name)
        b = fcf_data(c_name)
        c = fcf_model(a, b)
        d = funds_table(a, entry_multiple=entry_multiple)
        e = debt_schedule(d, c)
        f = returns(c, e, d)

        return {
            "ticker":          c_name,
            "year":            a["year"],
            "ebitda_M":        round(a["ebitda"] / 1e6, 1),
            "capex_M":         round(b["CAPEX"] / 1e6, 1),
            "nwc_change_M":    round(b["NWC_change"] / 1e6, 1),
            "tax_rate":        round(b["tax_rate"] * 100, 1),
            "TEV_M":           round(d["TEV"] / 1e6, 1),
            "sponsor_equity_M":round(d["sponsor_equity"] / 1e6, 1),
            "IRR":             round(f["IRR"] * 100, 1),
            "MoM":             round(f["MoM"], 2),
            "pass":            f["IRR"] > 0.20,
            "confidence":      a["confidence"]
        }
    except Exception as ex:
        print(f"⚠️ {c_name} failed: {ex}")
        return None
    
def compare_entries_exits(c_name, params, verbose=False):
    
    a = ebitdas(c_name)
    b = fcf_data(c_name)
    c = fcf_model(a, b,
                  ebitda_growth=params.get("ebitda_growth", 0.05),
                  years=params.get("years", 5))

    total = []
    
    for i in range(5, 11):
        rows = []
        for j in range(5, 11):
            d = funds_table(a,
                            entry_multiple=j,
                            pct_debt=params.get("pct_debt", 0.70),
                            pct_senior=params.get("pct_senior", 0.60),
                            transaction_fee_pct=params.get("transaction_fee_pct", 0.02),
                            financing_fee_pct=params.get("financing_fee_pct", 0.035),
                            mgmt_rollover_pct=params.get("mgmt_rollover_pct", 0.10))
            e = debt_schedule(d, c,
                              senior_rate=params.get("senior_rate", 0.07),
                              sub_rate=params.get("sub_rate", 0.10),
                              amort_pct=params.get("amort_pct", 0.05),
                              sweep_pct=params.get("sweep_pct", 0.50),
                              years=params.get("years", 5))
            f = returns(c, e, d,
                        exit_multiple=i,
                        years=params.get("years", 5))

            rows.append(round(f["IRR"] * 100, 1))
        total.append(rows)
        
    df = pd.DataFrame(
        total,
        columns=[f"Entry {x}" for x in range(5, 11)],
        index=[f"Exit {x}" for x in range(5, 11)]
    )
    
    return df
    
def highlight_irr(val):
    if val >= 25:
        return "background-color: #d4edda ; color: black "
    elif val >= 20:
        return "background-color: #fff3cd; color: black"
    else:
        return "background-color: #f8d7da; color: black "


# ── P5: Accretion dilution Model ────────────────────────────────────────────────────────────────

def get_price(ticker):
    url = f"https://data.alpaca.markets/v2/stocks/{ticker}/quotes/latest"
    headers = {
        "APCA-API-KEY-ID": ALPACA_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET
    }
    r = requests.get(url, headers=headers)
    data = r.json()
    return float(data["quote"]["ap"])

def get_companys_datas(acq, tgt, verbose=False):
    
    def extract(ticker_str):
        facts = get_facts(ticker_str)
        
        # Price from Alpha Vantage
        price = get_price(ticker_str)
        
        # Shares from EDGAR
        shares = get_latest_value(facts, "CommonStockSharesOutstanding")
        if shares == 0:
            shares = get_latest_value(facts, "CommonStockSharesIssued")
        
        market_cap = price * shares
        
        # Income statement from EDGAR
        net_income  = get_annual_value(facts, "NetIncomeLoss")
        if net_income == 0:
            net_income = get_annual_value(facts, "ProfitLoss")

        pretax = get_annual_value(facts, "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest")
        if pretax == 0 or abs(pretax) < abs(net_income):
            pretax = net_income / (1 - 0.21)
        revenue    = get_annual_value(facts, "Revenues")
        if revenue == 0:
            revenue = get_annual_value(facts, "RevenueFromContractWithCustomerExcludingAssessedTax")
        
        # Book value from EDGAR
        book_value = get_latest_value(facts, "StockholdersEquity")

        return {
            "symbol":            ticker_str,
            "marketCap":         market_cap,
            "previousClose":     price,
            "sharesOutstanding": shares,
            "netIncome":   net_income,
            "pretaxIncome": pretax,
            "totalRevenue":      revenue,
            "bookValue":         book_value,
        }

    acq_dict = extract(acq)
    tgt_dict = extract(tgt)

    if verbose:
        print(f"{'values':<15} | {acq_dict['symbol']:<25} | {tgt_dict['symbol']:<25}")
        print("-"*60)
        print(f"{'Market cap':<15} | {round(acq_dict['marketCap']):,} | {round(tgt_dict['marketCap']):,}")
        print(f"{'Price':<15} | {acq_dict['previousClose']:<25} | {tgt_dict['previousClose']:<25}")
        print(f"{'Shares':<15} | {acq_dict['sharesOutstanding']:<25} | {tgt_dict['sharesOutstanding']:<25}")

    return acq_dict, tgt_dict

def contract_offer(acq_dict, tgt_dict, offer_premium=.60, stock_pct=0.50, tax_rate=0.40,
                   years= 5, interest_rate= 0.05, financing_fees_pct=.035,transaccion_fees_pct= .02, 
                   synergies_pct=0, amortization_years= 10, verbose=False, **kwargs):
    
    # % of deal pay by cahs and with stocks
    cash_pct= 1-stock_pct
    
    # Amount of money the acusition will cost
    share_price= tgt_dict["previousClose"]* (1+offer_premium)
    offer_value= tgt_dict["sharesOutstanding"]* share_price
    acq_issued_shares= offer_value/acq_dict["previousClose"] * stock_pct
    
    # All expenses and writre offs 
    #Transaccion fees:
    transaccion_fees= offer_value * transaccion_fees_pct 
    #Financing fees:
    acq_borrowing= offer_value * cash_pct
    financing_fees= acq_borrowing * financing_fees_pct 
    financing_fees_amort= financing_fees/years
    #Posible write of 
    synergies= tgt_dict["totalRevenue"]* synergies_pct
    asset_write_off= (offer_value - tgt_dict["bookValue"]) * 0.15 
    incremental_DA_expense = asset_write_off/amortization_years 
    
    # Expected earnings
    acq_implide_net_inc    = acq_dict["netIncome"]
    tgt_implide_net_inc    = tgt_dict["netIncome"]
    acq_implide_pretax_inc = acq_dict["pretaxIncome"]
    tgt_implide_pretax_inc = tgt_dict["pretaxIncome"]
    
    #Getting all together and in negatice (accounting reasons)
    profroma_pretax_unadj= acq_implide_pretax_inc + tgt_implide_pretax_inc
    interest_expense_deal= acq_borrowing * interest_rate * -1
    incremental_DA_expense *= -1
    transaccion_fees *= -1
    financing_fees_amort *=-1
    synergies *=1 
    #after merge
    profroma_pretax_adj= profroma_pretax_unadj + interest_expense_deal + incremental_DA_expense + transaccion_fees + financing_fees_amort + synergies
    proforma_net_income= profroma_pretax_adj * (1-tax_rate)
    proforma_shares_outstanding= acq_dict["sharesOutstanding"]+ acq_issued_shares
    proforma_eps= proforma_net_income/proforma_shares_outstanding
    
    acq_eps = acq_dict["netIncome"] / acq_dict["sharesOutstanding"]
    accretion_dilution_per_share = proforma_eps - acq_eps
    accretion_dilution_pct = (proforma_eps / acq_eps) - 1 if acq_eps != 0 else 0
    
    if verbose == False:
        pass
    else: 
        print("Parameters:")
        print(f"Offer premium:            | {offer_premium*100}%")
        print(f"% of cash:                | {cash_pct*100}%")
        print(f"% of stock:               | {stock_pct*100}%")
        print(f"tax rate:                 | {tax_rate*100}%")
        print(f"interest rate:            | {interest_rate*100}%")
        print(f"% financing fees:         | {financing_fees_pct*100}%")
        print(f"% transaccion fees:       | {transaccion_fees_pct*100}%")
        print(f"% synergies:              | {synergies_pct*100}%")
        print(f"{"-"*60}\n")
        
        print("Deal:")
        print(f"Share price:              | {round(share_price):,}")
        print(f"Offer Value:              | {round(offer_value):,}")
        print(f"Money borrowed:           | {round(acq_borrowing):,}")
        print(f"Financing fees:           | {round(financing_fees):,}")
        print(f"Shares issued:            | {round(acq_issued_shares):,}\n")
        print(f"{"-"*60}\n")
        
        print("Income:")
        print(f"Accuary net income:       | {round(acq_implide_net_inc):,}")
        print(f"Target net income:        | {round(tgt_implide_net_inc):,}")
        print(f"Accuary pre tax income:   | {round(acq_implide_pretax_inc):,}")
        print(f"Target pre tax income:    | {round(tgt_implide_pretax_inc):,}")
        print(f"{"-"*60}\n")
        
        print("Totals")
        print(f"Proforma pretax unadj:    | {round(profroma_pretax_unadj):,}")
        print(f"Interest expenses:        | ({round(interest_expense_deal*-1):,})")
        print(f"Amort of finance fees:    | ({round(financing_fees_amort*-1):,})")
        print(f"Transaccion fees:         | ({round(transaccion_fees*-1):,})")
        print(f"D/A write off:            | ({round(incremental_DA_expense*-1):,})")
        print(f"% synergies:              | {round(synergies):,}")
        print(f"{"-"*60}\n")
        
        print("After merge:")
        print(f"Proforma pretax adj:      | {round(profroma_pretax_adj):,}")
        print(f"Proforma Net:             | {round(proforma_net_income):,}")
        print(f"Proforma shares:          | {round(proforma_shares_outstanding):,}")
        print(f"Proforma eps:             | {round(proforma_eps,ndigits=2)}")
        print(f"{"-"*60}\n")
        
        print("Results")
        print(f"Accretion/Dilution:       | $ {accretion_dilution_per_share:.2f}")
        print(f"%Accretion/Dilution:      | % {accretion_dilution_pct:.2f}")
    
    returns= {
    
    "share_price": share_price,
    "offer_value":offer_value,
    "money_borrowed": acq_borrowing,
    "financing_fees":financing_fees,
    "transaccion_fees":transaccion_fees,
    "shares_issued": acq_issued_shares,
    "accuary_net_income": acq_implide_net_inc,
    "target_net_income": tgt_implide_net_inc,
    "accuary_pretax_income": acq_implide_pretax_inc,
    "target_pretax_income": tgt_implide_pretax_inc,
    "synergies":synergies,
    
    
    "profroma_pretax_unadj": profroma_pretax_unadj,
    "interest_expense_deal": interest_expense_deal,
    "financing_fees_amort": financing_fees_amort,
    "incremental_DA_expense": incremental_DA_expense,
    
    "profroma_pretax_adj": profroma_pretax_adj,
    "proforma_net_income": proforma_net_income,
    "proforma_shares_outstanding": proforma_shares_outstanding,
    "proforma_eps": proforma_eps,
    "accretion_dilution_per_share": accretion_dilution_per_share,
    "accretion_dilution_pct": accretion_dilution_pct,

}
    return returns

def highlight_irr_accdil(val):
    if val >= 0:
        return "background-color: #d4edda ; color: black"
    elif val >= -.05:
        return "background-color: #fff3cd ; color: black "
    else:
        return "background-color: #f8d7da ; color: black "
    
def sensitivity_accretion_dilution(acq_dict, tgt_dict, verbose=False, steps=1, **kwargs):
    
    rows = []
    for i in range(0, 11, steps):
        row = []
        for j in range(0, 11, steps):
            result = contract_offer(acq_dict, tgt_dict,
                                    offer_premium=i/10,
                                    stock_pct=j/10,
                                    verbose=False,
                                    **kwargs)
            row.append(round(result["accretion_dilution_pct"] * 100, 2))
        rows.append(row)

    df = pd.DataFrame(rows,
                      columns=[f"Stock {x*10}%" for x in range(0, 11, steps)],
                      index=[f"Offer premium {x*10}%" for x in range(0, 11, steps)])
    return df

def accretion_dilution_model(acq,tgt):
    acq_dict, tgt_dict = get_companys_datas(acq,tgt, verbose= True)
    contract_offer(acq_dict, tgt_dict, verbose=True )
    sensitivity_accretion_dilution(acq_dict, tgt_dict)
    
# ── P6: Relative Valuation ────────────────────────────────────────────────────────────────

def company_data(ticker):
    stock= finvizfinance(ticker)
    stock_dict= stock.ticker_fundament()
    
    return stock_dict

def get_company_area(stock_dict):
    
    stock_areas= {"sector": stock_dict["Sector"],
                  "industry": stock_dict["Industry"],
                  "index":stock_dict["Index"].split(", ")
                  }
    
    return stock_areas

def get_index_companies(stock_areas):
    
    indexes= {}
    
    #hardcoded because they are only 4 opcions and dificult to get around it
    index_map = {
        "DJIA": "DJIA",
        "NDX": "NASDAQ 100",
        "S&P 500": "S&P 500",
        "RUT": "RUSSELL 2000"
        }
    
    for i in stock_areas["index"]:
        
        #converts the return of the index to find it in screnner
        mapped = index_map.get(i)
        if mapped is None:
            continue
        
        foverview = Overview()
        filters_dict = {'Index': mapped}
        foverview.set_filter(filters_dict=filters_dict)
        data = foverview.screener_view()
        
        indexes[mapped]= data
        
    return indexes

def get_competition(stock_areas):
    
    # Get them and filter them
    fvaluation = Valuation()
    filters_dict = {'Sector': stock_areas["sector"]}
    fvaluation.set_filter(filters_dict=filters_dict)
    # Get DF
    all_competition_df = fvaluation.screener_view()
    
    fvaluation = Valuation()
    filters_dict = {'Sector': stock_areas["sector"], 'Industry': stock_areas["industry"]}
    fvaluation.set_filter(filters_dict=filters_dict)
    direct_competition_df= fvaluation.screener_view()
    
    indexes_dfs= get_index_companies(stock_areas)
    
    return {'all competition':all_competition_df,
            'direct competition': direct_competition_df, 
            'index competition':indexes_dfs}
    
def filter_df(df, market_cap, past_sales_5, eps_next_5):
    df = df.copy()
    if len(df) > 10:
        df = df[(df['Market Cap'] > market_cap/3) & (df['Market Cap'] < market_cap*3)]

    if len(df) > 10 and past_sales_5 != 0 and 'Sales Past 5Y' in df.columns:
        df['Sales Past 5Y'] = df['Sales Past 5Y'].str.replace('%', '').str.replace('-', '0').astype(float)
        df = df[abs(df['Sales Past 5Y'] - past_sales_5) < 10]

    if len(df) > 10 and eps_next_5 != 0 and 'EPS Next 5Y' in df.columns:
        df['EPS Next 5Y'] = df['EPS Next 5Y'].str.replace('%', '').str.replace('-', '0').astype(float)
        df = df[abs(df['EPS Next 5Y'] - eps_next_5) < 10]

    return df

def clean_dfs(all_dfs, ticker):
    
    # Values to evaluate

    df_all_competition= all_dfs['all competition']
    try: 
        market_cap = df_all_competition[df_all_competition['Ticker'] == ticker]['Market Cap'].iloc[0]
    except Exception:
        market_cap = 0
        
    if 'Sales Past 5Y' in df_all_competition.columns:
        try:
            past_sales_5 = df_all_competition[df_all_competition['Ticker'] == ticker]['Sales Past 5Y'].iloc[0]
            past_sales_5 = past_sales_5.replace("%", "").replace('-', "0")
            past_sales_5 = float(past_sales_5)
        except Exception:
            past_sales_5 = 0
    else:
        past_sales_5 = 0
        
    if 'EPS Next 5Y' in df_all_competition.columns:
        try:
            eps_next_5 = df_all_competition[df_all_competition['Ticker'] == ticker]['EPS Next 5Y'].iloc[0]
            eps_next_5 = eps_next_5.replace("%", "").replace('-', "0")
            eps_next_5 = float(eps_next_5)
        except Exception:
            eps_next_5 = 0
    else:
        eps_next_5 = 0
    
    df = filter_df(df_all_competition, market_cap, past_sales_5, eps_next_5)
        
    all_dfs['all competition']=  df
    
    #for the indexes
    df_indexes = all_dfs['index competition']
    
    for i in df_indexes:
        df= filter_df(df_indexes[i], market_cap, past_sales_5, eps_next_5)
        all_dfs[i]=  df
        
    all_dfs.pop("index competition")
    
    for i in all_dfs:
        df= all_dfs[i]["Ticker"]
        all_dfs[i]= df
                
    return all_dfs

def all_values(all_dfs_clean):

    alpaca_headers = {
        "APCA-API-KEY-ID":     ALPACA_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET
    }

    def get_alpaca_price(ticker):
        try:
            url = f"https://data.alpaca.markets/v2/stocks/{ticker}/snapshot"
            r = requests.get(url, headers=alpaca_headers)
            return r.json().get("latestTrade", {}).get("p")
        except Exception:
            return None

    table_dfs = {}

    for key in all_dfs_clean:
        table = []
        for t in all_dfs_clean[key]:
            try:
                facts         = get_facts(t)
                total_debt    = get_latest_value(facts, "LongTermDebt")
                minority_interest = get_latest_value(facts, "MinorityInterest") or get_latest_value(facts, "NoncontrollingInterestMember") or 0
                total_cash    = get_latest_value(facts, "CashAndCashEquivalentsAtCarryingValue")
                total_revenue = get_latest_value(facts, "Revenues") or get_latest_value(facts, "RevenueFromContractWithCustomerExcludingAssessedTax")
                ebitda        = get_latest_value(facts, "OperatingIncomeLoss")
                shares        = get_latest_value(facts, "CommonStockSharesOutstanding")
                price         = get_alpaca_price(t)

                if not all([price, shares, total_revenue, ebitda]):
                    continue

                net_debt         = total_debt - total_cash
                market_cap       = price * shares
                enterprise_value = market_cap + net_debt
                ev_revenue       = enterprise_value / total_revenue if total_revenue else None
                ev_ebitda        = enterprise_value / ebitda if ebitda else None

                temporal_dict = {
                    "ticker":            t,
                    "market cap":        market_cap,
                    "net debt":          net_debt,
                    "minority interest": minority_interest,
                    "enterprise value":  enterprise_value,
                    "total revenue":     total_revenue,
                    "ebitda":            ebitda,
                    "ev/revenue":        ev_revenue,
                    "ev/ebitda":         ev_ebitda,
                    "shares":            shares,
                    "price":             price,
                }

            except Exception:
                continue
            table.append(temporal_dict)

        table_dfs[key] = pd.DataFrame(table)

    return table_dfs

def build_table(all_dataframes, ticker):

    b= next(iter(all_dataframes))
    c= all_dataframes[b].columns
    
    for i in c:
        if i == "price" or i== "shares":
            pass
        else:
            print(f"{i:<20}|",end=" ")

    print("")
    print("_" *20* (len(c)-1))



    for dictionary in all_dataframes:
        print("")
        print(dictionary)
        
        df= all_dataframes[dictionary]
        row= df[df["ticker"] == ticker].iloc[0]
        
        df_no_ticker = df[df["ticker"] != ticker]
        
        for i in c: # Means
            if i == "ticker":
                print(f"{"Mean":<20}|",end=" ")
                
            elif i == "ev/revenue" or i == "ev/ebitda":
                mean= round(df_no_ticker[i].mean(),2)
                print(f"{mean:<20}|",end=" ")
            
            elif i== "price" or i== "shares":
                continue
                
            else:
                mean= round(df_no_ticker[i].mean()/1e6)
                print(f"{mean:<20}|",end=" ")
                
        print("")
        
        for i in c: #Median
            
            if i == "ticker":
                print(f"{"Median":<20}|",end=" ")
                
            elif i == "ev/revenue" or i == "ev/ebitda":
                median= round(df_no_ticker[i].median(),2)
                print(f"{median:<20}|",end=" ")
            
            elif i== "price" or i== "shares":
                continue
            
            else:
                median= round(df_no_ticker[i].median()/1e6)
                print(f"{(median):<20}|",end=" ")
                
        print("")
        
        for i in c: #Ticker
            if i == "ticker":
                print(f"{ticker:<20}|",end=" ")
                
            elif i == "ev/revenue" or i == "ev/ebitda":
                val= round(row[i],2)
                print(f"{val:<20}|",end=" ")
            
            elif i== "price" or i== "shares":
                continue
            
            else:
                val= round(row[i]/1e6)
                print(f"{(val):<20}|",end=" ")
                
        print("")
        print("- " *int(20/2)* (len(c)-1))
        
        df_no_ticker = df_no_ticker.copy()
        ev_ex= row["ebitda"]* df_no_ticker["ev/ebitda"].median()
        row["enterprise value"]= ev_ex
        row["market cap"]= ev_ex - row["net debt"] - row["minority interest"]
        row["ev/ebitda"]= df_no_ticker["ev/ebitda"].median()
                
        for i in c: #Expected
            
            if i == "ticker":
                print(f"{"Expected":<20}|",end=" ")
            
            elif i == "ev/revenue" or i == "ev/ebitda":
                val= round(row[i],2)
                print(f"{round(val,2):<20}|",end=" ")
                
            elif i== "price" or i== "shares":
                continue
            
            else:
                val= round(row[i]/1e6)
                print(f"{(round(val,2)):<20}|",end=" ")
                
        
        print("\n", "_" *20 *(len(c)-1))
        
def relative_valuation(ticker):
    
    stock_dict= company_data(ticker)
    print("Company data done")
    stock_areas= get_company_area(stock_dict)
    print("Company areas done")
    all_dfs= get_competition(stock_areas)
    print("Company competition done")
    all_dfs_clean= clean_dfs(all_dfs, ticker) 
    print("Company df clean done")   
    all_dataframes = all_values(all_dfs_clean, ticker)
    print("Company all values done")
    build_table(all_dataframes, ticker)
    
def streamlit_df(all_dataframes, ticker):
    
    streamlit_dfs = {}
    
    for i in all_dataframes:
        df = all_dataframes[i]
        
        if "ticker" in df.columns:
            df = df.set_index("ticker")
        df = df.drop(columns=["shares", "price"], errors="ignore")
        
        stocks   = df.loc[ticker]
        means    = df.mean(numeric_only=True)
        medians  = df.median(numeric_only=True)
        expected = df.loc[ticker].copy()
        
        expected["enterprise value"] = stocks["ebitda"] * medians["ev/ebitda"]
        expected["market cap"]       = expected["enterprise value"] - stocks["net debt"] - stocks["minority interest"]
        expected["ev/ebitda"]        = medians["ev/ebitda"]
        expected["ev/revenue"]       = expected["enterprise value"] / expected["total revenue"]

        comparison_df = pd.DataFrame({
            "Mean":     means,
            "Median":   medians,
            ticker:     stocks,
            "Expected": expected,
        }).T
        
        streamlit_dfs[i] = comparison_df
    
    return streamlit_dfs
    

# ── P7: DCF model ────────────────────────────────────────────────────────────────

def get_company_dcf_data(ticker, verbose=False):

    facts = get_facts(ticker)

    # ── Find latest 10-K year ────────────────────────────────────────
    entries = facts.get("OperatingIncomeLoss", {}).get("units", {}).get("USD", [])
    annual  = [e for e in entries if e.get("form") == "10-K"]
    annual  = sorted(annual, key=lambda x: x["end"], reverse=True)
    year    = annual[0]["end"][:4] if annual else None
    if not year:
        return None

    # ── Core financials from EDGAR ───────────────────────────────────
    operating_income = get_latest_value(facts, "OperatingIncomeLoss")

    dep_am = 0
    for tag in ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation"]:
        val = get_latest_value(facts, tag)
        if val:
            dep_am = val
            break

    ebitda = operating_income + dep_am

    CAPEX = abs(get_latest_value(facts, "PaymentsToAcquirePropertyPlantAndEquipment") or
                get_latest_value(facts, "CapitalExpenditures") or 0)

    # ── NWC ──────────────────────────────────────────────────────────
    def get_value_by_year(facts, concept, target_year):
        try:
            entries = facts[concept]["units"]["USD"]
            annual  = [e for e in entries if e.get("form") == "10-K"]
            annual  = sorted(annual, key=lambda x: x["end"], reverse=True)
            for e in annual:
                if e["end"][:4] == target_year:
                    return e["val"]
            return None
        except Exception:
            return None

    assets_curr   = get_value_by_year(facts, "AssetsCurrent", year)
    liab_curr     = get_value_by_year(facts, "LiabilitiesCurrent", year)
    assets_prev   = get_value_by_year(facts, "AssetsCurrent", str(int(year)-1))
    liab_prev     = get_value_by_year(facts, "LiabilitiesCurrent", str(int(year)-1))

    NWC       = (assets_curr - liab_curr)   if (assets_curr and liab_curr)   else 0
    NWC_1     = (assets_prev - liab_prev)   if (assets_prev and liab_prev)   else 0
    NWC_change = NWC - NWC_1

    # ── Tax rate ─────────────────────────────────────────────────────
    tax_exp   = get_latest_value(facts, "IncomeTaxExpenseBenefit")
    pretax    = get_latest_value(facts, "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest")
    tax_rate  = (tax_exp / pretax) if (tax_exp and pretax and pretax != 0) else 0.21
    tax_rate  = 0.21 if (tax_rate < 0 or tax_rate > 0.40) else tax_rate

    # ── WACC inputs ──────────────────────────────────────────────────
    try:
        beta = round(calculate_beta(ticker), 2)
    except:
        beta = 1.0

    shares      = get_latest_value(facts, "CommonStockSharesOutstanding")
    total_debt  = get_latest_value(facts, "LongTermDebt") or 0
    cash        = get_latest_value(facts, "CashAndCashEquivalentsAtCarryingValue") or 0
    interest_expense = abs(get_latest_value(facts, "InterestExpense") or 0)

    # ── Price from Alpaca ────────────────────────────────────────────
    alpaca_headers = {
        "APCA-API-KEY-ID":     ALPACA_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET
    }
    snap        = requests.get(f"https://data.alpaca.markets/v2/stocks/{ticker}/snapshot", headers=alpaca_headers).json()
    share_price = snap.get("latestTrade", {}).get("p")
    market_cap  = share_price * shares

    # ── 10yr treasury from FRED ──────────────────────────────────────
    fred = requests.get(f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&sort_order=desc&limit=1&api_key={FRED_KEY}&file_type=json")
    bond_10yr = float(fred.json()["observations"][0]["value"]) / 100

    confidence = "high" if (operating_income != 0 and dep_am != 0) else "low"

    if verbose:
        print(f"Using          {ticker}, {year} financial year")
        print(f"Confidence:    {confidence}, \n")
        print(f"Market cap:    {market_cap/1e6:.1f}M")
        print(f"Shares:        {shares}")
        print(f"Share price:   {share_price}")
        print(f"Cash:          {cash/1e6:.1f}M")
        print(f"InterestExp:   {interest_expense/1e6:.1f}M,\n")
        print(f"Total debt:    {total_debt/1e6:.1f}M,\n")
        print(f"EBITDA:        {ebitda/1e6:.1f}M")
        print(f"Ebit:          {operating_income/1e6:.1f}M")
        print(f"D&A:           {dep_am/1e6:.1f}M ")
        print(f"CAPEX:         {CAPEX/1e6:.1f}M")
        print(f"NWC change:    {NWC_change/1e6:.1f}M")
        print(f"tax_rate:      {tax_rate:.1%}")
        print("-"*50)

    return {
        "operating_income": operating_income,
        "dep_am":           dep_am,
        "ebitda":           ebitda,
        "CAPEX":            CAPEX,
        "NWC":              NWC,
        "NWC_change":       NWC_change,
        "tax_rate":         tax_rate,
        "cash":             cash,
        "market_cap":       market_cap,
        "shares":           shares,
        "share_price":      share_price,
        "beta":             beta,
        "total_debt":       total_debt,
        "interest_expense": interest_expense,
        "bond_10yr":        bond_10yr,
        "year":             year,
        "confidence":       confidence
    }
    
def forecast_unlevered_FCF(c_data, year= 5, g= .05, verbose= False):
    
    fcf_list=[]
    
    FCF=  c_data["operating_income"] * (1- c_data["tax_rate"]) + c_data["dep_am"] - c_data["NWC_change"] - c_data["CAPEX"]
    
    FCF_normalized = c_data["ebitda"] - c_data["CAPEX"]
    
    for i in range (1, year+1):   
        yr_fcf = FCF_normalized * (1 + g) ** i
        fcf_list.append(yr_fcf)
    
    if verbose:
        print(f"{'Year 0 (actual)':<20} ", end=" ")
        print(f"{'Year 0 (normalized)':<20} ", end=" ")
        for i in range(len(fcf_list)):
            print(f"{'Year ' + str(i+1):<20}", end=" ")
        print("")

        print(f"{round(FCF/1e6):<20} ", end=" ")
        print(f"{round(FCF_normalized/1e6):<20} ", end=" ")
        for i in range(len(fcf_list)):
            val = round(fcf_list[i] / 1e6)
            print(f"{val:<20}", end=" ")
        print("\n")
        print("-" * 50)
        print("\n")
    
    return fcf_list

def get_wacc(c_data, equity_risk_premium=.05, verbose= False):
    
    cost_of_equity = c_data["bond_10yr"]+ c_data["beta"]* equity_risk_premium

    cost_debt= c_data["interest_expense"]/c_data["total_debt"]
    cost_debt_aftertax= cost_debt * (1-c_data["tax_rate"])

    enterprise_value= c_data["market_cap"] + c_data["total_debt"]

    WACC = (c_data["market_cap"] / enterprise_value) * cost_of_equity + (c_data["total_debt"] / enterprise_value) * cost_debt_aftertax
    
    if verbose: 
        print(f"Parameters   ")
        print(f"Bond rate:                 {c_data["bond_10yr"]:.1%}")
        print(f"Beta:                      {c_data["beta"]}")
        print(f"equity_risk_premium:       {equity_risk_premium:.1%}")
        print(f"cost_of_equity:            {cost_of_equity:.1%},\n")
        print(f"cost_debt:                 {cost_debt:.2%}")
        print(f"cost_debt_aftertax:        {cost_debt_aftertax:.2%},\n")
        print(f"enterprise_value:          {enterprise_value/1e6:.1f}M")
        print(f"WACC:                      {WACC:.1%}")
        print("-"*50)
        print("")

    return WACC

def terminal_value(last_fcf, wacc, g_longterm= .025):
    
    TV= (last_fcf *(1 + g_longterm) /(wacc - g_longterm))
    
    return TV

def discount_FCF_WACC(fcf_list, WACC, g_longterm= .025, verbose= False ):
    
    fcf_projected= [fcf / (1 + WACC)** i for  i , fcf in enumerate (fcf_list, 1)] 
    TV      = terminal_value(fcf_list[-1], WACC, g_longterm= g_longterm)
    pv_TV   = TV / (1 + WACC) ** 5
    enterprise_value  = sum(fcf_projected) + pv_TV
    
    if verbose:
        print(f"Terminal Value:    {round(TV/1e6, 2)}M")
    
    return enterprise_value

def final_details(c_data, enterprise_value, verbose= False):
    
    equity_value= enterprise_value - c_data["total_debt"]+ c_data["cash"]
    intrinsic_price= equity_value/ c_data["shares"]
    
    if verbose:
        print(f"intrinsic price:      {round(intrinsic_price,2)} $")
        print(f"current price:        {round(c_data["share_price"],2)} $")
        print(f"diference price:      {round(c_data["share_price"]- intrinsic_price,2)} $")
    
    return intrinsic_price

def calculate_beta(ticker, period="1y"):

    alpaca_headers = {
        "APCA-API-KEY-ID":     ALPACA_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET
    }

    end   = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")
    start = (pd.Timestamp.now(tz="UTC") - pd.DateOffset(years=1)).strftime("%Y-%m-%d")

    def get_prices(t):
        url    = f"https://data.alpaca.markets/v2/stocks/{t}/bars"
        params = {"timeframe": "1Day", "start": start, "end": end, "limit": 1000, "feed": "iex"}
        r      = requests.get(url, headers=alpaca_headers, params=params)
        bars   = r.json().get("bars", [])
        return pd.Series({b["t"]: b["c"] for b in bars})

    stock_prices = get_prices(ticker)
    spy_prices   = get_prices("SPY")

    df = pd.DataFrame({"stock": stock_prices, "market": spy_prices}).dropna()
    df = df.pct_change().dropna()

    covariance = df.cov().iloc[0, 1]
    variance   = df["market"].var()

    return covariance / variance
      
def sensitivity_DCF(ticker, year=5,equity_risk_premium=.025,g_longterm=0.025, verbose= False):

    total=[]
    c_data= get_company_dcf_data(ticker, verbose= verbose)

    g_vals   = np.arange(0.05, 0.45, 0.05)
    wacc_vals = np.arange(0.05, 0.21, 0.01)


    for i in g_vals:
        
        rows= []
        
        for j in wacc_vals:
            
            fcf_list= forecast_unlevered_FCF(c_data, g= i, year= year,verbose= False)
            enterprise_value= discount_FCF_WACC( fcf_list, WACC= j, verbose=False, g_longterm=g_longterm)
            intrinsic_price= final_details(c_data, enterprise_value, verbose= False)
            rows.append(round(intrinsic_price, 2))

        total.append(rows)
            

    df = pd.DataFrame(total,
                columns=[f"WACC {w:.0%}" for w in wacc_vals],
                index=[f"Growth Rate {g:.0%}" for g in g_vals])

    
    current_price= c_data["share_price"]
    
    def highlight_dcf(val):

        if val >  current_price * 1.1:
            return "background-color: #d4edda ; color: black "
        elif val < current_price * .9:
            return "background-color: #f8d7da; color: black"
        else:      
            return "background-color: #fff3cd; color: black "

    print(f"\n[{ticker}] Current Price: ${current_price}")
    return df.style.map(highlight_dcf).format("{:.2f}")

def DCF_Model(ticker, verbose= False, g=.1):    
    
    c_data= get_company_dcf_data(ticker, verbose= verbose)
    
    fcf_list= forecast_unlevered_FCF(c_data, g= g,verbose= verbose)
    
    WACC= get_wacc(c_data, verbose= verbose)
    
    enterprise_value= discount_FCF_WACC( fcf_list, WACC, verbose=verbose, g_longterm=.025)
    
    intrinsic_price= final_details(c_data, enterprise_value, verbose= verbose)

    sensitivity_DCF(ticker, verbose= verbose)

    return intrinsic_price

# ── P8 Black Scholes ────────────────────────────────────────────────────────────────

class BlackScholes:
    def __init__(self, S, K, T, r, o, call= True):
        
        self.S = S
        self.K = K
        self.T = T/365
        self.r = r
        self.o = o
        self.call = call
        
        self.d1 = (math.log(S/K) + (r + (o**2)/2) * self.T)/ (o * math.sqrt(self.T))
        self.d2 = self.d1 - o * math.sqrt(self.T)
        self.disc = math.exp(-r * self.T)
        
    def delta(self):
        if self.call:
            return norm.cdf(self.d1) 
        return norm.cdf(self.d1) - 1
    
    def gamma(self):
        return norm.pdf(self.d1)/ (self.S * self.o * math.sqrt(self.T))
    
    def theta(self):
        base= (-self.S * norm.pdf(self.d1) * self.o / (2 * math.sqrt(self.T)))
        if self.call:
            return base - (self.r * self.K * math.exp(-self.r * self.T) * norm.cdf(self.d2))  
        return     base + (self.r * self.K * math.exp(-self.r * self.T) * norm.cdf(-self.d2))
    
    def vega(self):
        return  self.S * norm.pdf(self.d1) * math.sqrt(self.T)
    
    def rho(self):
        if self.call:
            return self.K * self.T * math.exp(-self.r * self.T) * norm.cdf(self.d2)
        return    -self.K * self.T * math.exp(-self.r * self.T) * norm.cdf(-self.d2)
    
    def price(self):
        if self.call:
            return self.S * norm.cdf(self.d1) - self.K * self.disc * norm.cdf(self.d2)
        return self.K * self.disc * norm.cdf(-self.d2) - self.S * norm.cdf(-self.d1)
    
    def bid_ask(self, spread=0.05):
        mid = self.price()
        return {
            "mid" : mid,
            "bid" : mid - spread / 2,
            "ask" : mid + spread / 2
        }
    
    def greeks(self):
        return {
        "delta": self.delta(),
        "gamma": self.gamma(),
        "theta": self.theta(), 
        "vega": self.vega(),
        "rho": self.rho()
        }
        
    def opcion_chain_values(self):
        return {
        "delta": self.delta(),
        "gamma": self.gamma(),
        "theta": self.theta(), 
        "vega": self.vega(),
        "bid": self.bid_ask()["bid"],
        "ask": self.bid_ask()["ask"]
        }
        
def opcion_chain(S, K, T, r, o, spacing= 2.5):
    
    start = int(S * 0.5) - (int(S * 0.5) % spacing)
    Ks = np.arange(start, round(S * 1.5), spacing)
    call_vals = [BlackScholes(S, k, T, r, o, call=True).opcion_chain_values() for k in Ks]
    df_calls= pd.DataFrame(call_vals, index=Ks.round(1))
    

    put_vals = [BlackScholes(S, k, T, r, o, call=False).opcion_chain_values() for k in Ks]
    df_puts= pd.DataFrame(put_vals, index=Ks.round(1))
    df_puts= df_puts[df_puts.columns[::-1]]
    
    df_calls.columns = [c + " (c)" for c in df_calls.columns]
    df_puts.columns  = [c + " (p)" for c in df_puts.columns]
    df_strike = pd.DataFrame({"strike": Ks.round(1)}, index=Ks.round(1))

    chain= pd.concat([df_calls,df_strike, df_puts], axis= 1)
    
    closest = np.argsort(np.abs(Ks - S))[:11]
    closest = np.sort(closest)
    chain = chain.iloc[closest]

    
    return chain

def highlight_opt_chain(row):
    if row["strike"] == K:
        return ["background-color: rgba(255,255,0,0.2)"] * len(row)
    return [""] * len(row)

def get_prices_opcions(ticker, days=252):
    url = f"https://data.alpaca.markets/v2/stocks/{ticker}/bars"
    start = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    params = {
        "timeframe": "1Day",
        "limit": days,
        "start": start,  # ← add this
        "feed": "iex"           # ← add this, free tier
    }
    headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
    
    r = requests.get(url, params=params, headers=headers)
    bars = r.json().get("bars")
    
    if not bars:
        st.error(f"No data found for ticker: {ticker}")
        st.stop()
    
    return [bar["c"] for bar in bars]

# ── P9 Volatility Surface ────────────────────────────────────────────────────────────────

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
        rows.append({
            "expiry"  : f"20{expiry[:2]}-{expiry[2:4]}-{expiry[4:]}",
            "strike"  : int(strike) / 1000,
            "type"    : "call" if call_put == "C" else "put",
            "mid"     : (o["bid"] + o["ask"]) / 2,
            "iv"      : o["iv"],
            "delta"   : o["delta"],
            "gamma"   : o["gamma"],
            "theta"   : o["theta"],
            "vega"    : o["vega"],
            "volume"  : o["volume"],
            "oi"      : o["open_interest"]
        })
    return pd.DataFrame(rows)

def filter_surface_df(df, S, strike_range= .05, n_expiracies= 10):

    df = df[(df["strike"] >= S * (1 - strike_range)) & (df["strike"] <= S * (1 + strike_range))]
    df = df[df["iv"] > 0]
    
    next_10 = sorted(df["expiry"].unique())
    next_10 = next_10[:n_expiracies] 
    
    df = df[df["expiry"].isin(next_10)]
    
    OTM_puts= df[(df["type"] == "put")  & (df["strike"] < S)]
    OTM_calls= df[(df["type"] == "call")  & (df["strike"] > S)]
    
    surface_df = pd.concat([OTM_puts, OTM_calls]).sort_values(["expiry", "strike"])
    surface_df= surface_df[["expiry", "strike", "iv"]]
    
    return surface_df

def surface_vol_builder(surface_df):

    pivot = surface_df.pivot_table(index="expiry", columns="strike", values="iv").interpolate(method= "linear", axis= 0).bfill().ffill()

    fig = go.Figure(data=[go.Surface(
        x=pivot.columns.values,  # strikes
        y=pivot.index.values,    # days
        z=pivot.values,          # IV matrix
        colorscale="Viridis"
    )])

    fig.update_layout(
        title="Volatility Surface",
        scene=dict(
            xaxis_title="Strike",
            yaxis_title="Days to Expiry",
            zaxis_title="IV"
        ),
        template="plotly_dark"
    )

    return fig
    
def smile_vol(surface_df, S):
    next_1 = sorted(surface_df["expiry"].unique())[:1]
    df = surface_df[surface_df["expiry"].isin(next_1)]
    
    smile = df[["strike", "iv"]].reset_index(drop=True)
    
    fig, ax = plt.subplots()
    ax.plot(smile["strike"], smile["iv"])
    ax.axvline(x=S, color="red", linestyle="--", alpha=0.7, label=f"S = {S}")
    ax.legend()
    ax.set_xlabel("Strike")
    ax.set_ylabel("IV")
    ax.set_title(f"Vol Smile — {next_1[0]}")
    
    return fig
def full_surface_pipeline(ticker, **kwargs):
    
    data       = get_all_chains(ticker)
    df         = parse_chain(data)
    prices     = get_price(ticker)
    S          = prices[-1]
    
    surface_df  = filter_surface_df(df, S, **kwargs)
    surface_fig = surface_vol_builder(surface_df)
    smile_fig   = smile_vol(surface_df)
    
    return surface_fig, smile_fig, surface_df