import streamlit as st

def fmt(val):
    return f"${val/1e6:,.1f}M"

from Functions import get_companys_datas, contract_offer, highlight_irr_accdil, sensitivity_accretion_dilution, accretion_dilution_model

modify_parameters= False

offer_premium=         0.60
stock_pct=             0.50 
tax_rate=              0.40
years=                 5
interest_rate=         0.05 
financing_fees_pct=    0.035
transaccion_fees_pct=  0.02 
synergies_pct=         0
amortization_years=    10
                
st.title("Accretion / Dilution")

col1, col2= st.columns(2)
with col1:
    acq= st.text_input("Acquirer Ticker", "AAPL")
with col2:
    tgt= st.text_input("Target Ticker", "NCLH")
    
st.write("")  
modify_parameters= st.toggle("Modify parameters")    
if modify_parameters:

    col1, col2= st.columns(2)
    
    with col1:
        offer_premium=           st.slider("Offer premium",             0.0, 1.0,     0.6,   step= .1)
        stock_pct=               st.slider("Issued stock percent",      0.0, 1.0,     0.5,   step= .05)
        tax_rate=                st.slider("Tax rate",                  0.0, 0.50,    0.40,  step= .01)
        interest_rate=           st.slider("Interest rate",             0.0, 0.2,      0.10,  step= .01)
        st.write                 (f"Used Cash percent            {round(1- stock_pct,2)}")
        
        
    with col2:
        financing_fees_pct=       st.slider("Financing Fees",              0.0, 0.1,     .035,   step= .005)
        transaccion_fees_pct=     st.slider("Transaccion Fees",            0.0, 0.1,     0.02,   step= .01)
        synergies_pct=            st.slider("Synergies ",                  0.0, 0.25,    0.0,      step= .01)
        amortization_years=       st.slider("Years of Amortization",       0,   20,      10,     step= 1)
        years=                    st.slider("Years to Amortize interest",  0, 10,        5,      step= 1)

st.write("")       
if st.button("Run"):
    with st.spinner("Pulling data from Yfinance..."):
        
        params = {
            "offer_premium": offer_premium,
            "stock_pct": stock_pct,
            "tax_rate": tax_rate,
            "years": years,
            "interest_rate": interest_rate,
            "financing_fees_pct": financing_fees_pct,
            "transaccion_fees_pct": transaccion_fees_pct,
            "synergies_pct": synergies_pct,
            "amortization_years": amortization_years,
        }
        
        acq_dict, tgt_dict = get_companys_datas(acq,tgt, verbose= True)
        contract_results= contract_offer(acq_dict, tgt_dict, **params)
        
        st.write("")
        st.subheader("Totals:")
        st.write("")
        col1, col2= st.columns(2)
        with col1:
            st.metric("Accretion or dilution per share", f"{contract_results['accretion_dilution_per_share']:.2f}")
        with col2:
            st.metric("Acretion or dilution in %", f"{contract_results['accretion_dilution_pct']:.2%}")
        
        if contract_results["accretion_dilution_per_share"] > 0:
            st.success("Accretion")
        else:
            st.error("Dilution")
        st.write("")
        
        
        
        col1, col2, col3= st.columns(3)
        
        st.write("")
        with col1:
            st.write("Values")
            st.write("Market cap")
            st.write("Price")
            st.write("Shares")
            st.write("Net income")
            st.write("Pre tax income")
        with col2:
            st.write(acq_dict["symbol"])
            st.write(f"{fmt(acq_dict['marketCap'])}")
            st.write(f"{acq_dict['previousClose']}")
            st.write(f"{acq_dict['sharesOutstanding']/1e6:,.1f}M")
            st.write(f"{fmt(contract_results['accuary_net_income'])}")
            st.write(f"{fmt(contract_results['accuary_pretax_income'])}")

        with col3:
            st.write(tgt_dict["symbol"])
            st.write(f"{fmt(tgt_dict['marketCap'])}")
            st.write(f"{tgt_dict['previousClose']}")
            st.write(f"{tgt_dict['sharesOutstanding']/1e6:,.1f}M")
            st.write(f"{fmt(contract_results['target_net_income'])}")
            st.write(f"{fmt(contract_results['target_pretax_income'])}")
        
        st.write("")
        
        col1, col2 = st.columns(2)
        
        with col1:
            
            st.subheader("Parameters:")
            st.write(f"Offer premium:    {offer_premium}")
            st.write(f"Percent of cash:  {1- stock_pct}")
            st.write(f"Percent of stock: {stock_pct}")
            st.write(f"Tax rate:         {tax_rate}")
            st.write(f"Interest rate:    {tax_rate}")
            st.write(f"Financing rate:   {financing_fees_pct}")
            st.write(f"Transaccion rate: {transaccion_fees_pct}")
            st.write(f"Synergies:        {synergies_pct}")
            
            st.write("")
            st.subheader("Deal:")
            st.write(f"Share price:      {contract_results["share_price"]:,.2f}")
            st.write(f"Offer Value:      {fmt(contract_results["offer_value"])}")
            st.write(f"Money borrowed:   {fmt(contract_results["money_borrowed"])}")
            st.write(f"Shares issued:    {contract_results["shares_issued"]/1e6:,.1f}M")
            
        with col2:
            
            st.subheader("Totals:")
            st.write(f"Proforma pretax unadjusted:       {fmt(contract_results["profroma_pretax_unadj"])}")
            st.write(f"Interest expenses:                {fmt(contract_results["interest_expense_deal"])}")
            st.write(f"Amortization of finances fees:    {fmt(contract_results["financing_fees_amort"])}")
            st.write(f"Transaccion fees:                 {fmt(contract_results["transaccion_fees"])}")
            st.write(f"D/A write off:                    {fmt(contract_results["incremental_DA_expense"])}")
            st.write(f"synergies:                        {fmt(contract_results["synergies"])}")
            
            for i in range(6):
                st.write("")
                
            st.subheader("After the merge:")
            st.write(f"Proforma pretax adjusted:        {fmt(contract_results["profroma_pretax_adj"])}")
            st.write(f"Proforma net income:             {fmt(contract_results["proforma_net_income"])}")
            st.write(f"Proforma Shares Outstanding:     {contract_results["proforma_shares_outstanding"]/1e6:,.1f}M")
            st.write(f"Proforma Eps:                    {contract_results["proforma_eps"]:,.2f}")
            
            
    st.write("")  
    st.write("")
    st.header("Sensitivity table")    
    df = sensitivity_accretion_dilution(
        acq_dict, tgt_dict,
        steps=1,
        tax_rate=tax_rate,
        interest_rate=interest_rate,
        financing_fees_pct=financing_fees_pct,
        transaccion_fees_pct=transaccion_fees_pct,
        synergies_pct=synergies_pct,
        amortization_years=amortization_years,
        years=years
    )
    st.dataframe(df.style.format("{:.2f}%").map(highlight_irr_accdil))
    
st.page_link("main.py", label="Back to Home")