import pandas as pd
import yfinance as yf
from edgar import *
from IPython.display import display
import os
from dotenv import load_dotenv

load_dotenv()
set_identity(os.getenv("EMAIL"))
print("All imported")


def get_companys_datas(acq, tgt, verbose=False):

    acq_dict = yf.Ticker(acq).info
    tgt_dict = yf.Ticker(tgt).info

    if verbose == False:
        pass
    else:
        print(f"{'values':<15} | {acq_dict['symbol']:<25} | {tgt_dict['symbol']:<25}")
        print("-" * 60)
        print(
            f"{'Market cap':<15} | {round(acq_dict['marketCap']):<25,} | {round(tgt_dict['marketCap']):<25,}"
        )
        print(
            f"{'Price':<15} | {acq_dict['previousClose']:<25} | {tgt_dict['previousClose']:<25}"
        )
        print(
            f"{'Shares':<15} | {acq_dict['sharesOutstanding']:<25} | {tgt_dict['sharesOutstanding']:<25}\n\n"
        )

    return acq_dict, tgt_dict


def contract_offer(
    acq_dict,
    tgt_dict,
    offer_premium=0.60,
    stock_pct=0.50,
    tax_rate=0.40,
    years=5,
    interest_rate=0.05,
    financing_fees_pct=0.035,
    transaccion_fees_pct=0.02,
    synergies_pct=0,
    amortization_years=10,
    verbose=False,
):

    # % of deal pay by cahs and with stocks
    cash_pct = 1 - stock_pct

    # Amount of money the acusition will cost
    share_price = tgt_dict["previousClose"] * (1 + offer_premium)
    offer_value = tgt_dict["sharesOutstanding"] * share_price
    acq_issued_shares = offer_value / acq_dict["previousClose"] * stock_pct

    # All expenses and writre offs
    # Transaccion fees:
    transaccion_fees = offer_value * transaccion_fees_pct
    # Financing fees:
    acq_borrowing = offer_value * cash_pct
    financing_fees = acq_borrowing * financing_fees_pct
    financing_fees_amort = financing_fees / years
    # Posible write of
    synergies = tgt_dict["totalRevenue"] * synergies_pct
    asset_write_off = (offer_value - tgt_dict["bookValue"]) * 0.15
    incremental_DA_expense = asset_write_off / amortization_years

    # Expected earnings
    acq_implide_net_inc = acq_dict["sharesOutstanding"] * acq_dict["epsCurrentYear"]
    tgt_implide_net_inc = tgt_dict["sharesOutstanding"] * tgt_dict["epsCurrentYear"]
    acq_implide_pretax_inc = acq_implide_net_inc / (1 - tax_rate)
    tgt_implide_pretax_inc = tgt_implide_net_inc / (1 - tax_rate)

    # Getting all together and in negatice (accounting reasons)
    profroma_pretax_unadj = acq_implide_pretax_inc + tgt_implide_pretax_inc
    interest_expense_deal = acq_borrowing * interest_rate * -1
    incremental_DA_expense *= -1
    transaccion_fees *= -1
    financing_fees_amort *= -1
    synergies *= 1
    # after merge
    profroma_pretax_adj = (
        profroma_pretax_unadj
        + interest_expense_deal
        + incremental_DA_expense
        + transaccion_fees
        + financing_fees_amort
        + synergies
    )
    proforma_net_income = profroma_pretax_adj * (1 - tax_rate)
    proforma_shares_outstanding = acq_dict["sharesOutstanding"] + acq_issued_shares
    proforma_eps = proforma_net_income / proforma_shares_outstanding
    accretion_dilution_per_share = proforma_eps - acq_dict["epsCurrentYear"]
    accretion_dilution_pct = (proforma_eps / acq_dict["epsCurrentYear"]) - 1

    if verbose == False:
        pass
    else:
        print("Parameters:")
        print(f"Offer premium:            | {offer_premium * 100}%")
        print(f"% of cash:                | {cash_pct * 100}%")
        print(f"% of stock:               | {stock_pct * 100}%")
        print(f"tax rate:                 | {tax_rate * 100}%")
        print(f"interest rate:            | {interest_rate * 100}%")
        print(f"% financing fees:         | {transaccion_fees_pct * 100}%")
        print(f"% transaccion fees:       | {transaccion_fees_pct * 100}%")
        print(f"% synergies:              | {synergies_pct * 100}%")
        print(f"{'-' * 60}\n")

        print("Deal:")
        print(f"Share price:              | {round(share_price):,}")
        print(f"Offer Value:              | {round(offer_value):,}")
        print(f"Money borrowed:           | {round(acq_borrowing):,}")
        print(f"Financing fees:           | {round(financing_fees):,}")
        print(f"Shares issued:            | {round(acq_issued_shares):,}\n")
        print(f"{'-' * 60}\n")

        print("Income:")
        print(f"Accuary net income:       | {round(acq_implide_net_inc):,}")
        print(f"Target net income:        | {round(tgt_implide_net_inc):,}")
        print(f"Accuary pre tax income:   | {round(acq_implide_pretax_inc):,}")
        print(f"Target pre tax income:    | {round(tgt_implide_pretax_inc):,}")
        print(f"{'-' * 60}\n")

        print("Totals")
        print(f"Proforma pretax unadj:    | {round(profroma_pretax_unadj):,}")
        print(f"Interest expenses:        | ({round(interest_expense_deal * -1):,})")
        print(f"Amort of finance fees:    | ({round(financing_fees_amort * -1):,})")
        print(f"Transaccion fees:         | ({round(transaccion_fees * -1):,})")
        print(f"D/A write off:            | ({round(incremental_DA_expense * -1):,})")
        print(f"% synergies:              | {round(synergies):,}")
        print(f"{'-' * 60}\n")

        print("After merge:")
        print(f"Proforma pretax adj:      | {round(profroma_pretax_adj):,}")
        print(f"Proforma Net:             | {round(proforma_net_income):,}")
        print(f"Proforma shares:          | {round(proforma_shares_outstanding):,}")
        print(f"Proforma eps:             | {round(proforma_eps, ndigits=2)}")
        print(f"{'-' * 60}\n")

        print("Results")
        print(f"Accretion/Dilution:       | $ {accretion_dilution_per_share:.2f}")
        print(f"%Accretion/Dilution:      | % {accretion_dilution_pct:.2f}")

    return accretion_dilution_pct


