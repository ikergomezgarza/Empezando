# Aprendi a calcular el valor de una empresa segun su cashflow
# Diferenciar entre el cashflow operativo y neto
# Al final no use la libreria edgar pero jugue mucho con ella y apremdi muchas funciones qu etenia, sacar el cashflow estaba dificil pero la usare para sacar mas datos de empresas ya ue tiene todas las formas
# diferencias los tipos de informes que hay en USA

# update
# added so you can search the value of the company by just puting the name so you dont search the cashflow and its automatica
# pricing_dfc("AAPL", .12, 5) wich you put the (name, the yearly expected growth, and the number of years)

from edgar import *
import pandas as pd
from edgar import Company
import os
from dotenv import load_dotenv

load_dotenv()
set_identity(os.getenv("EMAIL"))
print("All imported")

apple = Company("AAPL")
apple_financials = apple.get_financials()
print(f"Company: {apple.name}")
print(f"Revenue: ${apple_financials.get_revenue():,.0f}")
print(f"Net Income: ${apple_financials.get_net_income():,.0f}")

c = Company("AAPL")  # ticker
fin = c.get_financials()  # pulls latest 10-K/10-Q financials from XBRL
cf = fin.cash_flow_statement()  # cash flow statement (DataFrame-like)
df = cf.to_dataframe()
row = df.iloc[15]
row[3]


def get_cashdata(c_name):
    c = Company(c_name)  # ticker
    fin = c.get_financials()  # pulls latest 10-K/10-Q financials from XBRL
    cf = fin.cash_flow_statement()  # cash flow statement (DataFrame-like)
    df = cf.to_dataframe()
    row = df.iloc[15]
    a = row.iloc[3]
    return a


def pricing_dfc(c_name, r, n):

    CF = get_cashdata(c_name)
    DCF = CF

    for i in range(n):
        DCF += CF / (1 + r) ** i
        print(DCF)

    return f"future value is {DCF / 1000000000:.1f} Billions"


pricing_dfc("AAPL", 0.12, 5)
