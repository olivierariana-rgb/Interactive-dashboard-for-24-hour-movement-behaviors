import streamlit as st
import pandas as pd
import plotly.express as px

# ======================================================================
# HELPER FUNCTION — FILTER SUMMARY
# ======================================================================

def summarize_filter(label, selected, all_options):
    selected = list(selected) if selected is not None else []
    all_options = list(all_options) if all_options is not None else []

    if len(selected) == 0:
        return f"{label}: none"

    # If everything is selected
    if set(map(str, selected)) == set(map(str, all_options)):
        return f"{label}: all"

    return f"{label}: {', '.join(map(str, selected))}"

# ======================================================================
# LOAD DATA
# ======================================================================

df = pd.read_csv("dashboard_clean_input (1).csv")      # long format for plotting
meta = pd.read_csv("full_metadata (1).csv")            # full metadata if needed later

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
# FILTER SUMMARY
# ======================================================================

st.markdown("### Current Selection Summary")

# Number of unique studies after all filters
n_studies = df_f["StudyID"].nunique()

st.write(f"📊 **Number of studies meeting these criteria:** {n_studies}")

# Build readable filter descriptions
filter_summaries = [
    summarize_filter("Age group", age_filter, df["Age_Group"].unique()),
    summarize_filter("Device brand", brand_filter, df["Device_Brand"].unique()),
    summarize_filter("Device type", type_filter, df["Device_Type"].unique()),
    summarize_filter("Country", country_filter, df["Country"].unique()),
    summarize_filter("Sampling rate", rate_filter, df["Sampling_Rate_Hz"].unique()),
    summarize_filter("Sleep measurement", sleep_filter, df["Sleep_Measurement_Type"].unique()),
    f"Subgroup mode: {subgroup_mode}"
]

st.write(
    "**Filters applied:**  \n" +
    " • " + "  \n • ".join(filter_summaries)
)

st.markdown("---")
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
            category_orders={"Age_Group": ["Children","Adolescents","Adult"]}
        )
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(fig_g, width="stretch")
    else:
        st.info("No geometric data available after filtering.")


# ============================================================
# BEHAVIOR-LEVEL SCATTER PLOT — Zoomed View
# ============================================================

st.subheader("Behavior-Level Scatter Plot")

st.caption(
    "This view provides a focused look within the currently selected studies. "
    "Changing the behavior or age group here does not affect the global filters above."
)

# --------------------------------------------------
# Local (zoom) controls
# --------------------------------------------------

selected_behavior = st.selectbox(
    "Zoom in on behavior:",
    sorted(df_f["Behavior"].dropna().unique())
)

selected_age = st.radio(
    "Zoom in on age group:",
    ["Children", "Adolescents", "Adult"],
    horizontal=True
)

# --------------------------------------------------
# Filtered data (local only)
# --------------------------------------------------

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
    # --------------------------------------------------
    # Order studies by year (if available)
    # --------------------------------------------------
    if "Year" in df_beh.columns:
        df_beh = df_beh.sort_values(["Year", "StudyID_display"])
    else:
        df_beh = df_beh.sort_values("StudyID_display")

    # --------------------------------------------------
    # Median summary (only what exists)
    # --------------------------------------------------
    summary = (
        df_beh
        .groupby("Mean_Type")["Minutes"]
        .median()
        .reset_index()
        .rename(columns={"Minutes": "Median"})
    )

    # --------------------------------------------------
    # Scatter plot
    # --------------------------------------------------
    fig = px.scatter(
        df_beh,
        x="Minutes",
        y="StudyID_display",
        color="Mean_Type",
        symbol="Mean_Type",
        symbol_map={
            "Arithmetic": "circle",
            "Geometric": "triangle-up"
        },
        title=f"{selected_behavior} — {selected_age}",
        height=700
    )

    # --------------------------------------------------
    # Add median reference lines + labels
    # --------------------------------------------------
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

        fig.add_vline(
            x=median_val,
            line_width=2,
            line_dash=dash,
            line_color="black",
        )

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

    # --------------------------------------------------
    # Layout polish (ONCE)
    # --------------------------------------------------
    fig.update_layout(
        xaxis_title="Minutes per day",
        yaxis_title="Study",
        legend_title="Mean type",
        margin=dict(l=40, r=40, t=110, b=40),
    )

    # --------------------------------------------------
    # Display (ONCE)
    # --------------------------------------------------
    st.plotly_chart(fig, use_container_width=True)
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

# ======================================================================
# --------------------------------------------------
#  SIMPLEX WITH SLIDER - GEOMETRIC MEANS ONLY
# --------------------------------------------------

st.subheader("Ternary Simplex (Geometric Means Only)")

