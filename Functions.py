# Functions.py
from finvizfinance.quote import finvizfinance
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.valuation import Valuation
from finvizfinance.screener.financial import Financial
import pandas as pd
import numpy as np
from edgar import *
import yfinance as yf
from IPython.display import display
set_identity("ikergogiga@gmail.com")

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

def ebitdas(c_name):

    company = Company(c_name)
    financials = company.get_financials()
    df_inc  = company.income_statement().to_dataframe()
    df_cash = company.cashflow_statement().to_dataframe()

    # ── Find year column (handle FY and non-FY formats) ──────────────
    year_cols = [c for c in df_inc.columns if "FY" in c]
    if not year_cols:
        # fallback: take first numeric-looking column
        year_cols = [c for c in df_inc.columns if any(ch.isdigit() for ch in str(c))]
    if not year_cols:
        print(f" {c_name}: no year columns found. Columns: {df_inc.columns.tolist()}")
        return None
    year = year_cols[0]
    print(f"Using year: {year}")

    # ── Operating Income ─────────────────────────────────────────────
    a = df_inc.loc[df_inc.index.str.contains("OperatingIncomeLoss", na=False), year]
    operating_income = int(a.iloc[0]) if not a.empty else 0

    # ── D&A ──────────────────────────────────────────────────────────
    dep_am = 0
    for tag in ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation"]:
        a = df_cash.loc[df_cash.index.str.contains(tag, na=False), year]
        if not a.empty and pd.notna(a.iloc[0]):
            dep_am = a.iloc[0]
            break

    # ── EBITDA ───────────────────────────────────────────────────────
    ebitda = operating_income + dep_am
    print(f"{c_name} | {year} | Op.Income: {operating_income/1e6:.1f}M | D&A: {dep_am/1e6:.1f}M | EBITDA: {ebitda/1e6:.1f}M")

    confidence = "high" if (operating_income != 0 and dep_am != 0 and "2024" not in str(year)) else "low"

    return {
        "operating_income": operating_income,
        "dep_am":           dep_am,
        "ebitda":           ebitda,
        "year":             year,
        "confidence":       confidence
    }
    
