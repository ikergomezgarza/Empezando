import streamlit as st

from Functions import get_company_dcf_data, forecast_unlevered_FCF, get_wacc, discount_FCF_WACC, final_details, sensitivity_DCF, DCF_Model
st.title("DCF Model")

modify_parameters= False

year=                    5
g=                      .05
equity_risk_premium=    .05
g_longterm=             .025

ticker = st.text_input("Calculate DCF of:", "AAPL")

if modify_parameters:
    
    year=                  st.slider("Years to discount",             0, 15,        5,   step= 1)
    g=                     st.slider("Company growth",                0.0, 0.2,     0.05,   step= .01)
    g_longterm=            st.slider("Growth long term",              0.0, 0.2,     0.025,  step= .005)
    equity_risk_premium=   st.slider("Equity risk premium",           0.0, 0.2,     0.05,  step= .01)
    
st.write("")       
if st.button("Run"):
    with st.spinner("Pulling data from Internet..."):
        
        c_data= get_company_dcf_data(ticker, verbose=True)
    
        fcf_list= forecast_unlevered_FCF(c_data, g= g, verbose=True)
    
        WACC= get_wacc(c_data, verbose=True )
    
        enterprise_value= discount_FCF_WACC( fcf_list, WACC, g_longterm=.025, verbose=True)
    
        intrinsic_price= final_details(c_data, enterprise_value, verbose=True)
        
        st.metric("Final valuation", f"{intrinsic_price:.2f}")
        
        
