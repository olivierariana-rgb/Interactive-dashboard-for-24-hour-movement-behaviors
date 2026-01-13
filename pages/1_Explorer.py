import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Explorer", page_icon="🔎", layout="wide")

st.markdown("# Explorer 🔎")
st.sidebar.header("Explorer")
st.write(
    """
This page lets you filter studies and explore 24-hour movement estimates
(arithmetic vs geometric means), behavior-level scatter plots, and study tables.
"""
)

# ======================================================================
# LOAD DATA
# ======================================================================

df = pd.read_csv("dashboard_clean_input (1).csv")
meta = pd.read_csv("full_metadata (1).csv")

df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

# Keep only valid age groups
df = df[df["Age_Group"].isin(["Children", "Adolescents", "Adult"])]

df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult"],
    ordered=True
)

# ======================================================================
# SIDEBAR FILTERS
# ======================================================================

st.sidebar.subheader("Filters")

def auto_multiselect(label, column):
    options = sorted(df[column].dropna().unique())
    return st.sidebar.multiselect(label, options=options, default=options)

age_filter     = auto_multiselect("Age Group", "Age_Group")
brand_filter   = auto_multiselect("Device Brand", "Device_Brand")
type_filter    = auto_multiselect("Device Type", "Device_Type")
country_filter = auto_multiselect("Country", "Country")
rate_filter    = auto_multiselect("Sampling Rate (Hz)", "Sampling_Rate_Hz")
sleep_filter   = auto_multiselect("Sleep Measurement Type", "Sleep_Measurement_Type")

# ----------------------------------------------------------------------
# Subgroup mode (same as your current app)
# ----------------------------------------------------------------------

df["Subgroup_clean"] = (
    df["Subgroup"]
    .fillna("Full")
    .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

subgroups_available = sorted([s for s in df["Subgroup_clean"].unique() if s != "Full"])

st.sidebar.markdown("### Subgroup Selection")

subgroup_mode = st.sidebar.radio(
    "Choose subgroup filtering mode:",
    ["Full sample only", "All subgroups", "Specific subgroups"]
)

df_f = df.copy()

# Apply basic filters
if age_filter:     df_f = df_f[df_f["Age_Group"].isin(age_filter)]
if brand_filter:   df_f = df_f[df_f["Device_Brand"].isin(brand_filter)]
if type_filter:    df_f = df_f[df_f["Device_Type"].isin(type_filter)]
if country_filter: df_f = df_f[df_f["Country"].isin(country_filter)]
if rate_filter:    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(rate_filter)]
if sleep_filter:   df_f = df_f[df_f["Sleep_Measurement_Type"].isin(sleep_filter)]

df_f["Subgroup_clean"] = (
    df_f["Subgroup"]
    .fillna("Full")
    .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

if subgroup_mode == "Full sample only":
    df_f = df_f[df_f["Subgroup_clean"] == "Full"]

elif subgroup_mode == "Specific subgroups":
    chosen_groups = st.sidebar.multiselect(
        "Choose one or more subgroups:",
        options=subgroups_available
    )
    if len(chosen_groups) > 0:
        df_f = df_f[df_f["Subgroup_clean"].isin(chosen_groups)]
    else:
        st.sidebar.warning("Select at least one subgroup or switch mode.")

# ======================================================================
# PAGE CONTENT (you can paste your plots below)
# ======================================================================

st.markdown("### Current Selection Summary")
st.write(f"📊 **Number of studies meeting these criteria:** {df_f['StudyID'].nunique()}")

st.markdown("---")

st.subheader("Arithmetic vs Geometric Means (by Age Group)")

arith = df_f[df_f["Mean_Type"] == "Arithmetic"]
geo   = df_f[df_f["Mean_Type"] == "Geometric"]

arith_means = arith.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"].mean().reset_index()
geo_means   = geo.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"].mean().reset_index()

col1, col2 = st.columns(2)

with col1:
    st.write("**Arithmetic Means**")
    if not arith_means.empty:
        fig_a = px.bar(
            arith_means,
            x="Minutes", y="Age_Group",
            color="Behavior",
            orientation="h",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult"]}
        )
        fig_a.update_layout(barmode="stack")
        st.plotly_chart(fig_a, width="stretch")
    else:
        st.info("No arithmetic data available after filtering.")

with col2:
    st.write("**Geometric Means**")
    if not geo_means.empty:
        fig_g = px.bar(
            geo_means,
            x="Minutes", y="Age_Group",
            color="Behavior",
            orientation="h",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult"]}
        )
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(fig_g, width="stretch")
    else:
        st.info("No geometric data available after filtering.")
