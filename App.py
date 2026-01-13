import streamlit as st

st.set_page_config(
    page_title="24-Hour Movement Explorer",
    page_icon="📊",
    layout="wide"
)

st.title("24-Hour Movement Composition Explorer")

st.markdown(
    """
    Welcome 👋  

    This interactive application accompanies a scoping review on  
    **24-hour movement behaviour measurement and methodological choices**.

    👉 Use the **sidebar on the left** to navigate between sections:
    - Explorer
    - Study Tables
    - Simplex
    - Results Engine
    """
)

st.sidebar.success("Select a page above ⬆️")


