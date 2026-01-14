# pages/1_Explorer.py
import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Explorer", page_icon="🔎", layout="wide")

st.markdown("# Explorer 🔎")
st.sidebar.header("Filters")

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
    if column not in df.columns:
        st.sidebar.warning(f"Missing column: {column}")
        return []
    options = sorted(df[column].dropna().unique())
    return st.sidebar.multiselect(label, options=options, default=options)


def clean_minutes(series):
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


# ============================================================
# LOAD DATA (robust file names)
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard_clean_input (1).csv")
    meta = pd.read_csv("full_metadata (1).csv")
    return df, meta


df, meta = load_data()

# Fix numeric type
if "Minutes" in df.columns:
    df["Minutes"] = clean_minutes(df["Minutes"])

# Keep only known age groups (consistent ordering)
df = df[df["Age_Group"].isin(["Children", "Adolescents", "Adult"])].copy()
df["Age_Group"] = pd.Categorical(df["Age_Group"], categories=["Children", "Adolescents", "Adult"], ordered=True)

# Normalize subgroup (for filtering)
df["Subgroup_clean"] = (
    df["Subgroup"]
    .fillna("Full")
    .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

# ============================================================
# SIDEBAR FILTERS (page-level)
# ============================================================
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

subgroups_available = sorted([s for s in df["Subgroup_clean"].dropna().unique() if s != "Full"])

# Apply filters
df_f = df.copy()

if age_filter:     df_f = df_f[df_f["Age_Group"].isin(age_filter)]
if brand_filter:   df_f = df_f[df_f["Device_Brand"].isin(brand_filter)]
if type_filter:    df_f = df_f[df_f["Device_Type"].isin(type_filter)]
if country_filter: df_f = df_f[df_f["Country"].isin(country_filter)]
if rate_filter:    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(rate_filter)]
if sleep_filter:   df_f = df_f[df_f["Sleep_Measurement_Type"].isin(sleep_filter)]

# subgroup mode
if subgroup_mode == "Full sample only":
    df_f = df_f[df_f["Subgroup_clean"] == "Full"]
elif subgroup_mode == "Specific subgroups":
    chosen_groups = st.sidebar.multiselect("Choose one or more subgroups:", options=subgroups_available)
    if len(chosen_groups) > 0:
        df_f = df_f[df_f["Subgroup_clean"].isin(chosen_groups)]
    else:
        st.sidebar.warning("Select at least one subgroup or switch mode.")

# ============================================================
# SUMMARY (top)
# ============================================================
st.markdown("### Current Selection Summary")
n_studies = df_f["StudyID"].nunique() if "StudyID" in df_f.columns else 0
st.write(f"📊 **Number of studies meeting these criteria:** {n_studies}")

filter_summaries = [
    summarize_filter("Age group", age_filter, df["Age_Group"].unique()),
    summarize_filter("Device brand", brand_filter, df["Device_Brand"].unique()),
    summarize_filter("Device type", type_filter, df["Device_Type"].unique()),
    summarize_filter("Country", country_filter, df["Country"].unique()),
    summarize_filter("Sampling rate", rate_filter, df["Sampling_Rate_Hz"].unique()),
    summarize_filter("Sleep measurement", sleep_filter, df["Sleep_Measurement_Type"].unique()),
    f"Subgroup mode: {subgroup_mode}",
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
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            orientation="h",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult"]},
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
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            orientation="h",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult"]},
        )
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(fig_g, width="stretch")
    else:
        st.info("No geometric data available after filtering.")

st.markdown("---")

# ============================================================
# PLOT 2 — BEHAVIOR-LEVEL SCATTER (Zoomed, local controls)
# ============================================================
st.subheader("Behavior-Level Scatter Plot")
st.caption(
    "Zoomed view within the currently selected studies. Changing behavior/age group here does not affect the sidebar filters."
)

beh_options = sorted(df_f["Behavior"].dropna().unique()) if "Behavior" in df_f.columns else []
if len(beh_options) == 0:
    st.warning("No behaviors available after filtering.")
    st.stop()

selected_behavior = st.selectbox("Zoom in on behavior:", beh_options)
selected_age = st.radio("Zoom in on age group:", ["Children", "Adolescents", "Adult"], horizontal=True)

df_beh = df_f[(df_f["Behavior"] == selected_behavior) & (df_f["Age_Group"] == selected_age)].copy()

# Clean and drop missing
df_beh["Minutes"] = clean_minutes(df_beh["Minutes"])
df_beh = df_beh.dropna(subset=["Minutes", "StudyID_display", "Mean_Type"])

if df_beh.empty:
    st.warning("No data available for this selection.")
else:
    # Order studies by year if it exists in THIS table
    if "Year" in df_beh.columns:
        df_beh = df_beh.sort_values(["Year", "StudyID_display"])
    else:
        df_beh = df_beh.sort_values("StudyID_display")

    # Median summary by Mean_Type
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
        height=700,
    )

    # Add reference lines + readable labels (only for types that exist)
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
            bgcolor="rgba(255,255,255,0.8)",
        )

    fig.update_layout(
        xaxis_title="Minutes per day",
        yaxis_title="Study",
        legend_title="Mean type",
        margin=dict(l=40, r=40, t=110, b=40),
    )

    st.plotly_chart(fig, width="stretch")
