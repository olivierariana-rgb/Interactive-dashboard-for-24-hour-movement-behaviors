import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------------------------------
# LOAD DATA
# ----------------------------------------------------
df = pd.read_csv("dashboard_clean_input.csv")        # Behavior-level tidy dataset
meta = pd.read_csv("full_metadata.csv")        # Study-level metadata   <<< FIXED

# ----------------------------------------------------
# CLEAN BASIC TYPES
# ----------------------------------------------------
numeric_cols = [
    "Minutes", "Sampling_Rate_Hz", "Data_Closure_24hr_Sum",
    "Mean_Sleep_Min", "Mean_SB", "Mean_LPA", "Mean_MVPA",
    "Geo_Mean_Sleep", "Geo_Mean_SB", "Geo_Mean_LPA", "Geo_Mean_MVPA"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Age categories
df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult", "Unknown"],
    ordered=True
)

# ----------------------------------------------------
# AUTOMATIC FILTER OPTIONS FROM METADATA FILE
# ----------------------------------------------------
st.sidebar.header("Filters")

age_filter = st.sidebar.multiselect(
    "Age Group",
    options=sorted(meta["Age_Group"].dropna().unique()),
    default=sorted(meta["Age_Group"].dropna().unique())
)

device_filter = st.sidebar.multiselect(
    "Device Brand",
    options=sorted(meta["Device_Brand"].dropna().unique()),
    default=None
)

sampling_filter = st.sidebar.multiselect(
    "Sampling Rate (Hz)",
    options=sorted(meta["Sampling_Rate_Hz"].astype(str).dropna().unique()),
    default=None
)

sleep_method_filter = st.sidebar.multiselect(
    "Sleep Measurement Type",
    options=sorted(meta["Sleep_Measurement_Type"].dropna().unique()),
    default=None
)

country_filter = st.sidebar.multiselect(
    "Country",
    options=sorted(meta["Country"].dropna().unique()),
    default=None
)

# ----------------------------------------------------
# APPLY FILTERS TO METADATA
# ----------------------------------------------------
meta_f = meta.copy()

if age_filter:
    meta_f = meta_f[meta_f["Age_Group"].isin(age_filter)]

if device_filter:
    meta_f = meta_f[meta_f["Device_Brand"].isin(device_filter)]

if sampling_filter:
    meta_f = meta_f[meta_f["Sampling_Rate_Hz"].astype(str).isin(sampling_filter)]

if sleep_method_filter:
    meta_f = meta_f[meta_f["Sleep_Measurement_Type"].isin(sleep_method_filter)]

if country_filter:
    meta_f = meta_f[meta_f["Country"].isin(country_filter)]

# ----------------------------------------------------
# JOIN METADATA FILTER RESULTS WITH BEHAVIOR DATA
# ----------------------------------------------------
df_f = df.merge(
    meta_f[[
        "StudyID", "Subgroup", "Age_Group", "Device_Brand", "Country",
        "Sampling_Rate_Hz", "Sleep_Measurement_Type"
    ]],
    on=["StudyID", "Subgroup"],
    how="inner"
)

# Ensure Minutes numeric
df_f["Minutes"] = pd.to_numeric(df_f["Minutes"], errors="coerce")

# ----------------------------------------------------
# TITLE
# ----------------------------------------------------
st.title("24-Hour Movement Composition Explorer")
st.write("Explore relationships between preprocessing decisions and 24-hour behavior estimates.")

# ----------------------------------------------------
# SPLIT ARITHMETIC VS GEOMETRIC
# ----------------------------------------------------
arith = df_f[df_f["Mean_Type"] == "Arithmetic"].copy()
geo   = df_f[df_f["Mean_Type"] == "Geometric"].copy()

# ----------------------------------------------------
# GROUPED MEANS
# ----------------------------------------------------
def compute_means(df_in):
    if df_in.empty:
        return pd.DataFrame(columns=["Age_Group", "Behavior", "Minutes"])
    return (
        df_in.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"]
        .mean().reset_index()
    )

arith_means = compute_means(arith)
geo_means   = compute_means(geo)

# ----------------------------------------------------
# 24-HOUR CLOSURE CHECK
# ----------------------------------------------------
st.subheader("24-Hour Closure Check")
if "Data_Closure_24hr_Sum" in meta_f.columns:
    bad = meta_f[meta_f["Data_Closure_24hr_Sum"] != 1440]
    if len(bad) > 0:
        st.error(f"⚠️ {len(bad)} studies have non-24h closure.")
        st.dataframe(bad[["StudyID", "Subgroup", "Data_Closure_24hr_Sum"]])
    else:
        st.success("✔ All included studies have valid 24h closure.")
else:
    st.info("No closure information available.")

# ----------------------------------------------------
# PLOTS
# ----------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Arithmetic Means")
    if arith_means.empty:
        st.warning("No arithmetic data.")
    else:
        fig_a = px.bar(
            arith_means,
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            orientation="h",
            title="Arithmetic Means",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult", "Unknown"]}
        )
        fig_a.update_layout(barmode="stack")
        st.plotly_chart(fig_a, width="stretch")

with col2:
    st.subheader("Geometric Means")
    if geo_means.empty:
        st.warning("No geometric data.")
    else:
        fig_g = px.bar(
            geo_means,
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            orientation="h",
            title="Geometric Means",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult", "Unknown"]}
        )
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(fig_g, width="stretch")

# ----------------------------------------------------
# STUDY-LEVEL TABLE (FULL METADATA + BEHAVIOR VALUES)
# ----------------------------------------------------
st.subheader("Study-Level Details")

study_table = df_f.sort_values(
    ["StudyID", "Subgroup", "Behavior"]
)

st.dataframe(study_table)