# === Choose which variable will control the slider ===
simplex_var = st.selectbox(
    "Choose a variable to explore:",
    ["Sampling_Rate_Hz", "Device_Brand", "Device_Type", "Country", "Year"]
)

# Get unique categories for slider
simplex_levels = sorted(meta[simplex_var].dropna().unique())

if len(simplex_levels) == 0:
    st.warning(f"No available categories for {simplex_var}.")
else:
    # Slider to choose one category at a time
    slider_choice = st.select_slider(
        f"Select {simplex_var} level:",
        options=simplex_levels
    )

    # --------------------------------------------------
    # FILTER DATA: only geometric means + selected level
    # --------------------------------------------------
    # Get wide-format table from earlier section
    # Ensure wide_all exists in this runtime
    try:
        wide_df = wide_all.copy()
    except:
        st.error("wide_all is not defined yet. Move this block below the Behavior Summary section.")
        st.stop()

    # Merge metadata
    wide_df = wide_df.merge(meta, on="StudyID", how="left")

    # Keep only rows matching the slider selection
    wide_sel = wide_df[wide_df[simplex_var] == slider_choice].copy()

    # Must have geometric means
    needed = ["G_Sleep", "G_SB", "G_MVPA"]
    wide_sel = wide_sel.dropna(subset=needed)

    if wide_sel.empty:
        st.warning(f"No studies match {simplex_var} = {slider_choice}.")
    else:
        # --------------------------------------------------
        # CLose compositions using geometric means
        # --------------------------------------------------
        wide_sel["sum_geo"] = (
            wide_sel["G_Sleep"] +
            wide_sel["G_SB"] +
            wide_sel["G_MVPA"]
        )

        wide_sel["Sleep_cl"] = wide_sel["G_Sleep"] / wide_sel["sum_geo"]
        wide_sel["SB_cl"]    = wide_sel["G_SB"]    / wide_sel["sum_geo"]
        wide_sel["MVPA_cl"]  = wide_sel["G_MVPA"]  / wide_sel["sum_geo"]

        # --------------------------------------------------
        # Plot: Ternary Simplex
        # --------------------------------------------------
        import plotly.express as px

        fig_simplex = px.scatter_ternary(
            wide_sel,
            a="Sleep_cl",
            b="SB_cl",
            c="MVPA_cl",
            hover_name="StudyID",
            hover_data={simplex_var: True},
            color="StudyID",
            title=f"Ternary Simplex for {simplex_var} = {slider_choice}"
        )

        fig_simplex.update_traces(marker=dict(size=12, opacity=0.8))

        st.plotly_chart(fig_simplex, use_container_width=True)

# ======================================================================
# METADATA BASE (for Results Engine only)
# ======================================================================

st.markdown("---")
st.header("Results Engine — Study Methodology Overview")
st.caption(
    "This section summarizes methodological patterns across all included studies. "
    "It is based on metadata only and is not affected by interactive filters above."
)

# --------------------------------------------------
# Base metadata: ONE row per study
# Prefer Subgroup == Full when available
# --------------------------------------------------

meta_base = meta.copy()