def funds_table(ebitda_results, entry_multiple=10, pct_debt=0.70,
                pct_senior=0.60, pct_sub=0.40,
                transaction_fee_pct=0.02, financing_fee_pct=0.035,
                mgmt_rollover_pct=0.10, verbose= False):
    
    ebitda= ebitda_results["ebitda"]
    
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
        "transaccion fees":transaccion_fees,
        "financing fees": financing_fees,
        "total uses": total_uses,
        "--SOURCES-----------------":"",
        "senior debt":senior_debt,
        "Sub/ HY debt": sub_debt,
        "total debt": total_debt,
        "managment rollover":managment_rollover,
        "sponsor equity":sponsor_equity,
        "Total Sources":total_debt+ managment_rollover + sponsor_equity,
        "--CHECKS------------------":"",
        "Total Debt / EBITDA": f"{total_debt_x:.1f}x",
        "Senior Debt / EBITDA": f"{senior_debt_x:.1f}x",
        "Equity %": f"{(equity_requirement / total_uses):.1%}",
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
    company = Company(c_name)
    financials = company.get_financials()

    df_cash= company.cashflow_statement().to_dataframe()
    df_bal=company.balance_sheet().to_dataframe()
    df_inc=company.income_statement().to_dataframe()

    year_cols = [c for c in df_cash.columns if "FY" in c]
    year = year_cols[0]
    year_prev= year_cols[1]

    #--------Getting values---------
    CAPEX = 0
    for tag in ["PaymentsToAcquirePropertyPlantAndEquipment","CapitalExpenditures"]:
        a = df_cash.loc[df_cash.index.str.contains(tag, na=False), year]
        if not a.empty and pd.notna(a.iloc[0]):
            CAPEX = a.iloc[0]
            break  

    assets_m = df_bal.loc[df_bal.index == "AssetsCurrent"]
    liab_m   = df_bal.loc[df_bal.index == "LiabilitiesCurrent"]
    NWC = (assets_m[year].iloc[0] - liab_m[year].iloc[0]) if (not assets_m.empty and not liab_m.empty) else None
    NWC_1 = (assets_m[year_prev].iloc[0] - liab_m[year_prev].iloc[0]) if (not assets_m.empty and not liab_m.empty) else None
    
    NWC_change= (NWC - NWC_1)

    tax_m    = df_inc.loc[df_inc.index == "IncomeTaxExpenseBenefit"]
    pretax_m = df_inc.loc[df_inc.index.str.contains("IncomeLossFromContinuingOperationsBeforeIncomeTaxes", na=False)]
    tax_rate = (tax_m[year].iloc[0] / pretax_m[year].iloc[0]) if (not tax_m.empty and not pretax_m.empty and pretax_m[year].iloc[0] != 0) else None
    
    if CAPEX == 0 or NWC is None:
        tax_rate=.25
        confidence= "low"
    else:
        confidence= "high"
    
    print(f"{c_name} | {year}")
    print(f"  CapEx:      {CAPEX/1e6:.1f}M")
    print(f"  NWC:        {NWC/1e6:.1f}M" if NWC is not None else "  NWC:      ⚠️ not found")
    print(f"  NWC_change: {NWC_change/1e6:.1f}M" if NWC_change is not None else "  NWC:      ⚠️ not found")
    print(f"  Tax rate:   {tax_rate:.1%}" if tax_rate is not None else "  Tax rate: ⚠️ not found")
    print(f"  Confidence: {confidence}  ")
    print("-----------------------------------------------")
    
    return {
        "CAPEX":            CAPEX,
        "NWC":              NWC,
        "NWC_change":       NWC_change,
        "tax_rate":         tax_rate,
        "year":             year,
        "confidence":       confidence
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
                  amort_pct=.05, sweep_pct= .5, years= 5):
    
    origianl_senior= funds_results["senior debt"]
    beginning_senior= origianl_senior
    original_sub= funds_results["Sub/ HY debt"]
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
    
def returns(fcf_results, debt_results, funds_results, exit_multiple= 9, years= 5, verbose= False ):
    
    ebitda_last_year= fcf_results["ebitda_list"][-1]
    remaining_debt= debt_results["total_debt_list"][-1]
    sponsor_equity= funds_results[ "sponsor equity"]
    
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
            "sponsor_equity_M":round(d["sponsor equity"] / 1e6, 1),
            "IRR":             round(f["IRR"] * 100, 1),
            "MoM":             round(f["MoM"], 2),
            "pass":            f["IRR"] > 0.20,
            "confidence":      a["confidence"]
        }
    except Exception as ex:
        print(f"⚠️ {c_name} failed: {ex}")
        return None
    
def compare_entries_exits(c_name, verbose=False):
    
    a = ebitdas(c_name)
    b = fcf_data(c_name)
    c = fcf_model(a, b)
    total= []
    
    for i in range(5, 11):
        rows= []
        for j in range(5,11):
            d = funds_table(a, entry_multiple=j, verbose= verbose)
            e = debt_schedule(d, c)
            f = returns(c, e, d, exit_multiple= i, verbose= verbose)
            rows.append(round(f["IRR"]*100,1))
            
        total.append(rows)
        
    df = pd.DataFrame(total, columns = [f"Entry {x}" for x in range(5, 11)], index   = [f"Exit {x}"  for x in range(5, 11)])
    
    df.style.format("{:.1f}%").applymap(highlight_irr)
       
    return df
    
def highlight_irr(val):
    if val >= 25:
        return "background-color: #d4edda !important; color: black !important"
    elif val >= 20:
        return "background-color: #fff3cd !important; color: black !important"
    else:
        return "background-color: #f8d7da !important; color: black !important"


