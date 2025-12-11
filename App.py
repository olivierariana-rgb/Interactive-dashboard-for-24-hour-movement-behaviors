import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------
# Load cleaned dashboard dataset
# --------------------------------------------
df = pd.read_csv("dashboard_clean.csv")

# Force Minutes to be numeric
df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

# Ensure Age_Group order
df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult", "Unknown"],
    ordered=True
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

# --------------------------------------------
# Apply filters to df
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
# Section title
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
# 24h closure check panel
# --------------------------------------------
st.subheader("24-Hour Closure Check")

if "Data_Closure_24hr_Sum" in df_f.columns:
    invalid_closure = df_f[df_f.get("Data_Closure_24hr_Sum", 1440) != 1440]

    if len(invalid_closure) > 0:
        st.error(f"⚠️ {len(invalid_closure)} rows do NOT sum to 24 hours!")
        st.write("These are the studies / subgroups with closure errors:")
        st.dataframe(invalid_closure[["StudyID", "Subgroup", "Data_Closure_24hr_Sum"]])
    else:
        st.success("✔️ All studies show proper 24-hour closure.")
else:
    st.info("No closure information available in dataset.")

# --------------------------------------------
# Plot section
# --------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Arithmetic Means")
    if arith_means.empty:
        st.warning("No arithmetic data matches filters.")
    else:
        fig_arith = px.bar(
            arith_means,
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            orientation="h",
            title="Arithmetic Means (Minutes)",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult", "Unknown"]}
        )
        fig_arith.update_layout(barmode="stack")
        st.plotly_chart(fig_arith, use_container_width=True)

with col2:
    st.subheader("Geometric Means")
    if geo_means.empty:
        st.warning("No geometric data matches filters.")
    else:
        fig_geo = px.bar(
            geo_means,
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            orientation="h",
            title="Geometric Means (Minutes)",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult", "Unknown"]}
        )
        fig_geo.update_layout(barmode="stack")
        st.plotly_chart(fig_geo, use_container_width=True)

# --------------------------------------------------
# STUDY-LEVEL BREAKDOWN (PIVOTED / CLEAN)
# --------------------------------------------------
st.subheader("Study-Level Breakdown for Current Filters")

if df_f.empty:
    st.warning("No rows match your current filters.")
else:

    # Pivot one row per Study × Subgroup
    pivot = df_f.pivot_table(
        index=["StudyID_display", "Age_Group", "Subgroup"],
        columns=["Mean_Type", "Behavior"],
        values="Minutes",
        aggfunc="mean",
        observed=False
    )

    # Flatten column names: Arithmetic_Sleep → A_Sleep (optional)
    pivot.columns = [f"{mean}_{beh}" for mean, beh in pivot.columns]

    pivot = pivot.reset_index()

    st.dataframe(pivot, use_container_width=True)

    existing_cols = [c for c in cols if c in df_f.columns]

    st.dataframe(
        df_f.sort_values(["StudyID", "Subgroup", "Behavior"])[existing_cols]
    )
