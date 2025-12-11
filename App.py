import streamlit as st
import pandas as pd
import plotly.express as px

# ======================================================================
# LOAD DATA
# ======================================================================

df = pd.read_csv("dashboard_clean_input.csv")      # long format for plotting
meta = pd.read_csv("full_metadata.csv")            # full metadata if needed later

# Fix numeric types
df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

# Remove Unknown age group
df = df[df["Age_Group"].isin(["Children", "Adolescents", "Adult"])]

# Ensure age group ordering
df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult"],
    ordered=True
)

# ======================================================================
# SIDEBAR FILTERS
# ======================================================================

st.sidebar.header("Filters")

# All filters automatically adapt to dataset categories
def auto_multiselect(label, column):
    options = sorted(df[column].dropna().unique())
    return st.sidebar.multiselect(label, options=options, default=options)

age_filter     = auto_multiselect("Age Group", "Age_Group")
brand_filter   = auto_multiselect("Device Brand", "Device_Brand")
type_filter    = auto_multiselect("Device Type", "Device_Type")
country_filter = auto_multiselect("Country", "Country")
rate_filter    = auto_multiselect("Sampling Rate (Hz)", "Sampling_Rate_Hz")
sleep_filter   = auto_multiselect("Sleep Measurement Type", "Sleep_Measurement_Type")


# ======================================================================
# NEW SUBGROUP FILTER
# ======================================================================

# Normalize subgroup variable
df["Subgroup_clean"] = (
    df["Subgroup"]
    .fillna("Full")
    .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

# Unique subgroup list (excluding "Full")
subgroups_available = sorted([s for s in df["Subgroup_clean"].unique() if s != "Full"])

st.sidebar.markdown("### Subgroup Selection")

subgroup_mode = st.sidebar.radio(
    "Choose subgroup filtering mode:",
    ["Full sample only", "All subgroups", "Specific subgroups"]
)

# Copy filtered dataset
df_f = df.copy()

# Apply basic filters first
if age_filter:     df_f = df_f[df_f["Age_Group"].isin(age_filter)]
if brand_filter:   df_f = df_f[df_f["Device_Brand"].isin(brand_filter)]
if type_filter:    df_f = df_f[df_f["Device_Type"].isin(type_filter)]
if country_filter: df_f = df_f[df_f["Country"].isin(country_filter)]
if rate_filter:    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(rate_filter)]
if sleep_filter:   df_f = df_f[df_f["Sleep_Measurement_Type"].isin(sleep_filter)]