# Normalize subgroup
meta_base["Subgroup_clean"] = (
    meta_base["Subgroup"]
    .fillna("Full")
    .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

# Prefer Full rows
meta_base["is_full"] = (meta_base["Subgroup_clean"] == "Full").astype(int)

meta_base = (
    meta_base
    .sort_values(["StudyID", "is_full"], ascending=[True, False])
    .drop_duplicates(subset="StudyID", keep="first")
    .reset_index(drop=True)
)

st.write(f"📊 **Total included studies:** {len(meta_base)}")

# --------------------------------------------------
# MOST COMMON METHODOLOGICAL CHOICES (by age group)
# --------------------------------------------------

st.subheader("Most Common Methodological Choices")
st.caption(
    "Top methodological decisions within the selected age group. "
    "Percentages are calculated within the selection using metadata only."
)

# Age group selector (includes ALL)
age_choice = st.radio(
    "Select age group:",
    ["All", "Children", "Adolescents", "Adults"],
    horizontal=True
)

# Apply age filter
if age_choice == "All":
    meta_age = meta_base.copy()
else:
    meta_age = meta_base[meta_base["Age_Group"] == age_choice].copy()

n_studies = len(meta_age)

if n_studies == 0:
    st.warning(f"No studies available for **{age_choice}**.")
else:
    st.info(f"📊 {n_studies} studies included for **{age_choice}**")

    method_vars = {
        "Device Brand": "Device_Brand",
        "Device Type": "Device_Type",
        "Sampling Rate (Hz)": "Sampling_Rate_Hz",
        "Sleep Measurement Type": "Sleep_Measurement_Type",
        "Cutpoint Type": "Cutpoint_Type",
        "Primary Analysis Type": "Primary_Analysis_Type",
        "Isotemporal Substitution Applied": "Compositional_Isotemporal_Substitution_Applied_Yes_No",
        "Time Reallocation Increment (min)": "Time_Reallocation_Increment_minutes",
        "Stratified Analyses": "Stratified_Analyses",
        "Sensitivity Analyses": "Sensitivity_Analyses",
        "Bootstrap": "Bootstrap",
    }

for label, col in method_vars.items():
    if col not in meta_age.columns:
        continue

    st.markdown(f"### {label}")

    counts = meta_age[col].fillna("NR").value_counts()
    total = counts.sum()

    if total == 0:
        st.write("• No data available")
        st.divider()
        continue

    top3 = counts.head(3)

    for val, cnt in top3.items():
        pct = round(100 * cnt / total, 1)
        st.write(f"• **{val}** — {cnt} studies ({pct}%)")

    # Explicit NR if needed
    if "NR" in counts.index and "NR" not in top3.index:
        nr_cnt = counts["NR"]
        pct_nr = round(100 * nr_cnt / total, 1)
        st.write(f"• **NR** — {nr_cnt} studies ({pct_nr}%)")

    # =================================================
    # 🔹 DEVICE MODEL BREAKDOWN (ONLY FOR DEVICE BRAND)
    # =================================================
    if label == "Device Brand" and "Device_Model" in meta_age.columns:
        st.markdown("**Device models used (within brand):**")

        for brand, brand_n in counts.items():
            st.markdown(f"*{brand}* (n = {brand_n})")

            sub_brand = meta_age[meta_age["Device_Brand"] == brand]

            model_counts = (
                sub_brand["Device_Model"]
                .fillna("NR")
                .value_counts()
            )

            for model, m_cnt in model_counts.items():
                pct_m = round(100 * m_cnt / brand_n, 1)
                st.write(f"• {model} — {m_cnt} studies ({pct_m}%)")

    st.divider()
# --------------------------------------------------
# REPORTING COMPLETENESS (Missingness)
# --------------------------------------------------

st.subheader("Reporting Completeness")

report_vars = [
    "Device_Brand",
    "Device_Type",
    "Sampling_Rate_Hz",
    "Sleep_Measurement_Type",
    "Cutpoint_Type",
    "Wear_Days_Instructed",
    "Valid_Hours_Per_Day",
    "Primary_Analysis_Type",
    "Bootstrap",
    "Sensitivity_Analyses"
]

missing_summary = []

for var in report_vars:
    if var not in meta_base.columns:
        continue

    total = len(meta_base)
    missing = meta_base[var].isna().sum()

    missing_summary.append({
        "Variable": var,
        "Reported (%)": round(100 * (total - missing) / total, 1),
        "Missing (%)": round(100 * missing / total, 1)
    })

missing_df = pd.DataFrame(missing_summary)

st.dataframe(missing_df, use_container_width=True)

# --------------------------------------------------
# HETEROGENEITY SUMMARY
# --------------------------------------------------

st.subheader("Methodological Heterogeneity")

heterogeneity = []

for col in method_vars.values():
    if col not in meta_base.columns:
        continue

    heterogeneity.append({
        "Methodological Dimension": col,
        "Number of Unique Choices": meta_base[col].dropna().nunique()
    })

hetero_df = pd.DataFrame(heterogeneity)

st.dataframe(hetero_df, use_container_width=True)

# ============================================================
# METHOD COMPARISON GRID — variation across methodological choices
# Rows = methodological dimensions, Cols = behaviors
# ============================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------
# Helpers
# ---------------------------

def _clean_minutes(x):
    return pd.to_numeric(
        pd.Series(x).astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )

def summarize_choice_variation(df_f, meta, behavior, mean_type, method_col):
    """
    One summary line for: (behavior, mean_type) showing variability ACROSS method choices.
    Steps:
      1) One value per study (median if duplicates)
      2) Attach method choice from meta
      3) For each choice: median across studies
      4) Summarize distribution of choice-medians: min/q25/median/q75/max
    """
    if method_col not in meta.columns:
        return None

    d = df_f[(df_f["Behavior"] == behavior) & (df_f["Mean_Type"] == mean_type)].copy()
    if d.empty:
        return None

    d["Minutes"] = _clean_minutes(d["Minutes"])
    d = d.dropna(subset=["StudyID", "Minutes"])
    if d.empty:
        return None

    # 1) One value per StudyID
    per_study = (
        d.groupby("StudyID", as_index=False)["Minutes"]
         .median()
         .rename(columns={"Minutes": "StudyValue"})
    )

    # 2) Attach method choice from metadata
    m = meta[["StudyID", method_col]].copy()
    m[method_col] = m[method_col].fillna("NR").astype(str)

    merged = per_study.merge(m, on="StudyID", how="left")
    merged[method_col] = merged[method_col].fillna("NR").astype(str)

    # 3) For each choice: median across studies
    by_choice = (
        merged.groupby(method_col)["StudyValue"]
              .agg(choice_median="median", n_studies="count")
              .reset_index()
              .rename(columns={method_col: "Choice"})
              .sort_values("choice_median", ascending=True)
              .reset_index(drop=True)
    )

    vals = by_choice["choice_median"].dropna().values
    if len(vals) == 0:
        return None

    return {
        "n_choices": int(by_choice["Choice"].nunique()),
        "min": float(np.min(vals)),
        "q25": float(np.percentile(vals, 25)),
        "median": float(np.median(vals)),
        "q75": float(np.percentile(vals, 75)),
        "max": float(np.max(vals)),
        "by_choice": by_choice
    }

def plot_choice_variation_cell(summary, title, x_label="Minutes/day"):
    """
    Draws:
      - thin line: min -> max
      - thick line: q25 -> q75
      - dot: median
    """
    fig = go.Figure()

    if summary is None:
        fig.update_layout(
            title=title,
            height=250,
            margin=dict(l=10, r=10, t=45, b=35),
            xaxis_title=x_label,
            yaxis_visible=False
        )
        fig.add_annotation(
            text="No data",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False
        )
        return fig

    # thin range line
    fig.add_shape(
        type="line",
        x0=summary["min"], x1=summary["max"],
        y0=0, y1=0,
        xref="x", yref="y",
        line=dict(width=3),
        opacity=0.25
    )

    # thick IQR line
    fig.add_shape(
        type="line",
        x0=summary["q25"], x1=summary["q75"],
        y0=0, y1=0,
        xref="x", yref="y",
        line=dict(width=8),
        opacity=0.35
    )

    # median dot
    fig.add_trace(
        go.Scatter(
            x=[summary["median"]],
            y=[0],
            mode="markers",
            marker=dict(size=12),
            hovertemplate=(
                f"Median across choices: {summary['median']:.1f}<br>"
                f"IQR: [{summary['q25']:.1f}, {summary['q75']:.1f}]<br>"
                f"Range: [{summary['min']:.1f}, {summary['max']:.1f}]<br>"
                f"n choices: {summary['n_choices']}<extra></extra>"
            ),
            showlegend=False
        )
    )

    fig.update_layout(
        title=title,
        height=250,
        margin=dict(l=10, r=10, t=45, b=35),
        xaxis_title=x_label,
        yaxis_visible=False,
        yaxis_range=[-1, 1]
    )

    return fig

# ---------------------------
# GRID SETTINGS
# ---------------------------

st.markdown("## Method Comparison (variation across methodological choices)")
st.caption(
    "Each panel shows one behavior. The dot is the median across methodological choices, "
    "the thick segment is the IQR, and the thin segment is the full range."
)

# Which mean type to use for the grid
mc_mean_type = "Geometric"   # or "Arithmetic"

# ✅ Put whatever method columns you want here (these must exist in meta)
method_rows = [
    "Cutpoint_Type",
    "Device_Brand",
    "Device_Type",
    "Sampling_Rate_Hz",
    "Sleep_Measurement_Type",
    # add more if you want:
    # "Wear_Days_Instructed",
    # "Valid_Hours_Per_Day",
]

behaviors = ["Sleep", "SB", "LPA", "MVPA"]

# Store detail tables so the expander can show them
details_grid = {}  # details_grid[method_col][behavior] = summary dict

# ---------------------------
# BUILD GRID
# ---------------------------

for method_col in method_rows:
    if method_col not in meta.columns:
        st.warning(f"Skipping `{method_col}` (not found in metadata).")
        continue

    st.markdown(f"### {method_col} — {mc_mean_type} estimates")

    cols = st.columns(4)
    details_grid[method_col] = {}

    for i, b in enumerate(behaviors):
        summ = summarize_choice_variation(df_f, meta, b, mc_mean_type, method_col)
        details_grid[method_col][b] = summ

        fig = plot_choice_variation_cell(
            summ,
            title=b,
            x_label="Minutes/day"
        )
        cols[i].plotly_chart(fig, width="stretch")

# ---------------------------
# OPTIONAL DETAILS
# ---------------------------

with st.expander("Show underlying choice medians (details)"):
    st.write(
        "For each methodological dimension, this shows the median estimate *within each choice* "
        "(e.g., each cutpoint type), which is what the range/IQR/median are computed from."
    )

    for method_col in details_grid:
        st.markdown(f"#### {method_col}")
        for b in behaviors:
            s = details_grid[method_col].get(b)

            if s is None:
                st.write(f"**{b}**: No data")
                continue

            st.write(f"**{b}** (n choices = {s['n_choices']})")
            st.dataframe(s["by_choice"], width="stretch")





