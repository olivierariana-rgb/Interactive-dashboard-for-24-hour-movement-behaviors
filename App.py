import streamlit as st

home = st.Page("home.py", title="Home", icon="🏠")
overview = st.Page("overview.py", title="Overview", icon="📌")
explorer = st.Page("explorer.py", title="Explorer", icon="🔎")
simplex = st.Page("simplex.py", title="Simplex", icon="🔺")
results = st.Page("results_engine.py", title="Results Engine", icon="🧠")
tables = st.Page("study_tables.py", title="Study Tables", icon="📋")
feedback = st.Page("corrections.py", title="Corrections & Feedback", icon="🛠️")

pg = st.navigation([
    home,
    overview,
    explorer,
    simplex,
    results,
    tables,
    feedback
])

pg.run()



