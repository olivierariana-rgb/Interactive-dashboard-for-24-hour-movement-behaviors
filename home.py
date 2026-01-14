import streamlit as st

st.set_page_config(
    page_title="24-Hour Movement Composition Explorer",
    page_icon="🏠",
    layout="wide"
)

st.write("# 24-Hour Movement Composition Explorer 🧭")

st.write(
    "An interactive dashboard to explore **study-level** 24-hour movement behavior estimates "
    "(Sleep, SB, LPA, MVPA) and compare how **methodological choices** relate to differences in reported values."
)

st.sidebar.success("Select a page above.")

st.markdown("---")

# ------------------------------------------------------------
# PURPOSE
# ------------------------------------------------------------
st.write("## What this app is for")

st.write(
    "- **Explore** arithmetic vs geometric means across studies\n"
    "- **Zoom in** on one behavior and age group to inspect study-level estimates\n"
    "- **Compare methods** (cutpoints, devices, sampling rate, sleep measurement) using compact variability plots\n"
    "- **Inspect tables** showing exactly which studies contribute to each result\n"
    "- **Support transparency** in a methods-focused scoping review"
)

st.markdown("---")

# ------------------------------------------------------------
# DATA
# ------------------------------------------------------------
st.write("## Data used")

st.write(
    "This app is based on two extracted datasets:\n\n"
    "- **Long-format estimates table**: study-level time estimates by behavior and mean type\n"
    "- **Metadata table**: study characteristics and methodological decisions\n\n"
    "When multiple subgroups were reported, the **full sample** was preferred where available."
)

st.markdown("---")

# ------------------------------------------------------------
# HOW TO USE
# ------------------------------------------------------------
st.write("## How to use (quick guide)")

st.write(
    "1) Start in **Explorer (🔎)** and apply filters (age group, device brand/type, country, sampling rate).\n"
    "2) Use **Behavior-Level Scatter** to examine study-to-study variability.\n"
    "3) Use **Simplex (🔺)** to view closed geometric compositions.\n"
    "4) Use **Results Engine (🧠)** to compare variability across methodological choices.\n"
    "5) Use **Study Tables (📋)** to inspect extracted values.\n"
    "6) Use **Corrections & Feedback (🛠️)** to flag potential issues."
)

st.markdown("---")

# ------------------------------------------------------------
# INTERPRETATION NOTES
# ------------------------------------------------------------
st.write("## Important interpretation notes")

st.write(
    "- Differences across studies may reflect **methodological decisions**, not true behavioral differences.\n"
    "- Estimates are shown **as reported or derived** from the original articles.\n"
    "- “NR” indicates **not reported** in the source paper.\n"
)

st.markdown("---")

# ------------------------------------------------------------
# LINKS
# ------------------------------------------------------------
with st.expander("Links"):
    st.write("- Scoping review preprint: (add later)")
    st.write("- GitHub repository: (add later)")
    st.write("- Contact: (add later)")
