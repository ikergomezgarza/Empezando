import streamlit as st
import pandas as pd

from Functions import get_company_dcf_data, forecast_unlevered_FCF, get_wacc, discount_FCF_WACC, final_details, sensitivity_DCF, DCF_Model, terminal_value
st.title("DCF Model")

modify_parameters= False

year=                    5
g=                      .05
equity_risk_premium=    .05
g_longterm=             .025

ticker = st.text_input("Calculate DCF of:", "AAPL")

modify_parameters= st.toggle("Modify parameters")
if modify_parameters:
    year=                  st.slider("Years to discount",             0, 15,        5,   step= 1)
    g=                     st.slider("Company growth",                0.0, 0.2,     0.05,   step= .01)
    g_longterm=            st.slider("Growth long term",              0.0, 0.2,     0.025,  step= .005)
    equity_risk_premium=   st.slider("Equity risk premium",           0.0, 0.2,     0.05,  step= .01)
    
st.write("")       
if st.button("Run"):
    with st.spinner("Pulling data from Internet..."):
        
        c_data= get_company_dcf_data(ticker, verbose=True)
    
        fcf_list= forecast_unlevered_FCF(c_data, g= g, year= year, verbose=True)
    
        WACC= get_wacc(c_data, equity_risk_premium=equity_risk_premium, verbose=True )
    
        enterprise_value= discount_FCF_WACC( fcf_list, WACC, g_longterm=.025, verbose=True)
        
        TV      = terminal_value(fcf_list[-1], WACC, g_longterm= g_longterm)
    
        intrinsic_price= final_details(c_data, enterprise_value, verbose=True)
        
        
        st.write("")
        st.subheader("Final results")
        st.write(f"Terminal Value:                {TV/1e6:,.1f}")
        st.write(f"Intrinsic price:               {intrinsic_price:.2f}$")
        st.write(f"Current price:                 {c_data["share_price"]:.2f}$")
        
        if (c_data["share_price"]- intrinsic_price) < 0:
            st.success(f"The company is under valued by {round(c_data["share_price"]- intrinsic_price,2)}$")
        else:
            st.error(f"The company is over valued by {round(c_data["share_price"]- intrinsic_price,2)}$")
        st.write("")
            
    
        
        st.subheader(f"{ticker} data")
        
        col1, col2, col3= st.columns(3)
        
        with col1:
            st.write(f"Confidence:            {c_data["confidence"]}")
            st.write(f"Market cap:            {c_data["market_cap"]/1e6:.1f}M")
            st.write(f"Shares:                {c_data["shares"]/1e6:.1f}M")
            st.write(f"Share price:           {c_data["share_price"]:.1f}")
            
        with col2:
            st.write(f"Cash:                  {c_data["cash"]/1e6:.1f}M")
            st.write(f"Interest Expense:      {c_data["interest_expense"]/1e6:.1f}M")
            st.write(f"Total debt:            {c_data["total_debt"]/1e6:.1f}M")
            st.write(f"Tax rate:              {c_data["tax_rate"]:.1%}")
       
        with col3:
            st.write(f"Ebitda:                {c_data["ebitda"]/1e6:.1f}M")
            st.write(f"Ebit:                  {c_data["operating_income"]/1e6:.1f}M")
            st.write(f"Dep % Amort:           {c_data["dep_am"]/1e6:.1f}M")
            st.write(f"NWC change:            {c_data["NWC_change"]/1e6:.1f}M")
        
        st.write("")
        fcf_df = pd.DataFrame(
            [round(f / 1e6, 1) for f in fcf_list],
            index=[f"Year {i}" for i in range(1, len(fcf_list)+1)],
            columns=["FCF (M$)"]
        ).T

        st.dataframe(fcf_df, use_container_width=True)
        
        st.write("")
        st.subheader("Parameters")
        st.write(f"Bond rate:                {c_data["bond_10yr"]:.1%}")
        st.write(f"Beta:                     {c_data["beta"]}")
        st.write(f"Equity risk premium:      {equity_risk_premium:.1%}")
        st.write(f"Cost of equity:           {(c_data["bond_10yr"]+ c_data["beta"]* equity_risk_premium):.2%}")
        st.write(f"Cost of debt:             {(c_data["interest_expense"]/c_data["total_debt"]):.2%}")
        st.write(f"Cost of debt after tax:   {((c_data["interest_expense"]/c_data["total_debt"])*(1-c_data["tax_rate"])):.2%}")
        st.write(f"Enterprise value:         {(c_data["market_cap"] + c_data["total_debt"])/1e6:,.1f}M")
        st.write(f"WACC:                     {WACC:.1%}")
        
        df = sensitivity_DCF(ticker, verbose=False)
        st.dataframe(df, use_container_width=True)