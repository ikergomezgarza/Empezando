import streamlit as st

from Functions import ebitdas, funds_table, fcf_data, fcf_model, debt_schedule, returns, evaluate_company, compare_entries_exits, highlight_irr

modify_values= False
modify_fees= False
modify_percents= False
modify_values= False

st.title("LBO Model")
st.write("Coming soon")

c_name= st.text_input("Ticker", "AAPL")
modify_variables= st.toggle("Modify Variables")


entry_multiple =      10
exit_multiple =       9
pct_debt =            0.70
pct_senior =          0.60
transaction_fee_pct = 0.02
financing_fee_pct =   0.035
mgmt_rollover_pct =   0.10
ebitda_growth =       0.05
senior_rate =         0.07
sub_rate =            0.10
amort_pct =           0.05
sweep_pct =           0.5
years =               5

if modify_variables:
    
    modify_values= st.toggle("Modify Values")
    if modify_values:
    
        entry_multiple=       st.slider("Entry Multiple",             5, 15,        10,  step= 1)
        exit_multiple=        st.slider("Exit Multiple",              5, 15,        10,  step= 1)
        ebitda_growth=        st.slider("Ebitda growth",              0.0, 0.2,     0.05, step= .01)
        years=                st.slider("years",                      0, 10,        5, step= 1)
    
    modify_percents= st.toggle("Modify Percents")
    if modify_percents:
        
        pct_debt=             st.slider("Percent of debt",            0.0, 1.0,     0.7, step= 0.1)
        pct_senior=           st.slider("Percent of Senior Debt",     0.0, 1.0,     0.6, step= 0.1)
        st.write(f"Percent of Sub Debt {round(1- pct_senior)}")
        senior_rate=          st.slider("Senior debt rate",           0.0, .2 ,     0.07, step= 0.01)
        sub_rate=             st.slider("Sub debt rate",              0.0, 0.2,     0.1, step= 0.01)
        amort_pct=            st.slider("Amortization percent",       0.0, 0.1,     0.05, step= 0.01) 
        sweep_pct=            st.slider("Sweep percent",              0.0, 1.0,     0.5, step= 0.1)
    
    modify_fees= st.toggle("Modify Fees")
    if modify_fees:
        transaction_fee_pct=  st.slider("Transaccion Fee",            0.0, 0.05,    .02,  step= .005)
        financing_fee_pct=    st.slider("Financing fee",              0.0, 0.05,    0.035, step= .005)
        mgmt_rollover_pct=    st.slider("Managment rollover percent", 0.0, 0.2,     0.1, step= .005)
        
    #retuns variables
    #entry_multiple= 
    #exit_multiple= 


#ebitdas
ebitdas_datas= ebitdas(c_name)

#funds_table
funds_results= funds_table(ebitdas_datas, entry_multiple= entry_multiple,
                           pct_debt=pct_debt, pct_senior=pct_senior, 
                           transaction_fee_pct=transaction_fee_pct, financing_fee_pct= financing_fee_pct, 
                           mgmt_rollover_pct=mgmt_rollover_pct)

#fcf_data
fcf_datas= fcf_data(c_name)

#fcf_model
fcf_results= fcf_model(ebitdas_datas, fcf_datas, 
                       ebitda_growth= ebitda_growth, 
                       years= years)

#debt_schedule
debt_results= debt_schedule(funds_results, fcf_results,
                            senior_rate=senior_rate, sub_rate= sub_rate, 
                            amort_pct= amort_pct, sweep_pct= sweep_pct, 
                            years= years)

#returns
returns_results= returns(fcf_results, debt_results, funds_results,
                         exit_multiple= exit_multiple, years= years)

#evaluate_company
evaluate_results= evaluate_company(c_name, entry_multiple= entry_multiple )



#this for later 
#compare_entries_exits

#highlight_irr