# LBO Screening Tool

A python projects that pulls real data from the company you desire from edgar
and will give you a full LBO model with possible flags, exit and entries results


---

## Table of Contents
- [Overview](#overview)
- [Setup](#setup)
- [Project Structure](#project-structure)
- [Pipeline](#pipeline)
- [Functions](#functions)
- [Known Limitations](#known-limitations)
- [Next Steps](#next-steps)

---

## Overview

In these project is the full pipeline for analizing if a company is viable to buy, and get its valuation
these includes pulling data from last year fiscal year, get all its necesary financials, it falgs for possible mistakes
Do alll the calculations about its debt and how it will be funded the operation, with all necesary fees and interests
At the end it calculates the returs depending on the entry and exit multiple (5x-10x each)
the final result is a grid with all possible combinations getting intervals of >25, >20, <20 IRR


---

## Setup
### Dependencies
pip install edgar pandas numpy

### EDGAR Identity
set_identity("your@email.com")

### Path
import sys
sys.path.append('/path/to/Empezando')

---

## Project Structure 
(AI did this thing i wouldnt have known)
Empezando/
├── Functions.py
├── README.md
├── requirements.txt
└── projects/
    └── P4_LBO_model/
        ├── P4_LBO.ipynb
        └── README.md
---

## Pipeline
a = ebitdas(c_name)
b = fcf_data(c_name)
c = fcf_model(a, b)
d = funds_table(a, entry_multiple=j)
e = debt_schedule(d, c)
f = returns(c, e, d, exit_multiple= i)

---

## Functions

### ebitdas()
Pulls from edgar ebitda and other financial details
input: company ticker
output:operating_income, dep_am, ebitda, year, confidence

### fcf_data()
Pulls from edgar financial statements and gives the capex, NWC and tax rate
input: company ticker
output: CAPEX, NWC, NWC_change, tax_rate, year, confidence

### fcf_model()
Proyects over the next 5 years the fcf
input: ebitdas dict, fcf_data dict
output: years_list, ebitda_list, ebit_list, nopat_list, fcf_list

### funds_table()
Build the table with all the uses and debts
inputs: ebita dict
output: TEV, transaccion_fees, financing_fees, total_uses, 
        senior_debt, sub_debt, total_debt, managment_rollover, sponsor_equity, Total Sources
        Total Debt / EBITDA Senior Debt / EBITDA Equity %

### debt_schedule()
Gives you the balance of the sources of the debts over the next 5 years to evaluate
inputs: funds dict, fcf dict
outputs: senior_beginning_list, senior_ending_list, senior_interest_list, sub_ending_list,
         sub_interest_list, total_interest_list, total_debt_list,

### returns()
It gives you the possible return of the investment IRR and MoM
input: fcf dict, debt dict, funds dict
output: IRR, MoM, exit_tev, equity_value

### evaluate_company()
The full pipeline from start to finish
input: company ticker
output: ticker, year, ebitda_M, capex_M, nwc_change_M, tax_rate, TEV_M,
        sponsor_equity_M, IRR, MoM pass IRR, confidence

### compare_entries_exits()
Gives you a table with possible entries and exit multiples (5x - 10x)
input: company ticker 
output: df with the all possible IRR combinations

---

## Known Limitations
-Financial years could not be updated, gives you last it can find
-Doesnt filter between LBO eligible companies and others
-Some data is missing so is given value 0 or a market standard
-it doesnt consider yet interest payments
NWC can be disorted and its capped at 2% ebitda
Edgar might not respond well to massive pulls
Only consider data from edgar and companies with k-10 fillings

---

## Next Steps
- [ ] Add revolver to debt schedule
- [ ] Deduct interest expense in FCF build
- [ ] Add sector filter to skip banks and insurance companies
- [ ] Reduce EDGAR API calls by passing dataframes between functions
- [ ] Add market multiple pull for realistic entry assumption

All these fixes will be done in future project separete from these one to optimize


### Learning Resources
- [Wall Street Prep — Basics of an LBO Model](https://www.wallstreetprep.com/knowledge/basics-of-an-lbo-model/)

### AI Contributions
Claude (Anthropic) assisted with:
- Project structure and file organization
- Debugging and error handling logic
- Verify financial formulas outputs
- Read massive outputs for possible errors 
- Regex tag matching for EDGAR data
- DataFrame styling

All financial logic was learned and validated by the author.
Code was written by the author with AI guidance.