import streamlit as st
from utils import load_data, apply_sidebar_filters

df, meta = load_data()
df_f, _ = apply_sidebar_filters(df)

st.header("Ternary Simplex")
st.info("Paste your simplex block here (we'll rebuild wide_all inside this page).")