# ── P5: Accretion dilution Model ────────────────────────────────────────────────────────────────

def get_companys_datas(acq, tgt, verbose= False):

    acq_dict = yf.Ticker(acq).info
    tgt_dict = yf.Ticker(tgt).info
    
    if verbose == False: 
        pass
    else:
        print(f"{"values":<15} | {acq_dict["symbol"]:<25} | {tgt_dict["symbol"]:<25}")
        print("-"*60)
        print(f"{"Market cap":<15} | {round(acq_dict["marketCap"]):<25,} | {round(tgt_dict["marketCap"]):<25,}")
        print(f"{"Price":<15} | {acq_dict["previousClose"]:<25} | {tgt_dict["previousClose"]:<25}")
        print(f"{"Shares":<15} | {acq_dict["sharesOutstanding"]:<25} | {tgt_dict["sharesOutstanding"]:<25}\n\n")

    return acq_dict, tgt_dict

def contract_offer(acq_dict, tgt_dict, offer_premium=.60, stock_pct=0.50, tax_rate=0.40,
                   years= 5, interest_rate= 0.05, financing_fees_pct=.035,transaccion_fees_pct= .02, 
                   synergies_pct=0, amortization_years= 10, verbose=False ):
    
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
    acq_implide_net_inc= acq_dict["sharesOutstanding"]* acq_dict["epsCurrentYear"]
    tgt_implide_net_inc= tgt_dict["sharesOutstanding"]* tgt_dict["epsCurrentYear"]
    acq_implide_pretax_inc= acq_implide_net_inc /(1-tax_rate)
    tgt_implide_pretax_inc= tgt_implide_net_inc /(1-tax_rate)
    
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
    accretion_dilution_per_share= proforma_eps - acq_dict["epsCurrentYear"]
    accretion_dilution_pct= (proforma_eps / acq_dict["epsCurrentYear"])-1
    
    if verbose == False:
        pass
    else: 
        print("Parameters:")
        print(f"Offer premium:            | {offer_premium*100}%")
        print(f"% of cash:                | {cash_pct*100}%")
        print(f"% of stock:               | {stock_pct*100}%")
        print(f"tax rate:                 | {tax_rate*100}%")
        print(f"interest rate:            | {interest_rate*100}%")
        print(f"% financing fees:         | {transaccion_fees_pct*100}%")
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
    
    return accretion_dilution_pct

def highlight_irr_accdil(val):
    if val >= 0:
        return "background-color: #d4edda !important; color: black !important"
    elif val >= -.05:
        return "background-color: #fff3cd !important; color: black !important"
    else:
        return "background-color: #f8d7da !important; color: black !important"
    
def sensitivity_accretion_dilution(acq, tgt,verbose= False, steps= 1):
    
    rows= []
    for i in range (0, 11, steps):
        row= []
        for j in range(0, 11, steps):

            accretion_dilution_pct= round(contract_offer(acq, tgt, offer_premium=i/10, stock_pct= j/10, verbose=False), ndigits= 2)
            
            row.append(accretion_dilution_pct)
            
        rows.append(row)
    
    df= df = pd.DataFrame(rows, columns = [f"Stock {x*10}%" for x in range(0, 11, steps)], index   = [f"Offer premium {x*10}%"  for x in range(0, 11, steps)])
    styled= df.style.format("{:.2f}%").map(highlight_irr_accdil)
    display(styled)
    
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

