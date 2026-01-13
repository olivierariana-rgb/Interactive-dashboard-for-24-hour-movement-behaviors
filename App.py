import streamlit as st

st.set_page_config(
    page_title="24-Hour Movement Composition Explorer",
    page_icon="📊",
    layout="wide",
)

st.write("# 24-Hour Movement Composition Explorer 📊")

st.sidebar.success("Select a page above.")

st.markdown(
    """
This Streamlit app supports a scoping review on 24-hour movement behaviours.

Use the sidebar to navigate:
- **Explorer**: interactive filtering + plots (arithmetic vs geometric, scatter, tables)
- **Simplex**: ternary composition view
- **Results Engine**: methodology summaries across studies
- **Study Tables**: export-ready tables for the manuscript

**👈 Select a page from the sidebar** to get started.
"""
)



