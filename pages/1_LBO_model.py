import streamlit as st

from Functions import (
    ebitdas,
    funds_table,
    fcf_data,
    fcf_model,
    debt_schedule,
    returns,
    evaluate_company,
    compare_entries_exits,
    highlight_irr,
)

modify_variables = False

entry_multiple = 10
exit_multiple = 9
pct_debt = 0.70
pct_senior = 0.60
transaction_fee_pct = 0.02
financing_fee_pct = 0.035
mgmt_rollover_pct = 0.10
ebitda_growth = 0.05
senior_rate = 0.07
sub_rate = 0.10
amort_pct = 0.05
sweep_pct = 0.5
years = 5

st.title("LBO Model")


c_name = st.text_input("Ticker", "AAPL")

st.write("")
modify_variables = st.toggle("Modify parameters")


if modify_variables:
    col1, col2, col3 = st.columns(3)

    with col1:
        entry_multiple = st.slider("Entry Multiple", 5, 15, 10, step=1)
        exit_multiple = st.slider("Exit Multiple", 5, 15, 10, step=1)
        ebitda_growth = st.slider("Ebitda growth", 0.0, 0.2, 0.05, step=0.01)
        pct_senior = st.slider("Percent of Senior Debt", 0.0, 1.0, 0.6, step=0.1)
        st.write(f"Percent of Sub Debt {round(1 - pct_senior, 2)}")

    with col2:
        pct_debt = st.slider("Percent of debt", 0.0, 1.0, 0.7, step=0.1)
        senior_rate = st.slider("Senior debt rate", 0.0, 0.2, 0.07, step=0.01)
        sub_rate = st.slider("Sub debt rate", 0.0, 0.2, 0.1, step=0.01)
        amort_pct = st.slider("Amortization percent", 0.0, 0.1, 0.05, step=0.01)
        sweep_pct = st.slider("Sweep percent", 0.0, 1.0, 0.5, step=0.1)

    with col3:
        transaction_fee_pct = st.slider("Transaccion Fee", 0.0, 0.05, 0.02, step=0.005)
        financing_fee_pct = st.slider("Financing fee", 0.0, 0.05, 0.035, step=0.005)
        mgmt_rollover_pct = st.slider(
            "Managment rollover percent", 0.0, 0.2, 0.1, step=0.005
        )
        years = st.slider("years", 1, 10, 5, step=1)

    # retuns variables
    # entry_multiple=
    # exit_multiple=


if st.button("Run"):
    with st.spinner("Pulling data from Yfinance..."):
        # ebitdas
        ebitdas_datas = ebitdas(c_name)

        # funds_table
        funds_results = funds_table(
            ebitdas_datas,
            entry_multiple=entry_multiple,
            pct_debt=pct_debt,
            pct_senior=pct_senior,
            transaction_fee_pct=transaction_fee_pct,
            financing_fee_pct=financing_fee_pct,
            mgmt_rollover_pct=mgmt_rollover_pct,
        )

        # fcf_data
        fcf_datas = fcf_data(c_name)

        # fcf_model
        fcf_results = fcf_model(
            ebitdas_datas, fcf_datas, ebitda_growth=ebitda_growth, years=years
        )

        # debt_schedule
        debt_results = debt_schedule(
            funds_results,
            fcf_results,
            senior_rate=senior_rate,
            sub_rate=sub_rate,
            amort_pct=amort_pct,
            sweep_pct=sweep_pct,
            years=years,
        )

        # returns
        returns_results = returns(
            fcf_results,
            debt_results,
            funds_results,
            exit_multiple=exit_multiple,
            years=years,
        )

        # evaluate_company
        evaluate_results = evaluate_company(c_name, entry_multiple=entry_multiple)

        st.write("")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("IRR", f"{returns_results['IRR']:.1%}")
            if returns_results["IRR"] > 0.2:
                st.success("Acceptable")
            else:
                st.error("Not acceptable")

        with col2:
            st.metric("MoM", f"{returns_results['MoM']:.2f}x")
            if returns_results["MoM"] > 2.5:
                st.success("Acceptable")
            else:
                st.error("Not acceptable")

        st.write("")
        st.header(f"{c_name} main accounting data")
        st.write("")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"Year:                         {ebitdas_datas['year']}")
            st.write(
                f"Ebitda:                       {ebitdas_datas['ebitda'] / 1e6:.1f}M"
            )
            st.write(
                f"Depreciation & Amortization:  {ebitdas_datas['dep_am'] / 1e6:.1f}M"
            )
            st.write(
                f"Operating income:             {ebitdas_datas['operating_income'] / 1e6:.1f}M"
            )
            st.write(f"CAPEX:                        {fcf_datas['CAPEX'] / 1e6:.1f}M")
            st.write(f"NWC:                          {fcf_datas['NWC'] / 1e6:.1f}M")
            st.write(
                f"NWC change:                   {fcf_datas['NWC_change'] / 1e6:.1f}M"
            )
            st.write(f"Tax rate:                     {fcf_datas['tax_rate']:.1%}")

            st.write("")
            st.subheader("Checks")
            st.write(
                f"Total Debt / EBITDA:          {funds_results['Total_Debt_/_EBITDA']}"
            )
            st.write(
                f"Senior Debt / EBITDA:         {funds_results['Senior_Debt_/_EBITDA']}"
            )
            st.write(f"Equity:                       {funds_results['Equity_%']}")

        with col2:
            st.subheader("Uses")
            st.write(f"TEV:                         {funds_results['TEV'] / 1e6:.1f}M")
            st.write(
                f"Transaccion Fees:            {funds_results['transaccion_fees'] / 1e6:.1f}M"
            )
            st.write(
                f"Financing Fees:              {funds_results['financing_fees'] / 1e6:.1f}M"
            )
            st.write(
                f"Total Uses:                  {funds_results['total_uses'] / 1e6:.1f}M"
            )

            st.write("")
            st.subheader("Sources")
            st.write(
                f"Senior debt:                 {funds_results['senior_debt'] / 1e6:.1f}M"
            )
            st.write(
                f"Sub debt:                    {funds_results['Sub/_HY_debt'] / 1e6:.1f}M"
            )
            st.write(
                f"Total debt:                  {funds_results['total_debt'] / 1e6:.1f}M"
            )
            st.write(
                f"Managment rollover:          {funds_results['managment_rollover'] / 1e6:.1f}M"
            )
            st.write(
                f"Sponsor equity:              {funds_results['sponsor_equity'] / 1e6:.1f}M"
            )
            st.write(
                f"Total Sources:               {funds_results['Total_Sources'] / 1e6:.1f}M"
            )

        # this for later
        # compare_entries_exits

        # highlight_irr

        st.header("Sensitivity table")

        params = {
            "entry_multiple": entry_multiple,
            "exit_multiple": exit_multiple,
            "pct_debt": pct_debt,
            "pct_senior": pct_senior,
            "transaction_fee_pct": transaction_fee_pct,
            "financing_fee_pct": financing_fee_pct,
            "mgmt_rollover_pct": mgmt_rollover_pct,
            "ebitda_growth": ebitda_growth,
            "senior_rate": senior_rate,
            "sub_rate": sub_rate,
            "amort_pct": amort_pct,
            "sweep_pct": sweep_pct,
            "years": years,
        }

        df = compare_entries_exits(c_name, params)
        st.dataframe(df.style.format("{:.1f}%").map(highlight_irr))

st.page_link("main.py", label="Back to Home")
