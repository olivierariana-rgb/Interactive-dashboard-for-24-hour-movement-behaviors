# pages/4_Results_Engine.py
import streamlit as st
import pandas as pd
from utils import load_data, apply_sidebar_filters

df, meta = load_data()
_ = apply_sidebar_filters(df)  # filters appear, but we won’t use them for Results Engine

st.header("Results Engine — Study Methodology Overview")
st.caption("Metadata-only summaries. Not affected by the filters above.")

# ---- Paste your meta_base block here ----
# ---- Paste most common methodological choices block here ----
# ---- Paste reporting completeness + heterogeneity here ----
# ---- Paste method comparison grid here ----
