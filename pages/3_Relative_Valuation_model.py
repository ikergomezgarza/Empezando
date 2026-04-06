import streamlit as st
st.title("Relative Valuation")


from Functions import company_data, get_company_area, get_index_companies, get_competition, filter_df, clean_dfs, all_values, build_table, relative_valuation, streamlit_df



ticker= st.text_input("Company to evaluate", "AAPL")
    
st.write("")       
if st.button("Run"):
    
    
    with st.spinner("Getting Company data"): 
        stock_dict= company_data(ticker)
    with st.spinner("Getting Company areas"): 
        stock_areas= get_company_area(stock_dict)
    with st.spinner("Getting Company competitors"): 
        all_dfs= get_competition(stock_areas)
    with st.spinner("Cleaning all the data"):
        all_dfs_clean= clean_dfs(all_dfs, ticker) 
    with st.spinner("Getting important Values"): 
        all_dataframes = all_values(all_dfs_clean)
    with st.spinner("Getting the expected values"): 
        streamlit_dfs= streamlit_df(all_dataframes, ticker)
    
    fmt = {
    "market cap":        "{:,.0f}",
    "net debt":          "{:,.0f}",
    "minority interest": "{:,.0f}",
    "enterprise value":  "{:,.0f}",
    "total revenue":     "{:,.0f}",
    "ebitda":            "{:,.0f}",
    "ev/revenue":        "{:.2f}x",
    "ev/ebitda":         "{:.2f}x",
}

    for name, df in streamlit_dfs.items():
        st.subheader(name)
        st.dataframe(
            df.style.format(fmt),
            use_container_width=True
        )

