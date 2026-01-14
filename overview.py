import re
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Overview", page_icon="📌", layout="wide")

st.write("# Overview 📌")
st.write(
    "High-level summary of the included studies and how coverage changes over time. "
    "This page uses the metadata file."
)

# ------------------------------------------------------------
# Load metadata
# ------------------------------------------------------------
meta = pd.read_csv("full_metadata (1).csv")

# ------------------------------------------------------------
# Helper: find a year column + clean it
# ------------------------------------------------------------
def _pick_year_col(df: pd.DataFrame):
    # Prefer exact matches first, then common alternatives
    candidates = [
        "Year",
        "Publication_Year",
        "Year_Published",
        "Pub_Year",
        "Year_Data",
        "Year_Study",
    ]
    for c in candidates:
        if c in df.columns:
            return c
    # fallback: any column containing "year"
    yearish = [c for c in df.columns if "year" in c.lower()]
    return yearish[0] if len(yearish) > 0 else None

def _extract_year(val):
    """Return a 4-digit year as int if possible, else NA."""
    if pd.isna(val):
        return pd.NA
    s = str(val)

    # Find first 4-digit year between 1900 and 2099
    m = re.search(r"(19\d{2}|20\d{2})", s)
    if not m:
        return pd.NA
    try:
        y = int(m.group(0))
        return y
    except:
        return pd.NA

# ------------------------------------------------------------
# One row per study (prefer Full subgroup if available)
# ------------------------------------------------------------
meta_base = meta.copy()

if "Subgroup" in meta_base.columns:
    meta_base["Subgroup_clean"] = (
        meta_base["Subgroup"]
        .fillna("Full")
        .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
    )
    meta_base["is_full"] = (meta_base["Subgroup_clean"] == "Full").astype(int)
else:
    meta_base["is_full"] = 1

if "StudyID" in meta_base.columns:
    meta_base = (
        meta_base
        .sort_values(["StudyID", "is_full"], ascending=[True, False])
        .drop_duplicates(subset="StudyID", keep="first")
        .reset_index(drop=True)
    )
else:
    st.error("Your metadata file is missing a `StudyID` column, so I can't compute unique studies.")
    st.stop()

# ------------------------------------------------------------
# Basic counts
# ------------------------------------------------------------
total_studies = meta_base["StudyID"].nunique()
st.write(f"### Total included studies: **{total_studies}**")

# ------------------------------------------------------------
# Year handling
# ------------------------------------------------------------
year_col = _pick_year_col(meta_base)

if year_col is None:
    st.warning(
        "I couldn't find a year column in your metadata. "
        "Add a column named `Year` (or similar) to enable the time plots."
    )
    st.stop()

meta_base["Year_clean"] = meta_base[year_col].apply(_extract_year).astype("Int64")

valid_years = meta_base["Year_clean"].dropna()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Earliest year", int(valid_years.min()) if len(valid_years) else "NR")

with col2:
    st.metric("Latest year", int(valid_years.max()) if len(valid_years) else "NR")

with col3:
    missing_years = meta_base["Year_clean"].isna().sum()
    st.metric("Year missing (NR)", int(missing_years))

st.markdown("---")

# ------------------------------------------------------------
# Studies per year
# ------------------------------------------------------------
st.write("## Studies per year")

if len(valid_years) == 0:
    st.warning("No valid 4-digit years found. Check your year column values (e.g., NR, ranges, text).")
else:
    per_year = (
        meta_base.dropna(subset=["Year_clean"])
        .groupby("Year_clean")["StudyID"]
        .nunique()
        .reset_index()
        .rename(columns={"Year_clean": "Year", "StudyID": "n_studies"})
        .sort_values("Year")
    )

    # Chart
    fig = px.bar(
        per_year,
        x="Year",
        y="n_studies",
        title="Number of included studies by year",
    )
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Number of studies",
        margin=dict(l=40, r=40, t=70, b=40),
    )
    st.plotly_chart(fig, width="stretch")

    # Table
    st.write("### Table: studies per year")
    st.dataframe(per_year, width="stretch")

# ------------------------------------------------------------
# Optional: completeness trend (if you want)
# ------------------------------------------------------------
with st.expander("Optional: completeness trend over time"):
    st.write(
        "This computes a simple completeness score per study = % of selected fields that are NOT missing."
    )

    # Change this list if you want different “core fields”
    fields = [
        "Device_Brand",
        "Device_Type",
        "Sampling_Rate_Hz",
        "Sleep_Measurement_Type",
        "Cutpoint_Type",
        "Wear_Days_Instructed",
        "Valid_Hours_Per_Day",
        "Primary_Analysis_Type",
    ]
    fields = [f for f in fields if f in meta_base.columns]

    if len(fields) == 0:
        st.warning("None of the completeness fields were found in your metadata columns.")
    else:
        comp = meta_base.dropna(subset=["Year_clean"]).copy()
        comp["completeness_pct"] = (
            comp[fields].notna().sum(axis=1) / len(fields) * 100
        ).round(1)

        comp_year = (
            comp.groupby("Year_clean")["completeness_pct"]
            .median()
            .reset_index()
            .rename(columns={"Year_clean": "Year", "completeness_pct": "Median completeness (%)"})
            .sort_values("Year")
        )

        fig2 = px.line(
            comp_year,
            x="Year",
            y="Median completeness (%)",
            title="Median reporting completeness over time",
            markers=True,
        )
        fig2.update_layout(
            xaxis_title="Year",
            yaxis_title="Median completeness (%)",
            margin=dict(l=40, r=40, t=70, b=40),
        )
        st.plotly_chart(fig2, width="stretch")
        st.dataframe(comp_year, width="stretch")
