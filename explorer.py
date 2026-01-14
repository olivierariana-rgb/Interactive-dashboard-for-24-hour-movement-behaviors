# pages/1_Explorer.py
import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Explorer", page_icon="🔎", layout="wide")

# ============================================================
# HELPERS
# ============================================================
def summarize_filter(label, selected, all_options):
    selected = list(selected) if selected is not None else []
    all_options = list(all_options) if all_options is not None else []

    if len(selected) == 0:
        return f"{label}: none"

    if set(map(str, selected)) == set(map(str, all_options)):
        return f"{label}: all"

    return f"{label}: {', '.join(map(str, selected))}"

def auto_multiselect(df, label, column):
    options = sorted(df[column].dropna().unique())
    return st.sidebar.multiselect(label, options=options, default=options)

# ============================================================
# LOAD DATA
# ============================================================
df = pd.read_csv("dashboard_clean_input (2).csv")
meta = pd.read_csv("full_metadata (2).csv")

df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

# Keep only known age groups
df = df[df["Age_Group"].isin(["Children", "Adolescents", "Adult"])].copy()

df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult"],
    ordered=True
)

# Normalize subgroup
df["Subgroup_clean"] = (
    df["Subgroup"]
    .fillna("Full")
    .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

subgroups_available = sorted([s for s in df["Subgroup_clean"].unique() if s != "Full"])

# ============================================================
# SIDEBAR FILTERS (ONLY ONCE)
# ============================================================
st.sidebar.header("Filters")

age_filter     = auto_multiselect(df, "Age Group", "Age_Group")
brand_filter   = auto_multiselect(df, "Device Brand", "Device_Brand")
type_filter    = auto_multiselect(df, "Device Type", "Device_Type")
country_filter = auto_multiselect(df, "Country", "Country")
rate_filter    = auto_multiselect(df, "Sampling Rate (Hz)", "Sampling_Rate_Hz")
sleep_filter   = auto_multiselect(df, "Sleep Measurement Type", "Sleep_Measurement_Type")

st.sidebar.markdown("### Subgroup Selection")
subgroup_mode = st.sidebar.radio(
    "Choose subgroup filtering mode:",
    ["Full sample only", "All subgroups", "Specific subgroups"]
)

# ============================================================
# APPLY FILTERS
# ============================================================
df_f = df.copy()

if age_filter:     df_f = df_f[df_f["Age_Group"].isin(age_filter)]
if brand_filter:   df_f = df_f[df_f["Device_Brand"].isin(brand_filter)]
if type_filter:    df_f = df_f[df_f["Device_Type"].isin(type_filter)]
if country_filter: df_f = df_f[df_f["Country"].isin(country_filter)]
if rate_filter:    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(rate_filter)]
if sleep_filter:   df_f = df_f[df_f["Sleep_Measurement_Type"].isin(sleep_filter)]

# Subgroup mode
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

# ============================================================
# TITLE + SUMMARY
# ============================================================
st.title("24-Hour Movement Composition Explorer")
st.write("Compare arithmetic and geometric means across studies and visualize individual data points.")

st.markdown("### Current Selection Summary")

n_studies = df_f["StudyID"].nunique()
st.write(f"📊 **Number of studies meeting these criteria:** {n_studies}")

filter_summaries = [
    summarize_filter("Age group", age_filter, df["Age_Group"].unique()),
    summarize_filter("Device brand", brand_filter, df["Device_Brand"].unique()),
    summarize_filter("Device type", type_filter, df["Device_Type"].unique()),
    summarize_filter("Country", country_filter, df["Country"].unique()),
    summarize_filter("Sampling rate", rate_filter, df["Sampling_Rate_Hz"].unique()),
    summarize_filter("Sleep measurement", sleep_filter, df["Sleep_Measurement_Type"].unique()),
    f"Subgroup mode: {subgroup_mode}"
]
st.write("**Filters applied:**  \n" + " • " + "  \n • ".join(filter_summaries))

st.markdown("---")

# ============================================================
# PLOT 1 — STACKED BAR PANELS (Arithmetic vs Geometric)
# ============================================================
st.subheader("Arithmetic vs Geometric Means (by Age Group)")

