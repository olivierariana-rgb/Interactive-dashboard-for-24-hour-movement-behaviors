import streamlit as st

st.set_page_config(
    page_title="24-Hour Movement Behaviour Dashboard",
    layout="wide"
)

st.title("24-Hour Movement Behaviour Dashboard")

st.markdown("""
This interactive dashboard accompanies a scoping review on
**24-hour movement behaviours** (sleep, sedentary behaviour,
light physical activity, and MVPA).

Use the navigation menu on the left to explore:

- **Explorer** — interactive visualizations and distributions  
- **Study Tables** — study-level summaries and metadata  
- **Simplex & Methods** — compositional and methodological comparisons  

This app is intended as a transparent research companion and
methodological exploration tool.
""")

import streamlit as st

st.set_page_config(
    page_title="24-Hour Movement Composition Explorer",
    page_icon="📊",
    layout="wide"
)

st.title("24-Hour Movement Composition Explorer")
st.write("Use the sidebar to navigate between pages.")

st.sidebar.success("Select a page above.")




