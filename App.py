import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
df = pd.read_csv("dashboard_clean.csv")
meta = pd.read_csv("dashboard_meta.csv")

# ------------------------------------------------------------
# FIX STRING COLUMNS → NUMERIC
# Streamlit Cloud is strict, so this prevents all groupby crashes
# ------------------------------------------------------------
numeric_cols = [
    "Minutes",
    "Mean_Sleep_Min", "Mean_SB", "Mean_LPA", "Mean_MVPA",
    "Geo_Mean_Sleep", "Geo_Mean_SB", "Geo_Mean_LPA", "Geo_Mean_MVPA"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ------------------------------------------------------------
# Ensure Age_Group order
# ------------------------------------------------------------
df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult", "Unknown"],
    ordered=True
)

# ------------------------------------------------------------
# SIDEBAR FILTERS
# ------------------------------------------------------------
st.sidebar.header("Filters")

age_filter = st.sidebar.multiselect(
    "Age Group",
    options=df["Age_Group"].unique().tolist(),
    default=df["Age_Group"].unique().tolist()
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

sleep_filter = st.sidebar.multiselect(
    "Sleep Measurement",
    options=sorted(df["Sleep_Objective_Yes_No"].dropna().unique()),
    default=None
)

country_filter = st.sidebar.multiselect(
    "Country",
    options=sorted(df["Country"].dropna().unique()),
    default=None
)

# ------------------------------------------------------------
# APPLY FILTERS
# ------------------------------------------------------------
df_f = df.copy()

if len(age_filter) > 0:
    df_f = df_f[df_f["Age_Group"].isin(age_filter)]

if device_filter:
    df_f = df_f[df_f["Device_Brand"].isin(device_filter)]

if sampling_filter:
    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(sampling_filter)]

if sleep_filter:
    df_f = df_f[df_f["Sleep_Objective_Yes_No"].isin(sleep_filter)]

if country_filter:
    df_f = df_f[df_f["Country"].isin(country_filter)]

# ------------------------------------------------------------
# PAGE TITLE
# ------------------------------------------------------------
st.title("24-Hour Movement Composition Explorer")
st.write("Visualize arithmetic and geometric means across studies and subgroups.")

# ------------------------------------------------------------
# SPLIT DATA: arithmetic vs geometric
# ------------------------------------------------------------
arith = df_f[df_f["Mean_Type"] == "Arithmetic"]
geo = df_f[df_f["Mean_Type"] == "Geometric"]

# ------------------------------------------------------------
# Compute grouped means safely
# ------------------------------------------------------------
def compute_means(df_subset):
    if len(df_subset) == 0:
        return pd.DataFrame(columns=["Age_Group", "Behavior", "Minutes"])
    return (
        df_subset.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"]
        .mean()
        .reset_index()
    )

arith_means = compute_means(arith)
geo_means = compute_means(geo)

# ------------------------------------------------------------
# 24-HOUR CLOSURE CHECK
# ------------------------------------------------------------
st.subheader("24-Hour Closure Check")

if "Data_Closure_24hr_Sum" in df_f.columns:
    df_f["Data_Closure_24hr_Sum"] = pd.to_numeric(df_f["Data_Closure_24hr_Sum"], errors="coerce")

    invalid = df_f[df_f["Data_Closure_24hr_Sum"] != 1440]

    if len(invalid) > 0:
        st.error(f"⚠️ {len(invalid)} rows do NOT sum to 24h.")
        st.dataframe(invalid[["StudyID", "Subgroup", "Data_Closure_24hr_Sum"]])
    else:
        st.success("✔ All rows sum to 24 hours.")
else:
    st.info("No closure information found in the dataset.")

# ------------------------------------------------------------
# PLOTS — SIDE BY SIDE
# ------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Arithmetic Means")
    if arith_means.empty:
        st.warning("No arithmetic mean data available for your filters.")
    else:
        fig_arith = px.bar(
            arith_means,
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            title="Arithmetic Means",
            orientation="h",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult", "Unknown"]}
        )
        fig_arith.update_layout(barmode="stack")
        st.plotly_chart(fig_arith, use_container_width=True)

with col2:
    st.subheader("Geometric Means")
    if geo_means.empty:
        st.warning("No geometric mean data available for your filters.")
    else:
        fig_geo = px.bar(
            geo_means,
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            title="Geometric Means",
            orientation="h",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult", "Unknown"]}
        )
        fig_geo.update_layout(barmode="stack")
        st.plotly_chart(fig_geo, use_container_width=True)

# ------------------------------------------------------------
# STUDY-LEVEL DATA MERGED WITH METADATA
# ------------------------------------------------------------
st.subheader("Study-Level Breakdown")

if df_f.empty:
    st.warning("No data matches your filters.")
else:
    merged = df_f.merge(meta, on="StudyID", how="left")

    merged = merged[
        [
            "StudyID", "StudyID_display", "Subgroup", "Mean_Type",
            "Age_Group", "Behavior", "Minutes",
            "Country", "Device_Brand", "Sampling_Rate_Hz", "Sleep_Objective_Yes_No"
        ]
    ].sort_values(["StudyID", "Subgroup", "Behavior"])

    st.dataframe(merged, use_container_width=True)
