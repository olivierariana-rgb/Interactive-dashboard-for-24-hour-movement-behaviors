# pages/3_Simplex.py
import streamlit as st
import plotly.express as px
from utils import load_data, apply_sidebar_filters

df, meta = load_data()
df_f, _ = apply_sidebar_filters(df)

st.header("Ternary Simplex")

# ---- Paste your simplex block here ----
# Note: if it relies on wide_all, rebuild wide_all on this page (don’t depend on other pages)
