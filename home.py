import streamlit as st

st.set_page_config(
    page_title="24-Hour Movement Composition Explorer",
    page_icon="🧭",
    layout="wide"
)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.write("# 24-Hour Movement Composition Explorer 🧭")
st.write(
    "An interactive dashboard to explore **study-level** 24-hour movement behavior estimates "
    "(Sleep, SB, LPA, MVPA) and compare how **methodological choices** relate to differences in reported values."
)

st.markdown("---")

# ------------------------------------------------------------
# QUICK CONTEXT / PURPOSE
# ------------------------------------------------------------
left, right = st.columns([2, 1])

with left:
    st.write("## What this app is for")
    st.write(
        "- **Explore** arithmetic vs geometric means across studies.\n"
        "- **Zoom in** on one behavior + age group to inspect study estimates.\n"
        "- **Summarize** study characteristics and exportable tables.\n"
        "- **Compare methods** (e.g., cutpoint type, device brand/type, sampling rate) using a compact variability view.\n"
    )

    st.write("## Data")
    st.write(
        "This app uses two inputs:\n"
        "- A long-format table for plotting (study estimates by behavior and mean type)\n"
        "- A metadata table (one row per study, preferred full sample when available)\n"
    )

with right:
    st.write("## Pages")
    st.info(
        "**Explorer**: main plots + filters\n\n"
        "**Study Tables**: study-level tables (wide format)\n\n"
        "**Simplex**: ternary plot (geometric means)\n\n"
        "**Results Engine**: methods comparison + reporting completeness"
    )

st.markdown("---")

# ------------------------------------------------------------
# HOW TO USE
# ------------------------------------------------------------
st.write("## How to use (30 seconds)")
st.write(
    "1) Start in **Explorer** and select filters (age group, device brand/type, country, sampling rate, sleep measurement).\n"
    "2) Use **Behavior-Level Scatter** to zoom in and see study-to-study spread.\n"
    "3) Go to **Study Tables** to view one-row-per-study metadata and wide-format behavior tables.\n"
    "4) Use **Results Engine** to compare how methodological choices relate to variability across studies.\n"
)

st.markdown("---")

# ------------------------------------------------------------
# WHAT TO CITE / NOTES
# ------------------------------------------------------------
st.write("## Notes")
st.write(
    "- This dashboard is designed to support a **methods-focused scoping review**.\n"
    "- Values reflect what was **reported/extracted** from studies and may differ due to protocol differences.\n"
    "- “NR” indicates **not reported** in the source article.\n"
)

# Space for links later
with st.expander("Links"):
    st.write("- Scoping review preprint: (add later)")
    st.write("- GitHub repository: (add later)")
    st.write("- Contact: (add later)")
