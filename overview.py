import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Overview",
    page_icon="📌",
    layout="wide"
)

st.write("# Overview 📌")

st.write(
    "This page provides a **high-level snapshot** of the studies included in the dashboard."
)

st.markdown("---")

# ------------------------------------------------------------
# LOAD METADATA
# ------------------------------------------------------------
meta = pd.read_csv("full_metadata (1).csv")

# Prefer full sample where available
meta["Subgroup_clean"] = (
    meta["Subgroup"]
    .fillna("Full")
    .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

meta["is_full"] = (meta["Subgroup_clean"] == "Full").astype(int)

meta_base = (
    meta.sort_values(["StudyID", "is_full"], ascending=[True, False])
        .drop_duplicates(subset="StudyID", keep="first")
        .reset_index(drop=True)
)

# ------------------------------------------------------------
# KEY NUMBERS
# ------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total studies", len(meta_base))

with col2:
    if "Year" in meta_base.columns:
        st.metric("Earliest year", int(meta_base["Year"].min()))

with col3:
    if "Year" in meta_base.columns:
        st.metric("Latest year", int(meta_base["Year"].max()))

st.markdown("---")

# ------------------------------------------------------------
# STUDIES PER YEAR
# ------------------------------------------------------------
if "Year" in meta_base.columns:
    st.write("## Number of studies per year")

    year_counts = (
        meta_base["Year"]
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
        .reset_index()
        .rename(columns={"index": "Year", "Year": "Number of studies"})
    )

    st.bar_chart(
        year_counts.set_index("Year"),
        height=300
    )

st.markdown("---")

# ------------------------------------------------------------
# REPORTING COMPLETENESS SNAPSHOT
# ------------------------------------------------------------
st.write("## Reporting completeness (snapshot)")

report_vars = [
    "Device_Brand",
    "Device_Type",
    "Sampling_Rate_Hz",
    "Sleep_Measurement_Type",
    "Cutpoint_Type"
]

rows = []

for var in report_vars:
    if var in meta_base.columns:
        reported = meta_base[var].notna().mean() * 100
        rows.append({
            "Variable": var,
            "Reported (%)": round(reported, 1)
        })

st.dataframe(pd.DataFrame(rows), width="stretch")
