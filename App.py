import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------------------
# LOAD DATASETS
# ------------------------------------------------------------
df = pd.read_csv("dashboard_clean_input.csv")     # long-format behavior table
meta = pd.read_csv("full_metadata.csv")           # full metadata for study info

# ------------------------------------------------------------
# SAFETY CLEANING
# ------------------------------------------------------------

# Make Minutes numeric
df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

# Clean Sampling Rate
df["Sampling_Rate_Hz"] = df["Sampling_Rate_Hz"].astype(str).str.strip()

# Ensure Age_Group is categorical but keep whatever categories exist
age_categories = [c for c in df["Age_Group"].dropna().unique()]
df["Age_Group"] = pd.Categorical(df["Age_Group"], categories=age_categories, ordered=True)

# ------------------------------------------------------------
# SIDEBAR FILTERS
# ------------------------------------------------------------
st.sidebar.header("Filters")

age_filter = st.sidebar.multiselect(
    "Age Group",
    options=sorted(df["Age_Group"].dropna().unique().tolist()),
    default=sorted(df["Age_Group"].dropna().unique().tolist())
)

device_filter = st.sidebar.multiselect(
    "Device Brand",
    options=sorted(df["Device_Brand"].dropna().unique()),
    default=None
)

sampling_filter = st.sidebar.multiselect(
    "Sampling Rate (Hz)",
    options=sorted(df["Sampling_Rate_Hz"].dropna().unique()),
    default=None
)

sleepmeas_filter = st.sidebar.multiselect(
    "Sleep Measurement Type",
    options=sorted(df["Sleep_Measurement_Type"].dropna().unique()),
    default=None
)

country_filter = st.sidebar.multiselect(
    "Country",
    options=sorted(df["Country"].dropna().unique()),
    default=None
)

subgroup_filter = st.sidebar.multiselect(
    "Subgroup",
    options=sorted(df["Subgroup"].dropna().unique()),
    default=None
)

# ------------------------------------------------------------
# APPLY FILTERS
# ------------------------------------------------------------
df_f = df.copy()

if age_filter:
    df_f = df_f[df_f["Age_Group"].isin(age_filter)]

if device_filter:
    df_f = df_f[df_f["Device_Brand"].isin(device_filter)]

if sampling_filter:
    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(sampling_filter)]

if sleepmeas_filter:
    df_f = df_f[df_f["Sleep_Measurement_Type"].isin(sleepmeas_filter)]

if country_filter:
    df_f = df_f[df_f["Country"].isin(country_filter)]

if subgroup_filter:
    df_f = df_f[df_f["Subgroup"].isin(subgroup_filter)]

# ------------------------------------------------------------
# TITLE + SUMMARY
# ------------------------------------------------------------
st.title("24-Hour Movement Composition Explorer")
st.write("Visualize Arithmetic vs Geometric means across studies, subgroups, and methods.")

# ------------------------------------------------------------
# SPLIT BY MEAN TYPE
# ------------------------------------------------------------
arith = df_f[df_f["Mean_Type"] == "Arithmetic"].copy()
geo   = df_f[df_f["Mean_Type"] == "Geometric"].copy()

# ------------------------------------------------------------
# COMPUTE MEANS (safe version)
# ------------------------------------------------------------
def compute_means(df_sub):
    if df_sub.empty:
        return pd.DataFrame(columns=["Age_Group", "Behavior", "Minutes"])
    df_sub["Minutes"] = pd.to_numeric(df_sub["Minutes"], errors="coerce")
    return (df_sub.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"]
            .mean().reset_index())

arith_means = compute_means(arith)
geo_means   = compute_means(geo)

# ------------------------------------------------------------
# SHOW MEAN PLOTS
# ------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Arithmetic Means")
    if arith_means.empty:
        st.warning("No arithmetic data matches filters.")
    else:
        fig_a = px.bar(
            arith_means,
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            orientation="h",
            title="Arithmetic Means (Minutes)"
        )
        fig_a.update_layout(barmode="stack")
        st.plotly_chart(fig_a, width="stretch")

with col2:
    st.subheader("Geometric Means")
    if geo_means.empty:
        st.warning("No geometric data matches filters.")
    else:
        fig_g = px.bar(
            geo_means,
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            orientation="h",
            title="Geometric Means (Minutes)"
        )
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(fig_g, width="stretch")

# ------------------------------------------------------------
# STUDY LIST (unique study-level view)
# ------------------------------------------------------------
st.subheader("Included Studies")

unique_studies = sorted(df_f["StudyID_display"].dropna().unique())
st.write(f"**Studies shown: {len(unique_studies)}**")
st.write(unique_studies)

# ------------------------------------------------------------
# STUDY-LEVEL TABLE (behavior-level, filtered)
# ------------------------------------------------------------
st.subheader("Study-Level Behavior Table")

if df_f.empty:
    st.warning("No rows match the current filters.")
else:
    st.dataframe(
        df_f.sort_values(["StudyID", "Subgroup", "Behavior"])[
            ["StudyID_display", "Age_Group", "Subgroup", "Behavior",
             "Minutes", "Mean_Type", "Device_Brand", "Country",
             "Sampling_Rate_Hz", "Sleep_Measurement_Type"]
        ],
        width="stretch"
    )

# ------------------------------------------------------------
# METADATA SECTION
# ------------------------------------------------------------
st.subheader("Study Metadata (from full_metadata.csv)")

meta_filtered = meta[meta["StudyID"].isin(unique_studies)]
st.dataframe(meta_filtered, height=300, width="stretch")

study_table = df_f.sort_values(
    ["StudyID", "Subgroup", "Behavior"]
)

st.dataframe(study_table)
