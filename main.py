import streamlit as st

st.set_page_config(page_title="Iker Gomez Garza", layout="wide")

st.title("Iker Gomez Garza")
st.subheader("Finance Models · Python")
st.write("Second-year Economics student at Universidad de Valencia.")
st.markdown("---")
st.page_link("pages/1_LBO_model.py", label="Go to LBO Model")
st.page_link("pages/2_Accretion_Dilution_model.py", label="Go to Accretion and Dilution Model")
st.page_link("pages/3_Relative_Valuation_model.py", label="Go to Relative Valuation Model")
st.page_link("pages/4_DCF_model.py", label="Go to DCF Model")
st.page_link("pages/5_Black_Scholes.py", label="Go to Opcion chain and Greeks Model")
st.page_link("pages/6_Volatility_Surface.py", label="Go to Volatility Surface Model")

st.markdown("[← Back to Portfolio](https://ikergomezgarza.github.io)")

