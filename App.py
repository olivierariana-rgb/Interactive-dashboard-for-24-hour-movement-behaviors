import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# ----------------------------------------------------
# LOAD DATA
# ----------------------------------------------------
df = pd.read_csv("dashboard_clean_input.csv")
meta = pd.read_csv("full_metadata.csv")


# ----------------------------------------------------
# BASIC CLEANING
# ----------------------------------------------------
numeric_cols = ["Minutes", "Sampling_Rate_Hz", "Data_Closure_24hr_Sum"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Replace NA Age_Group with "Unknown"
df["Age_Group"] = df["Age_Group"].fillna("Unknown")

# Order age groups consistently
df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult", "Unknown"],
    ordered=True
)


# ----------------------------------------------------
# SIDEBAR FILTERS
# ----------------------------------------------------
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
    "Sleep Measurement Type",
    options=sorted(df["Sleep_Measurement_Type"].dropna().unique()),
    default=None
)

country_filter = st.sidebar.multiselect(
    "Country",
    options=sorted(df["Country"].dropna().unique()),
    default=None
)


# ----------------------------------------------------
# APPLY FILTERS
# ----------------------------------------------------
df_f = df.copy()

if age_filter:
    df_f = df_f[df_f["Age_Group"].isin(age_filter)]

if device_filter:
    df_f = df_f[df_f["Device_Brand"].isin(device_filter)]

if sampling_filter:
    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(sampling_filter)]

if sleep_filter:
    df_f = df_f[df_f["Sleep_Measurement_Type"].isin(sleep_filter)]

if country_filter:
    df_f = df_f[df_f["Country"].isin(country_filter)]

df_f["Minutes"] = pd.to_numeric(df_f["Minutes"], errors="coerce")


# ----------------------------------------------------
# SPLIT BY MEAN TYPE
# ----------------------------------------------------
arith = df_f[df_f["Mean_Type"] == "Arithmetic"]
geo = df_f[df_f["Mean_Type"] == "Geometric"]


# ----------------------------------------------------
# FUNCTION TO COMPUTE GROUP MEANS
# ----------------------------------------------------
def compute_means(d):
    if d.empty:
        return pd.DataFrame(columns=["Age_Group", "Behavior", "Minutes"])
    return (
        d.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"]
        .mean()
        .reset_index()
    )


arith_means = compute_means(arith)
geo_means = compute_means(geo)


# ----------------------------------------------------
# TITLE
# ----------------------------------------------------
st.title("24-Hour Movement Composition Explorer")
st.write("Visualize arithmetic and geometric means, plus all study-level data points.")


# ----------------------------------------------------
# 24-HOUR CLOSURE CHECK
# ----------------------------------------------------
st.subheader("24-Hour Closure Check")
if "Data_Closure_24hr_Sum" in df_f.columns:
    invalid = df_f[df_f["Data_Closure_24hr_Sum"] != 1440]
    if len(invalid) > 0:
        st.error(f"{len(invalid)} rows do NOT close to 24 hours.")
        st.dataframe(invalid[["StudyID", "Subgroup", "Data_Closure_24hr_Sum"]])
    else:
        st.success("All rows sum to 24 hours.")
else:
    st.info("No closure information provided.")


# ----------------------------------------------------
# PLOT 1 & 2 — BAR CHARTS
# ----------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Arithmetic Means (Stacked Bar)")
    if arith_means.empty:
        st.warning("No arithmetic data matches filters.")
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
    st.subheader("Geometric Means (Stacked Bar)")
    if geo_means.empty:
        st.warning("No geometric data matches filters.")
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


# ----------------------------------------------------
# INDIVIDUAL DATA POINTS WITH MEANS (FACETED)
# ----------------------------------------------------
st.subheader(f"{selected_behavior}: Individual Data Points with Means")

# Filter to the selected behavior
df_beh = df_f[df_f["Behavior"] == selected_behavior].copy()

if df_beh.empty:
    st.warning("No data available for this behavior with the current filters.")
else:
    # Sort studies by value (Minutes)
    df_beh = df_beh.sort_values("Minutes", ascending=True)

    # Compute means separately for each age group
    means = (
        df_beh.groupby(["Age_Group", "Mean_Type"], observed=False)["Minutes"]
        .mean()
        .reset_index()
    )

    # Build scatter plot faceted by Age_Group
    fig2 = px.scatter(
        df_beh,
        x="Minutes",
        y="StudyID_display",
        color="Mean_Type",
        symbol="Mean_Type",
        facet_col="Age_Group",
        category_orders={"Age_Group": ["Children", "Adolescents", "Adult"]},
        labels={"Minutes": "Minutes", "StudyID_display": "Study"},
        title=None,
        opacity=0.9
    )

    # Add MEAN markers: diamonds
    for age in ["Children", "Adolescents", "Adult"]:
        for mean_type, color in [("Arithmetic", "black"), ("Geometric", "royalblue")]:
            mean_row = means[
                (means["Age_Group"] == age) &
                (means["Mean_Type"] == mean_type)
            ]

            if len(mean_row) == 1:
                mean_val = mean_row.iloc[0]["Minutes"]
                # Add a diamond marker
                fig2.add_scatter(
                    x=[mean_val],
                    y=[None],  # Centers in the panel
                    mode="markers",
                    marker=dict(
                        symbol="diamond",
                        size=14,
                        color=color,
                        line=dict(width=1, color="white")
                    ),
                    name=f"{mean_type} Mean",
                    legendgroup=f"{mean_type} Mean",
                    showlegend=True,
                    xref=f"x{1 if age=='Children' else 2 if age=='Adolescents' else 3}"
                )

    # Improve theme for readability
    fig2.update_layout(
        height=600,
        legend_title="Mean Type",
        margin=dict(l=40, r=40, t=40, b=40),
    )

    # Increase spacing between facet columns
    fig2.update_layout(
        annotations=[
            ann for ann in fig2.layout.annotations if "Age_Group" in ann.text
        ]
    )

    st.plotly_chart(fig2, use_container_width=True)


# ----------------------------------------------------
# STUDY-LEVEL TABLE
# ----------------------------------------------------
st.subheader("Study-Level Rows (After Filters)")

cols = [
    "StudyID", "StudyID_display", "Age_Group", "Subgroup",
    "Behavior", "Mean_Type", "Minutes",
    "Device_Type", "Device_Brand", "Country",
    "Sampling_Rate_Hz", "Sleep_Measurement_Type"
]
cols = [c for c in cols if c in df_f.columns]

st.dataframe(df_f[cols].sort_values(["StudyID", "Behavior"]))
