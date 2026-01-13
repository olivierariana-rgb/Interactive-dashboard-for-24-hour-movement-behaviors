import streamlit as st

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="24-Hour Movement Composition Explorer",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# Landing page content
# --------------------------------------------------
st.title("24-Hour Movement Composition Explorer")

st.markdown(
    """
    This interactive application accompanies a scoping review on **24-hour movement behaviors**.
    
    It allows users to:
    - Explore arithmetic vs geometric estimates across studies
    - Compare methodological choices and their impact on results
    - Visualize compositional data using simplex plots
    - Examine study-level metadata and reporting heterogeneity

    ---
    **👈 Use the sidebar to navigate between sections of the app.**
    """
)

st.sidebar.success("Select a page above to get started.")