arith = df_f[df_f["Mean_Type"] == "Arithmetic"].copy()
geo   = df_f[df_f["Mean_Type"] == "Geometric"].copy()

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

# ============================================================
# PLOT 2 — BEHAVIOR-LEVEL SCATTER (ZOOM VIEW)
# ============================================================
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
    # Order studies by year if available (sometimes Year is only in meta)
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

    # Add medians with readable labels (and skip missing types automatically)
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
            bgcolor="rgba(255,255,255,0.85)"
        )

    fig.update_layout(
        xaxis_title="Minutes per day",
        yaxis_title="Study",
        legend_title="Mean type",
        margin=dict(l=40, r=40, t=110, b=40),
    )

    st.plotly_chart(fig, width="stretch")

st.markdown("---")

# ============================================================
# FILTERED STUDY TABLES (moved here so no duplicate filters/pages)
# ============================================================
st.header("Study Tables (filtered by Explorer selection)")
st.caption("These tables reflect the filters selected in the Explorer sidebar above.")

# ---- Study-level breakdown (1 row per study) ----
st.subheader("Study-Level Breakdown (1 row per study)")

study_ids = df_f["StudyID"].dropna().unique()

if len(study_ids) == 0:
    st.warning("No studies match the current filters.")
else:
    st.info(f"Showing **{len(study_ids)} unique studies** based on current filters.")

    meta_filtered = meta[meta["StudyID"].isin(study_ids)].copy()

    # Prefer Full subgroup rows when possible
    if "Subgroup" in meta_filtered.columns:
        meta_filtered["Subgroup_clean"] = (
            meta_filtered["Subgroup"]
            .fillna("Full")
            .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
        )
        meta_filtered["is_full"] = (meta_filtered["Subgroup_clean"] == "Full").astype(int)
        meta_unique = (
            meta_filtered.sort_values(["StudyID", "is_full"], ascending=[True, False])
            .drop_duplicates(subset="StudyID", keep="first")
            .reset_index(drop=True)
        )
    else:
        meta_unique = (
            meta_filtered.sort_values("StudyID")
            .drop_duplicates(subset="StudyID", keep="first")
            .reset_index(drop=True)
        )

    metadata_cols = [
        "StudyID", "Year", "title", "Country",
        "Age_Group", "SampleSize", "Device_Brand", "Device_Type",
        "Sampling_Rate_Hz", "Sleep_Measurement_Type"
    ]
    metadata_cols = [c for c in metadata_cols if c in meta_unique.columns]

    st.dataframe(meta_unique[metadata_cols], width="stretch")

# ---- Subgroup summary ----
st.subheader("Subgroups Available Per Study")

if len(study_ids) > 0:
    subgroup_table = (
        df_f.groupby("StudyID")["Subgroup_clean"]
            .unique()
            .reset_index()
            .rename(columns={"Subgroup_clean": "Available_Subgroups"})
    )
    st.dataframe(subgroup_table, width="stretch")

# ---- Behavior summary wide ----
st.subheader("Behavior Summary (Wide Format: 1 row per Study + Subgroup)")

behaviors = ["Sleep", "SB", "LPA", "MVPA"]
df_beh4 = df_f[df_f["Behavior"].isin(behaviors)].copy()

if df_beh4.empty:
    st.warning("No behavior data available for current filters.")
else:
    wide_arith = (
        df_beh4[df_beh4["Mean_Type"] == "Arithmetic"]
        .pivot_table(index=["StudyID", "Subgroup_clean"], columns="Behavior", values="Minutes", aggfunc="mean")
        .add_prefix("A_")
        .reset_index()
        .rename(columns={"Subgroup_clean": "Subgroup"})
    )

    wide_geo = (
        df_beh4[df_beh4["Mean_Type"] == "Geometric"]
        .pivot_table(index=["StudyID", "Subgroup_clean"], columns="Behavior", values="Minutes", aggfunc="mean")
        .add_prefix("G_")
        .reset_index()
        .rename(columns={"Subgroup_clean": "Subgroup"})
    )

    wide_all = pd.merge(wide_arith, wide_geo, on=["StudyID", "Subgroup"], how="outer")
    st.dataframe(wide_all, width="stretch")