# Add normalized subgroup column to df_f as well
df_f["Subgroup_clean"] = (
    df_f["Subgroup"]
    .fillna("Full")
    .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

# Apply subgroup mode
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
# TITLE
# ======================================================================

st.title("24-Hour Movement Composition Explorer")
st.write("Compare arithmetic and geometric means across studies and visualize individual data points.")

# ======================================================================
# PLOT 1 — STACKED BAR PANELS (Arithmetic vs Geometric)
# ======================================================================

st.subheader("Arithmetic vs Geometric Means (by Age Group)")

arith = df_f[df_f["Mean_Type"] == "Arithmetic"]
geo   = df_f[df_f["Mean_Type"] == "Geometric"]

# Compute aggregated means
arith_means = (
    arith.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"].mean().reset_index()
)
geo_means = (
    geo.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"].mean().reset_index()
)

col1, col2 = st.columns(2)

# ---- Arithmetic panel ----
with col1:
    st.write("**Arithmetic Means**")
    if not arith_means.empty:
        fig_a = px.bar(
            arith_means,
            x="Minutes", y="Age_Group",
            color="Behavior",
            orientation="h",
            title="Arithmetic Means",
            category_orders={"Age_Group": ["Children","Adolescents","Adult"]}
        )
        fig_a.update_layout(barmode="stack")
        st.plotly_chart(fig_a, width="stretch")
    else:
        st.info("No arithmetic data available after filtering.")

# ---- Geometric panel ----
with col2:
    st.write("**Geometric Means**")
    if not geo_means.empty:
        fig_g = px.bar(
            geo_means,
            x="Minutes", y="Age_Group",
            color="Behavior",
            orientation="h",
            title="Geometric Means",
            category_orders={"Age_Group": ["Children","Adolescents","Adult"]}
        )
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(fig_g, width="stretch")
    else:
        st.info("No geometric data available after filtering.")
# ============================================================
# IMPROVED SCATTER PANEL — One behavior at a time
# ============================================================

import plotly.graph_objects as go

st.subheader("Behavior-Level Scatter Plot")

# User selects ONE behavior
selected_behavior = st.selectbox(
    "Select a behavior to visualize:",
    sorted(df_f["Behavior"].unique())
)

# Filter dataset
df_beh = df_f[df_f["Behavior"] == selected_behavior].copy()

if df_beh.empty:
    st.warning("No data available for this behavior under current filters.")
else:

    # Compute mean arithmetic and geometric per age group
    mean_table = (
        df_beh.groupby(["Age_Group", "Mean_Type"], observed=False)["Minutes"]
        .mean()
        .reset_index()
    )

    # Sort studies for prettier display
    df_beh["StudyID_display"] = df_beh["StudyID_display"].astype(str)
    df_beh = df_beh.sort_values("Minutes")

    # --------------------------
    # Build scatter — facet by AGE GROUP (rows)
    # --------------------------
    fig2 = px.scatter(
        df_beh,
        x="Minutes",
        y="StudyID_display",
        color="Mean_Type",
        symbol="Mean_Type",
        symbol_map={"Arithmetic": "circle", "Geometric": "triangle-up"},
        facet_row="Age_Group",
        category_orders={"Age_Group": ["Children","Adolescents","Adult"]},
        height=900,
        title=f"Study Estimates for {selected_behavior}"
    )

    # --------------------------
    # Add MEAN LINES per facet
    # --------------------------
    age_order = ["Children", "Adolescents", "Adult"]

    for age_group in age_order:
        sub_mean = mean_table[mean_table["Age_Group"] == age_group]
        if sub_mean.empty:
            continue

        # Determine facet row index
        row_num = age_order.index(age_group) + 1

        for _, r in sub_mean.iterrows():
            # Mean vertical line
            fig2.add_vline(
                x=r["Minutes"],
                line=dict(color="black", width=2, dash="dot"),
                row=row_num,
                col=1
            )

            # Mean diamond marker
            fig2.add_trace(
                go.Scatter(
                    x=[r["Minutes"]],
                    y=[df_beh["StudyID_display"].iloc[-1]],  # place at top row
                    mode="markers",
                    marker=dict(size=14, color="black", symbol="diamond"),
                    showlegend=False,
                    name=f"{age_group} Mean ({r['Mean_Type']})"
                ),
                row=row_num,
                col=1
            )

    # --------------------------
    # Style improvements
    # --------------------------
    fig2.update_layout(
        legend_title="Mean Type",
        margin=dict(l=40, r=40, t=80, b=40),
        height=1100
    )

    # Dark facet labels
    fig2.for_each_annotation(
        lambda a: a.update(
            font=dict(color="white", size=14),
            bgcolor="#444444"
        )
    )

    st.plotly_chart(fig2, width="stretch")
# --------------------------------------------------
#  STUDY-LEVEL BREAKDOWN (ONE ROW PER STUDY)
# --------------------------------------------------
st.subheader("Study-Level Breakdown (1 row per study)")

# 1️⃣ Identify unique studies from filtered dashboard data
study_ids = df_f["StudyID"].unique()

if len(study_ids) == 0:
    st.warning("No studies match the current filters.")
else:
    st.info(f"Showing **{len(study_ids)} unique studies** based on current filters.")

    # 2️⃣ Pull metadata rows for these studies
    meta_filtered = meta[meta["StudyID"].isin(study_ids)].copy()

    # 3️⃣ Keep only ONE row per StudyID (first occurrence)
    meta_unique = (
        meta_filtered
        .sort_values("StudyID")
        .drop_duplicates(subset="StudyID", keep="first")
        .reset_index(drop=True)
    )

    # 4️⃣ Choose metadata columns to display
    metadata_cols = [
        "StudyID", "Year", "title", "Country",
        "Age_Group", "SampleSize", "Device_Brand", "Device_Type",
        "Sampling_Rate_Hz", "Sleep_Measurement_Type"
    ]

    metadata_cols = [c for c in metadata_cols if c in meta_unique.columns]

    st.write("### Study Characteristics (1 row per study)")
    st.dataframe(meta_unique[metadata_cols])


    # --------------------------------------------------
    #  SUBGROUP SUMMARY TABLE
    # --------------------------------------------------
    st.write("### Subgroups Available Per Study")

    subgroup_table = (
        df_f.groupby("StudyID")["Subgroup"]
            .unique()
            .reset_index()
            .rename(columns={"Subgroup": "Available_Subgroups"})
    )

    st.dataframe(subgroup_table)

# --------------------------------------------------
#  BEHAVIOR SUMMARY TABLE (WIDE FORMAT)
# --------------------------------------------------
st.write("### Behavior Summary (Wide Format: 1 row per Study + Subgroup)")

# Keep only the behaviors you want included
behaviors = ["Sleep", "SB", "LPA", "MVPA"]

# Filter only relevant rows
df_beh4 = df_f[df_f["Behavior"].isin(behaviors)].copy()

if df_beh4.empty:
    st.warning("No behavior data available for current filters.")
else:
    # Pivot arithmetic and geometric separately
    wide_arith = (
        df_beh4[df_beh4["Mean_Type"] == "Arithmetic"]
        .pivot_table(index=["StudyID", "Subgroup"],
                     columns="Behavior",
                     values="Minutes",
                     aggfunc="mean")
        .add_prefix("A_")
        .reset_index()
    )

    wide_geo = (
        df_beh4[df_beh4["Mean_Type"] == "Geometric"]
        .pivot_table(index=["StudyID", "Subgroup"],
                     columns="Behavior",
                     values="Minutes",
                     aggfunc="mean")
        .add_prefix("G_")
        .reset_index()
    )

    # Merge arithmetic + geometric
    wide_all = pd.merge(wide_arith, wide_geo, on=["StudyID", "Subgroup"], how="outer")

    # Display table 
    st.dataframe(wide_all)
