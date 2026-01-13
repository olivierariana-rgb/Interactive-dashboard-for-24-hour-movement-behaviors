import streamlit as st

st.set_page_config(
    page_title="Explorer",
    page_icon="🔍",
)

st.markdown("# Study & Behavior Explorer")
st.sidebar.header("Explorer")

st.write(
    """
    This section allows you to explore the extracted data from the scoping review.

    Here, you can:
    - Browse included studies
    - Examine reported 24-hour movement behaviours
    - Compare arithmetic and geometric summaries
    - Understand how estimates vary across studies

    Use this page as an **entry point** to the data before moving on to
    summary tables, methodological comparisons, and compositional visualizations.
    """
)

st.markdown(
    """
    **What you’ll find on this page (coming next):**
    - Interactive filters (age group, device, country, etc.)
    - Behavior-level summaries (Sleep, SB, LPA, MVPA)
    - Study-level breakdowns

    This page is intentionally lightweight and exploratory.
    """
)