def all_values(all_dfs_clean, ticker):
   
    table_dfs = {}

    for key in all_dfs_clean: 
        table = []
        for t in all_dfs_clean[key]:  # t is each ticker string
            try:
                
                yfin = yf.Ticker(t).info
                market_cap = yfin.get('marketCap')
                total_debt = yfin.get('totalDebt', 0)
                total_cash = yfin.get('totalCash', 0)
                net_debt = total_debt - total_cash
                enterprise_value = yfin.get('enterpriseValue')
                minority_interest = enterprise_value - market_cap - net_debt
                total_revenue = yfin.get('totalRevenue')
                ebitda = yfin.get('ebitda')
                ev_revenue = enterprise_value / total_revenue
                ev_ebitda = enterprise_value / ebitda
                shares= yfin.get("sharesOutstanding")
                price=yfin.get("previousClose")
                
                temporal_dict = {
                    "ticker": t,  # peer ticker not subject
                    'market cap': market_cap,
                    'net debt': net_debt,
                    'minority interest': minority_interest,
                    'enterprise value': enterprise_value,
                    'total revenue': total_revenue,
                    'ebitda': ebitda,
                    'ev/revenue': ev_revenue,
                    'ev/ebitda': ev_ebitda, 
                    'shares':shares,
                    'price':price
  
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
    

# ── P7: DCF model ────────────────────────────────────────────────────────────────

def get_company_dcf_data(ticker, verbose= False):
    
    company = Company(ticker)
    financials = company.get_financials()
    df_inc  = company.income_statement().to_dataframe()
    df_cash = company.cashflow_statement().to_dataframe()
    df_bal=company.balance_sheet().to_dataframe()
    yfin_ticker = yf.Ticker(ticker)
    info   = yfin_ticker.info

    # ── Find year column (handle FY and non-FY formats) ──────────────
    year_cols = [c for c in df_inc.columns if "FY" in c]
    if not year_cols:
        # fallback: take first numeric-looking column
        year_cols = [c for c in df_inc.columns if any(ch.isdigit() for ch in str(c))]
    if not year_cols:
        print(f" {ticker}: no year columns found. Columns: {df_inc.columns.tolist()}")
        return None
    year = year_cols[0]
    year_prev= year_cols[1]
    

    # ── Operating Income ─────────────────────────────────────────────
    a = df_inc.loc[df_inc.index.str.contains("OperatingIncomeLoss", na=False), year]
    operating_income = int(a.iloc[0]) if not a.empty else 0

    # ── D&A ──────────────────────────────────────────────────────────
    dep_am = 0
    for tag in ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation"]:
        a = df_cash.loc[df_cash.index.str.contains(tag, na=False), year]
        if not a.empty and pd.notna(a.iloc[0]):
            dep_am = a.iloc[0]
            break

    # ── EBITDA ───────────────────────────────────────────────────────
    ebitda = operating_income + dep_am

    
    # ── CAPEX ───────────────────────────────────────────────────────
    CAPEX = abs(yfin_ticker.cashflow.loc["Capital Expenditure"].iloc[0] )
    for tag in ["PaymentsToAcquirePropertyPlantAndEquipment","CapitalExpenditures"]:
        a = df_cash.loc[df_cash.index.str.contains(tag, na=False), year]
        if not a.empty and pd.notna(a.iloc[0]):
            CAPEX = a.iloc[0]
            break
    
    # ── NWC ───────────────────────────────────────────────────────
    assets_m = df_bal.loc[df_bal.index == "AssetsCurrent"]
    liab_m   = df_bal.loc[df_bal.index == "LiabilitiesCurrent"]
    NWC = (assets_m[year].iloc[0] - liab_m[year].iloc[0]) if (not assets_m.empty and not liab_m.empty) else None
    NWC_1 = (assets_m[year_prev].iloc[0] - liab_m[year_prev].iloc[0]) if (not assets_m.empty and not liab_m.empty) else None
    NWC_change= (NWC - NWC_1)
    
    # ── TAX RATE ───────────────────────────────────────────────────────
    tax_m    = df_inc.loc[df_inc.index == "IncomeTaxExpenseBenefit"]
    pretax_m = df_inc.loc[df_inc.index.str.contains("IncomeLossFromContinuingOperationsBeforeIncomeTaxes", na=False)]
    tax_rate = (tax_m[year].iloc[0] / pretax_m[year].iloc[0]) if (not tax_m.empty and not pretax_m.empty and pretax_m[year].iloc[0] != 0) else None
    tax_rate = 0.21 if (tax_rate < 0 or tax_rate > 0.40) else tax_rate
    
    
    # ──WACC EXTRA DATA ─────────────────────────────────────────────────────── 
    try:
        beta = round(calculate_beta(ticker),2)
    except:
        beta= info["beta"] 
        
    market_cap = info["marketCap"]
    total_debt = yfin_ticker.balance_sheet.loc["Total Debt"].iloc[0]
    
    try:
        interest_expense    = yfin_ticker.financials.loc["Interest Expense"].iloc[0]
        interest_expense = 0 if np.isnan(interest_expense) else abs(interest_expense)
    except:
        interest_expense = 0
        print(f"interest expense missing — so 0 used for {ticker}")
    
    
    # ──TRESURY BOND PRICE ───────────────────────────────────────────────────────  
    tnx = yf.Ticker("^TNX")
    data = tnx.history(period="1d")
    bond_10yr= data["Close"].iloc[-1]/100
    
    # ──CASH ─────────────────────────────────────────────────────── 
    cash = yfin_ticker.balance_sheet.loc["Cash And Cash Equivalents"].iloc[0]
    shares= info["sharesOutstanding"]
    share_price= info["previousClose"]
    
    confidence = "high" if (operating_income != 0 and dep_am != 0 and "2024"  not in str(year)) else "low"
        
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
        print("")


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

def calculate_beta (ticker,market= "^GSPC", period = "1y"):
    
    stock= yf.Ticker(ticker).history(period=period)["Close"].pct_change()
    mkt= yf.Ticker(market).history(period=period)["Close"].pct_change()
    
    df= pd.DataFrame({"market": mkt, "stock":stock}).dropna()
    
    covariance = df.cov().iloc[0, 1]
    variance   = df["market"].var()
    
    return covariance / variance
      
def sensitivity_DCF(ticker, verbose= False):

    total=[]
    c_data= get_company_dcf_data(ticker, verbose= verbose)

    g_vals   = np.arange(0.05, 0.45, 0.05)
    wacc_vals = np.arange(0.05, 0.21, 0.01)


    for i in g_vals:
        
        rows= []
        
        for j in wacc_vals:
            
            fcf_list= forecast_unlevered_FCF(c_data, g= i,verbose= False)
            enterprise_value= discount_FCF_WACC( fcf_list, WACC= j, g=i, verbose=False, g_longterm=.025)
            intrinsic_price= final_details(c_data, enterprise_value, verbose= False)
            rows.append(round(intrinsic_price, 2))

        total.append(rows)
            
    df = pd.DataFrame(total,
                    columns=[f"{w:.0%}" for w in wacc_vals],
                    index=[f"{g:.0%}" for g in g_vals])

    current_price= c_data["share_price"]

    def highlight_dcf(val):
        if val >  current_price * 1.1:
            return "background-color: #d4edda !important; color: black !important"
        elif val < current_price * .9:
            return "background-color: #f8d7da !important; color: black !important"
        else:      
            return "background-color: #fff3cd !important; color: black !important"

    print(f"\n[{ticker}] Current Price: ${current_price}")
    return df.style.map(highlight_dcf).format("{:.2f}")

def DCF_Model(ticker, verbose= False, g=.1):    
    
    c_data= get_company_dcf_data(ticker, verbose= verbose)
    
    fcf_list= forecast_unlevered_FCF(c_data, g= g,verbose= verbose)
    
    WACC= get_wacc(c_data, verbose= verbose)
    
    enterprise_value= discount_FCF_WACC( fcf_list, WACC, g=g, verbose=verbose, g_longterm=.025)
    
    intrinsic_price= final_details(c_data, enterprise_value, verbose= verbose)

    sensitivity_DCF("META", verbose= verbose)

    return intrinsic_price