import streamlit as st

st.set_page_config(
    page_title="24-Hour Movement Methods Explorer",
    page_icon="📊",
)

st.write("# 24-Hour Movement Methods Explorer")

st.sidebar.success("Select a section above.")

st.markdown(
    """
    This interactive application accompanies a scoping review on  
    **24-hour movement behaviours (sleep, sedentary behaviour, LPA, MVPA)**  
    and the **methodological choices** used to derive time-use estimates from wearable data.

    **👈 Use the sidebar** to navigate between sections of the app, including:
    - An interactive explorer of extracted study characteristics  
    - Summary tables of included studies  
    - Visual comparisons of methodological choices  
    - Results illustrating variability across analytic decisions  

    ### What is the goal of this app?
    To transparently show how different **measurement and processing decisions**
    (e.g., cutpoints, devices, sampling rates, summaries) can lead to
    **meaningful variation in reported 24-hour movement behaviour estimates**.

    ### How to use it
    - Navigate through pages using the sidebar  
    - Hover over figures to see detailed values  
    - Use filters where available to focus on specific behaviours or subgroups  

    This app is designed as a **companion tool** for researchers, reviewers,
    and students interested in reproducibility and methodological rigor in
    movement behaviour research.
    """
)


