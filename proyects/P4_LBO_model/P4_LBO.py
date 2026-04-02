import sys
import pandas as pd
from edgar import *
import os
from dotenv import load_dotenv
from IPython.display import display
load_dotenv()
set_identity(os.getenv("EMAIL"))
print("All imported")

#from Functions import *
sys.path.append('/Users/ikergg/Documents/Python learning/Proyectos/Empezando')

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
  
def highlight_irr(val):
    if val >= 25:
        return "background-color: #d4edda !important; color: black !important"
    elif val >= 20:
        return "background-color: #fff3cd !important; color: black !important"
    else:
        return "background-color: #f8d7da !important; color: black !important"  
    
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
    
    
    return df.style.format("{:.1f}%").map(highlight_irr)

if __name__ == "__main__":
    
    result= compare_entries_exits("MANH", verbose= False)
    print(result.data.to_string())