import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# Load cleaned dataset (must be in the same repo)
# --------------------------------------------------
df = pd.read_csv("dashboard_clean.csv")

# --------------------------------------------------
# CLEAN + FIX TYPES
# --------------------------------------------------

# Force numeric conversion on all relevant columns
numeric_cols = [
    "Minutes", "Sampling_Rate_Hz", "Data_Closure_24hr_Sum",
    "Mean_Sleep_Min", "Mean_SB", "Mean_LPA", "Mean_MVPA",
    "Geo_Mean_Sleep", "Geo_Mean_SB", "Geo_Mean_LPA", "Geo_Mean_MVPA"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Ensure ordered age groups
df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult", "Unknown"],
    ordered=True
)

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
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

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------
df_f = df.copy()

if age_filter:
    df_f = df_f[df_f["Age_Group"].isin(age_filter)]

if device_filter:
    df_f = df_f[df_f["Device_Brand"].isin(device_filter)]

if sampling_filter:
    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(sampling_filter)]

if sleep_filter:
    df_f = df_f[df_f["Sleep_Objective_Yes_No"].isin(sleep_filter)]

if country_filter:
    df_f = df_f[df_f["Country"].isin(country_filter)]

# Ensure Minutes is numeric AFTER filtering
df_f["Minutes"] = pd.to_numeric(df_f["Minutes"], errors="coerce")

# --------------------------------------------------
# TITLES
# --------------------------------------------------
st.title("24-Hour Movement Composition Explorer")
st.write("Visualize Arithmetic vs Geometric means across studies and subgroups.")

# --------------------------------------------------
# SPLIT BY MEAN TYPE
# --------------------------------------------------
arith = df_f[df_f["Mean_Type"] == "Arithmetic"].copy()
geo = df_f[df_f["Mean_Type"] == "Geometric"].copy()

arith["Minutes"] = pd.to_numeric(arith["Minutes"], errors="coerce")
geo["Minutes"] = pd.to_numeric(geo["Minutes"], errors="coerce")

# --------------------------------------------------
# COMPUTE MEANS
# --------------------------------------------------
arith_means = (
    arith.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"]
    .mean().reset_index()
)

geo_means = (
    geo.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"]
    .mean().reset_index()
)

# --------------------------------------------------
# 24-HOUR CLOSURE CHECK
# --------------------------------------------------
st.subheader("24-Hour Closure Check")

if "Data_Closure_24hr_Sum" in df_f.columns:
    invalid_closure = df_f[df_f["Data_Closure_24hr_Sum"] != 1440]

    if len(invalid_closure) > 0:
        st.error(f"⚠️ {len(invalid_closure)} rows do NOT sum to 24 hours!")
        st.dataframe(
            invalid_closure[
                ["StudyID", "Subgroup", "Data_Closure_24hr_Sum"]
            ]
        )
    else:
        st.success("✔️ All studies show proper 24-hour closure.")
else:
    st.info("No closure information available in dataset.")

# --------------------------------------------------
# PLOTS — ARITHMETIC vs GEOMETRIC
# --------------------------------------------------
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
            title="Arithmetic Means (Minutes)",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult", "Unknown"]}
        )
        fig_a.update_layout(barmode="stack")
        st.plotly_chart(fig_a, use_container_width=True)

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
            title="Geometric Means (Minutes)",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult", "Unknown"]}
        )
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(fig_g, use_container_width=True)

# --------------------------------------------------
# STUDY-LEVEL BREAKDOWN TABLES (Separated)
# --------------------------------------------------
st.subheader("Study-Level Breakdown (Separated by Mean Type)")

if df_f.empty:
    st.warning("No rows match your current filters.")
else:

    # Columns to show
    cols = [
        "StudyID_display", "StudyID", "Age_Group", "Subgroup", "Behavior",
        "Minutes", "Mean_Type", "Device_Brand", "Country",
        "Sampling_Rate_Hz", "Sleep_Objective_Yes_No"
    ]
    cols = [c for c in cols if c in df_f.columns]

    # ---- Arithmetic table ----
    st.markdown("### 🔵 Arithmetic Means")
    if arith.empty:
        st.info("No arithmetic rows in this filter.")
    else:
        st.dataframe(
            arith.sort_values(["StudyID", "Subgroup", "Behavior"])[cols],
            use_container_width=True
        )

    # ---- Geometric table ----
    st.markdown("### 🟣 Geometric Means")
    if geo.empty:
        st.info("No geometric rows in this filter.")
    else:
        st.dataframe(
            geo.sort_values(["StudyID", "Subgroup", "Behavior"])[cols],
            use_container_width=True
        )
