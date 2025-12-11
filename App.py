import os
import streamlit as st
import pandas as pd
import plotly.express as px

# Disable file watcher warnings on Streamlit Cloud
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

# --------------------------------------------
# Load cleaned dashboard dataset (local file)
# --------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("dashboard_clean.csv")

df = load_data()

# Ensure Age_Group has consistent ordering
df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult", "Unknown"],
    ordered=True
)

# --------------------------------------------
# Sidebar Filters
# --------------------------------------------
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
    "Sleep Measurement (Objective?)",
    options=sorted(df["Sleep_Objective_Yes_No"].dropna().unique()),
    default=None
)

country_filter = st.sidebar.multiselect(
    "Country",
    options=sorted(df["Country"].dropna().unique()),
    default=None
)

# --------------------------------------------
# Apply filters
# --------------------------------------------
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

# --------------------------------------------
# Page Title
# --------------------------------------------
st.title("24-Hour Movement Composition Explorer")
st.write("Visualize Arithmetic vs Geometric means across studies and subgroups.")

# --------------------------------------------
# Prepare arithmetic vs geometric datasets
# --------------------------------------------
arith = df_f[df_f["Mean_Type"] == "Arithmetic"]
geo = df_f[df_f["Mean_Type"] == "Geometric"]

arith_means = arith.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"].mean().reset_index()
geo_means = geo.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"].mean().reset_index()

# --------------------------------------------
# 24h Closure Check Panel
# --------------------------------------------
st.subheader("24-Hour Closure Check")

if "Data_Closure_24hr_Sum" in df_f.columns:
    invalid = df_f[df_f["Data_Closure_24hr_Sum"] != 1440]

    if len(invalid) > 0:
        st.error(f"⚠️ {len(invalid)} rows do NOT sum to 24 hours.")
        st.dataframe(invalid[["StudyID", "Subgroup", "Data_Closure_24hr_Sum"]])
    else:
        st.success("✔ All rows close properly to 24 hours.")
else:
    st.info("No closure information available in dataset.")

# --------------------------------------------
# PLOTS — Arithmetic vs Geometric Means
# --------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Arithmetic Means")
    if arith_means.empty:
        st.warning("No arithmetic data matches your filters.")
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
        st.plotly_chart(fig_a, use_container_width=True)

with col2:
    st.subheader("Geometric Means")
    if geo_means.empty:
        st.warning("No geometric data matches your filters.")
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
        st.plotly_chart(fig_g, use_container_width=True)

# --------------------------------------------
# Study-Level Breakdown
# --------------------------------------------
st.subheader("Study-Level Breakdown (Matching Current Filters)")

if df_f.empty:
    st.warning("No rows match your filters.")
else:
    st.dataframe(
        df_f.sort_values(["StudyID", "Subgroup", "Behavior"])[
            [
                "StudyID", "Age_Group", "Subgroup", "Behavior",
                "Minutes", "Mean_Type", "Device_Brand",
                "Country", "Sampling_Rate_Hz", "Sleep_Objective_Yes_No"
            ]
        ]
    )