import streamlit as st

st.set_page_config(
    page_title="24-Hour Movement Composition Explorer",
    page_icon="📊",
    layout="wide",
)

home = st.Page("home.py", title="Home", icon="🏠")
explorer = st.Page("explorer.py", title="Explorer", icon="🔍")
study_tables = st.Page("study_tables.py", title="Study Tables", icon="📋")
simplex = st.Page("simplex.py", title="Simplex", icon="🔺")
results_engine = st.Page("results_engine.py", title="Results Engine", icon="🧠")

pg = st.navigation([home, explorer, study_tables, simplex, results_engine])
pg.run()

