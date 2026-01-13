import streamlit as st
import pandas as pd
import plotly.express as px

from utils import load_data, apply_filters, summarize_filter

# =========================
# Setup
# =========================
st.set_page_config(page_title="Explorer", layout="wide")

df, meta = load_data()
df_f, sel = apply_filters(df)

st.title("24-Hour Movement Composition Explorer")
st.write("Compare arithmetic and geometric means across studies and visualize individual data points.")

# =========================
# Filter summary
# =========================
st.markdown("### Current Selection Summary")

n_studies = df_f["StudyID"].nunique()
st.write(f"📊 **Number of studies meeting these criteria:** {n_studies}")

filter_summaries = [
    summarize_filter("Age group", sel["age_filter"], df["Age_Group"].unique()),
    summarize_filter("Device brand", sel["brand_filter"], df["Device_Brand"].unique()),
    summarize_filter("Device type", sel["type_filter"], df["Device_Type"].unique()),
    summarize_filter("Country", sel["country_filter"], df["Country"].unique()),
    summarize_filter("Sampling rate", sel["rate_filter"], df["Sampling_Rate_Hz"].unique()),
    summarize_filter("Sleep measurement", sel["sleep_filter"], df["Sleep_Measurement_Type"].unique()),
    f"Subgroup mode: {sel['subgroup_mode']}"
]

st.write("**Filters applied:**  \n" + " • " + "  \n • ".join(filter_summaries))
st.markdown("---")

# =========================
# Stacked bars: arithmetic vs geometric
# =========================
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
            category_orders={"Age_Group": ["Children","Adolescents","Adult"]}
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
            category_orders={"Age_Group": ["Children","Adolescents","Adult"]}
        )
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(fig_g, width="stretch")
    else:
        st.info("No geometric data available after filtering.")

st.markdown("---")

# =========================
# Zoomed scatter: behavior + age group (local controls)
# =========================
st.subheader("Behavior-Level Scatter Plot")
st.caption(
    "This view provides a focused look within the currently selected studies. "
    "Changing the behavior or age group here does not affect the global filters above."
)

selected_behavior = st.selectbox(
    "Zoom in on behavior:",
    sorted(df_f["Behavior"].dropna().unique())
)

selected_age = st.radio(
    "Zoom in on age group:",
    ["Children", "Adolescents", "Adult"],
    horizontal=True
)

df_beh = df_f[
    (df_f["Behavior"] == selected_behavior) &
    (df_f["Age_Group"] == selected_age)
].copy()

df_beh["Minutes"] = pd.to_numeric(
    df_beh["Minutes"].astype(str).str.replace(",", "", regex=False),
    errors="coerce"
)

df_beh = df_beh.dropna(subset=["Minutes", "StudyID_display", "Mean_Type"])

if df_beh.empty:
    st.warning("No data available for this selection.")
else:
    # Try to sort by year if it's present in df_beh, otherwise use StudyID_display
    if "Year" in df_beh.columns:
        df_beh = df_beh.sort_values(["Year", "StudyID_display"])
    else:
        df_beh = df_beh.sort_values("StudyID_display")

    summary = (
        df_beh.groupby("Mean_Type")["Minutes"]
        .median()
        .reset_index()
        .rename(columns={"Minutes": "Median"})
    )

    fig = px.scatter(
        df_beh,
        x="Minutes",
        y="StudyID_display",
        color="Mean_Type",
        symbol="Mean_Type",
        symbol_map={"Arithmetic": "circle", "Geometric": "triangle-up"},
        title=f"{selected_behavior} — {selected_age}",
        height=700
    )

    # Median reference lines (only for what exists)
    for _, row in summary.iterrows():
        mean_type = row["Mean_Type"]
        median_val = row["Median"]
        if pd.isna(median_val):
            continue

        if mean_type == "Arithmetic":
            dash = "dot"
            label = f"Arithmetic median = {median_val:.1f} min"
            y_offset = 1.02
        else:
            dash = "solid"
            label = f"Geometric median = {median_val:.1f} min"
            y_offset = 1.06

        fig.add_vline(x=median_val, line_width=2, line_dash=dash, line_color="black")
        fig.add_annotation(
            x=median_val,
            y=y_offset,
            yref="paper",
            text=label,
            showarrow=False,
            font=dict(size=12),
            align="center",
            bgcolor="rgba(255,255,255,0.8)"
        )

    fig.update_layout(
        xaxis_title="Minutes per day",
        yaxis_title="Study",
        legend_title="Mean type",
        margin=dict(l=40, r=40, t=110, b=40),
    )

    st.plotly_chart(fig, width="stretch")
