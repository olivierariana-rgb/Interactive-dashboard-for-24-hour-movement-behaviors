import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

st.write("# 24-Hour Movement Composition Explorer")
st.write(
    "This app accompanies a scoping review of device-based 24-hour movement behavior studies. "
    "Use it to explore behavior estimates, compare methodological choices, and verify extracted values."
)

st.markdown("---")

# =========================
# Load metadata
# =========================
@st.cache_data
def load_meta():
    m = pd.read_csv("full_metadata (1).csv")
    if "StudyID" not in m.columns:
        raise ValueError("StudyID column not found in metadata.")
    return m

meta = load_meta()

# =========================
# Build meta_base: one row per study (prefer Full)
# =========================
meta_base = meta.copy()

meta_base["Subgroup_clean"] = (
    meta_base.get("Subgroup", pd.Series([None]*len(meta_base)))
    .fillna("Full")
    .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

meta_base["is_full"] = (meta_base["Subgroup_clean"] == "Full").astype(int)

meta_base = (
    meta_base
    .sort_values(["StudyID", "is_full"], ascending=[True, False])
    .drop_duplicates(subset="StudyID", keep="first")
    .reset_index(drop=True)
)

# =========================
# Quick stats
# =========================
c1, c2, c3, c4 = st.columns(4)

total_studies = len(meta_base)
years_available = meta_base["Year"].dropna() if "Year" in meta_base.columns else pd.Series(dtype=float)

with c1:
    st.metric("Included studies", f"{total_studies}")

with c2:
    if len(years_available) > 0:
        st.metric("Year range", f"{int(years_available.min())}–{int(years_available.max())}")
    else:
        st.metric("Year range", "NR")

with c3:
    if "Device_Brand" in meta_base.columns:
        top_brand = meta_base["Device_Brand"].fillna("NR").value_counts().index[0]
        st.metric("Most common brand", str(top_brand))
    else:
        st.metric("Most common brand", "NR")

with c4:
    if "Country" in meta_base.columns:
        n_countries = meta_base["Country"].dropna().nunique()
        st.metric("Countries", f"{n_countries}")
    else:
        st.metric("Countries", "NR")

st.markdown("---")

# ============================================================
# FIGURE 1: Studies per year
# ============================================================
st.write("## Studies per year")

if "Year" not in meta_base.columns or meta_base["Year"].dropna().empty:
    st.warning("No Year column (or all missing), so the studies-per-year plot can’t be created.")
else:
    year_counts = (
        meta_base.dropna(subset=["Year"])
        .assign(Year=lambda d: pd.to_numeric(d["Year"], errors="coerce"))
        .dropna(subset=["Year"])
        .astype({"Year": int})
        .groupby("Year", as_index=False)["StudyID"]
        .nunique()
        .rename(columns={"StudyID": "n_studies"})
        .sort_values("Year")
    )

    fig_year = px.bar(
        year_counts,
        x="Year",
        y="n_studies",
        title="Number of included studies by publication year"
    )
    fig_year.update_layout(
        xaxis_title="Year",
        yaxis_title="Number of studies",
        margin=dict(l=30, r=30, t=60, b=30)
    )
    st.plotly_chart(fig_year, width="stretch")

st.markdown("---")

# ============================================================
# Completeness score + trend over time
# ============================================================
st.write("## Reporting completeness over time")

st.caption(
    "Completeness score = % of selected metadata fields that are reported (not missing). "
    "This helps show whether reporting quality improves over time."
)

# Choose which fields define "completeness"
default_fields = [
    "Device_Brand",
    "Device_Type",
    "Sampling_Rate_Hz",
    "Sleep_Measurement_Type",
    "Cutpoint_Type",
    "Wear_Days_Instructed",
    "Valid_Hours_Per_Day",
    "Primary_Analysis_Type",
    "Bootstrap",
    "Sensitivity_Analyses"
]

available_fields = [f for f in default_fields if f in meta_base.columns]

if "Year" not in meta_base.columns or len(available_fields) == 0:
    st.warning("Missing Year column and/or completeness fields, so completeness over time can’t be created.")
else:
    # compute completeness per study
    comp = meta_base.copy()
    comp["Year"] = pd.to_numeric(comp["Year"], errors="coerce")
    comp = comp.dropna(subset=["Year"])
    comp["Year"] = comp["Year"].astype(int)

    # reported = non-missing (and not empty string)
    reported_matrix = comp[available_fields].apply(
        lambda col: (~col.isna()) & (col.astype(str).str.strip() != ""),
        axis=0
    )

    comp["Completeness_Score"] = (reported_matrix.sum(axis=1) / len(available_fields)) * 100

    # aggregate by year
    comp_year = (
        comp.groupby("Year", as_index=False)
        .agg(
            n_studies=("StudyID", "nunique"),
            mean_completeness=("Completeness_Score", "mean"),
            median_completeness=("Completeness_Score", "median")
        )
        .sort_values("Year")
    )

    colL, colR = st.columns([2, 1])

    with colL:
        fig_comp = px.line(
            comp_year,
            x="Year",
            y="median_completeness",
            title="Median completeness score by year"
        )
        fig_comp.update_layout(
            xaxis_title="Year",
            yaxis_title="Completeness score (%)",
            margin=dict(l=30, r=30, t=60, b=30)
        )
        st.plotly_chart(fig_comp, width="stretch")

    with colR:
        st.write("### Year-level table")
        st.dataframe(comp_year, width="stretch")

    st.download_button(
        "Download completeness-by-year table (CSV)",
        data=comp_year.to_csv(index=False).encode("utf-8"),
        file_name="completeness_by_year.csv",
        mime="text/csv"
    )