def highlight_irr_accdil(val):
    if val >= 0:
        return "background-color: #d4edda !important; color: black !important"
    elif val >= -0.05:
        return "background-color: #fff3cd !important; color: black !important"
    else:
        return "background-color: #f8d7da !important; color: black !important"


def sensitivity_accretion_dilution(acq, tgt, verbose=False, steps=1):

    rows = []
    for i in range(0, 11, steps):
        row = []
        for j in range(0, 11, steps):
            accretion_dilution_pct = round(
                contract_offer(
                    acq, tgt, offer_premium=i / 10, stock_pct=j / 10, verbose=False
                ),
                ndigits=2,
            )

            row.append(accretion_dilution_pct)

        rows.append(row)

    df = df = pd.DataFrame(
        rows,
        columns=[f"Stock {x * 10}%" for x in range(0, 11, steps)],
        index=[f"Offer premium {x * 10}%" for x in range(0, 11, steps)],
    )
    styled = df.style.format("{:.2f}%").map(highlight_irr_accdil)
    display(styled)

    return df


def accretion_dilution_model(acq, tgt):
    acq_dict, tgt_dict = get_companys_datas(acq, tgt, verbose=True)
    contract_offer(acq_dict, tgt_dict, verbose=True)
    result = sensitivity_accretion_dilution(acq_dict, tgt_dict)
    return result


if __name__ == "__main__":
    result = accretion_dilution_model("NCLH", "SONO")
    print(result.to_string())
