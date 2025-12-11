import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
df = pd.read_csv("dashboard_clean_input.csv")
meta = pd.read_csv("full_metadata.csv")

# Force Minutes to numeric
df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

# Ensure ordered age groups (if missing, included automatically)
desired_age_order = ["Children", "Adolescents", "Adult", "Unknown"]
existing = [x for x in desired_age_order if x in df["Age_Group"].unique()]
df["Age_Group"] = pd.Categorical(df["Age_Group"], categories=existing, ordered=True)

# --------------------------------------------------
# SIDEBAR FILTERS — fully dynamic categories
# --------------------------------------------------
st.sidebar.header("Filters")

age_filter = st.sidebar.multiselect(
    "Age Group",
    options=sorted(df["Age_Group"].dropna().unique()),
    default=sorted(df["Age_Group"].dropna().unique())
)

device_filter = st.sidebar.multiselect(
    "Device Brand",
    options=sorted(df["Device_Brand"].dropna().unique()),
    default=None
)

sampling_filter = st.sidebar.multiselect(
    "Sampling Rate (Hz)",
    options=sorted(df["Sampling_Rate_Hz"].dropna().astype(str).unique()),
    default=None
)

sleep_measure_filter = st.sidebar.multiselect(
    "Sleep Measurement Type",
    options=sorted(df["Sleep_Measurement_Type"].dropna().unique()),
    default=None
)

country_filter = st.sidebar.multiselect(
    "Country",
    options=sorted(df["Country"].dropna().unique()),
    default=None
)

behavior_filter = st.sidebar.multiselect(
    "Behavior",
    options=sorted(df["Behavior"].dropna().unique()),
    default=sorted(df["Behavior"].dropna().unique())
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
    df_f = df_f[df_f["Sampling_Rate_Hz"].astype(str).isin(sampling_filter)]

if sleep_measure_filter:
    df_f = df_f[df_f["Sleep_Measurement_Type"].isin(sleep_measure_filter)]

if country_filter:
    df_f = df_f[df_f["Country"].isin(country_filter)]

if behavior_filter:
    df_f = df_f[df_f["Behavior"].isin(behavior_filter)]

# --------------------------------------------------
# SPLIT ARITHMETIC / GEOMETRIC
# --------------------------------------------------
arith = df_f[df_f["Mean_Type"] == "Arithmetic"].copy()
geo   = df_f[df_f["Mean_Type"] == "Geometric"].copy()

# --------------------------------------------------
# COMPUTE GROUPED MEANS
# --------------------------------------------------
def compute_means(sub):
    if sub.empty:
        return pd.DataFrame(columns=["Age_Group", "Behavior", "Minutes"])
    return (
        sub.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"]
        .mean()
        .reset_index()
    )

arith_means = compute_means(arith)
geo_means   = compute_means(geo)

# --------------------------------------------------
# PAGE TITLE
# --------------------------------------------------
st.title("24-Hour Movement Composition Explorer")
st.write("Visualize arithmetic and geometric means, plus individual study values.")

# --------------------------------------------------
# PLOTS — ORIGINAL STACKED BAR CHARTS
# --------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Arithmetic Means (Stacked Bar)")
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
            category_orders={"Age_Group": existing}
        )
        fig_a.update_layout(barmode="stack")
        st.plotly_chart(fig_a, width="stretch")

with col2:
    st.subheader("Geometric Means (Stacked Bar)")
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
            category_orders={"Age_Group": existing}
        )
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(fig_g, width="stretch")

# --------------------------------------------------
# NEW VISUAL — DOT PLOT + MEAN LINE (per Behavior)
# --------------------------------------------------
st.subheader("Individual Study Values + Mean Line")

if df_f.empty:
    st.warning("No data for dot plots.")
else:
    # Merge arithmetic + geometric together for easier plotting
    plot_df = df_f.copy()

    # Map shape
    shape_map = {"Arithmetic": "circle", "Geometric": "triangle-up"}

    fig_dot = px.scatter(
        plot_df,
        x="Minutes",
        y="Age_Group",
        color="Behavior",
        symbol="Mean_Type",
        symbol_map=shape_map,
        title="Study-level values with arithmetic & geometric means",
        facet_col="Behavior",
        category_orders={"Age_Group": existing},
        height=500,
        opacity=0.7
    )

    # ADD MEAN LINES PER BEHAVIOR
    for behavior in plot_df["Behavior"].unique():
        subA = arith_means[arith_means["Behavior"] == behavior]
        subG = geo_means[geo_means["Behavior"] == behavior]

        if not subA.empty:
            fig_dot.add_shape(
                type="line",
                x0=subA["Minutes"].mean(),
                x1=subA["Minutes"].mean(),
                y0=0, y1=1,
                xref=f"x{1 + list(plot_df['Behavior'].unique()).index(behavior)}",
                yref=f"y{1 + list(plot_df['Behavior'].unique()).index(behavior)} domain",
                line=dict(color="blue", width=2)
            )
        if not subG.empty:
            fig_dot.add_shape(
                type="line",
                x0=subG["Minutes"].mean(),
                x1=subG["Minutes"].mean(),
                y0=0, y1=1,
                xref=f"x{1 + list(plot_df['Behavior'].unique()).index(behavior)}",
                yref=f"y{1 + list(plot_df['Behavior'].unique()).index(behavior)} domain",
                line=dict(color="red", width=2, dash="dot")
            )

    st.plotly_chart(fig_dot, width="stretch")

# --------------------------------------------------
# STUDY-LEVEL TABLE (unchanged)
# --------------------------------------------------
st.subheader("Study-Level Breakdown for Current Filters")

if df_f.empty:
    st.warning("No rows match your current filters.")
else:
    cols = [
        "StudyID_display", "Year", "Age_Group", "Subgroup", "Behavior",
        "Minutes", "Mean_Type", "Device_Brand", "Country",
        "Sampling_Rate_Hz", "Sleep_Measurement_Type"
    ]
    existing_cols = [c for c in cols if c in df_f.columns]

    st.dataframe(
        df_f.sort_values(["StudyID", "Subgroup", "Behavior"])[existing_cols],
        width="stretch"
    )

study_table = df_f.sort_values(
    ["StudyID", "Subgroup", "Behavior"]
)

st.dataframe(study_table)
