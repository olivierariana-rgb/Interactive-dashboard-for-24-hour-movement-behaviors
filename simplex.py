import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Simplex", page_icon="🔺", layout="wide")

# --------------------------------------------------
# LOAD DATA (page-local)
# --------------------------------------------------
df = pd.read_csv("dashboard_clean_input (2).csv")
meta = pd.read_csv("full_metadata (2).csv")

df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

# Optional: keep standard age groups
if "Age_Group" in df.columns:
    df = df[df["Age_Group"].isin(["Children", "Adolescents", "Adult"])]

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.write("## Compare simplex across methodological choices")
st.caption(
    "Select 2–4 levels of a variable and compare geometric-mean compositions side-by-side. "
    "This page does not use Explorer filters."
)

# --------------------------------------------------
# USER CONTROLS
# --------------------------------------------------
compare_var = st.selectbox(
    "Compare by:",
    ["Device_Brand", "Device_Type", "Sampling_Rate_Hz", "Country", "Year",
     "Sleep_Measurement_Type", "Cutpoint_Type"]
)

if compare_var not in meta.columns:
    st.error(f"`{compare_var}` not found in metadata.")
    st.stop()

levels = sorted(meta[compare_var].dropna().astype(str).unique().tolist())

selected_levels = st.multiselect(
    f"Select 2–4 {compare_var} levels to compare:",
    options=levels,
    default=levels[:2] if len(levels) >= 2 else levels
)

if len(selected_levels) < 1:
    st.warning("Select at least 1 level.")
    st.stop()

if len(selected_levels) > 4:
    st.warning("Please select at most 4 levels (for readability).")
    st.stop()

# Optional age filter (local to this page)
age_opts = ["All"]
if "Age_Group" in df.columns:
    age_opts += ["Children", "Adolescents", "Adult"]

age_choice = st.selectbox("Optional age group filter (local to this page):", age_opts)

# --------------------------------------------------
# BUILD WIDE TABLE (ONE ROW PER STUDY) — GEOMETRIC ONLY
# --------------------------------------------------
behaviors_needed = ["Sleep", "SB", "MVPA"]

df_g = df[(df["Mean_Type"] == "Geometric") & (df["Behavior"].isin(behaviors_needed))].copy()

if age_choice != "All" and "Age_Group" in df_g.columns:
    df_g = df_g[df_g["Age_Group"] == age_choice]

if df_g.empty:
    st.warning("No geometric mean data available for simplex.")
    st.stop()

# Prefer Full sample when available (so each StudyID is single-valued)
if "Subgroup" in df_g.columns:
    df_g["Subgroup_clean"] = (
        df_g["Subgroup"]
        .fillna("Full")
        .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
    )
else:
    df_g["Subgroup_clean"] = "Full"

df_g["is_full"] = (df_g["Subgroup_clean"] == "Full").astype(int)

# Keep FULL rows when they exist; otherwise keep whatever exists
df_g = (
    df_g.sort_values(["StudyID", "Behavior", "is_full"], ascending=[True, True, False])
        .drop_duplicates(subset=["StudyID", "Behavior"], keep="first")
        .reset_index(drop=True)
)

# Now pivot: one row per StudyID
wide_geo = (
    df_g.pivot_table(
        index="StudyID",
        columns="Behavior",
        values="Minutes",
        aggfunc="mean"
    )
    .reset_index()
)

# Attach compare_var from metadata (also one row per StudyID)
meta_one = meta[["StudyID", compare_var]].copy()
meta_one[compare_var] = meta_one[compare_var].fillna("NR").astype(str)

# If meta has duplicate StudyID rows, keep first
meta_one = meta_one.drop_duplicates(subset="StudyID", keep="first")

wide_geo = wide_geo.merge(meta_one, on="StudyID", how="left")
wide_geo[compare_var] = wide_geo[compare_var].fillna("NR").astype(str)

# Must have all 3 behaviors to be plotted
wide_geo = wide_geo.dropna(subset=behaviors_needed)

if wide_geo.empty:
    st.warning("No studies have complete (Sleep, SB, MVPA) geometric means after filtering.")
    st.stop()

# --------------------------------------------------
# FUNCTION: PLOT ONE LEVEL
# --------------------------------------------------
def make_simplex_for_level(wide_df, level_value, compare_var_name):
    sub = wide_df[wide_df[compare_var_name] == str(level_value)].copy()
    if sub.empty:
        return None, 0

    # Close to 1
    sub["sum_geo"] = sub["Sleep"] + sub["SB"] + sub["MVPA"]
    sub = sub[sub["sum_geo"] > 0].copy()

    sub["Sleep_cl"] = sub["Sleep"] / sub["sum_geo"]
    sub["SB_cl"] = sub["SB"] / sub["sum_geo"]
    sub["MVPA_cl"] = sub["MVPA"] / sub["sum_geo"]

    n_unique = sub["StudyID"].nunique()

    fig = px.scatter_ternary(
        sub,
        a="Sleep_cl",
        b="SB_cl",
        c="MVPA_cl",
        hover_name="StudyID",
        hover_data=[compare_var_name],
        title=f"{compare_var_name} = {level_value}"
    )
    fig.update_traces(marker=dict(size=10, opacity=0.8))
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=10))

    return fig, n_unique

# --------------------------------------------------
# DISPLAY PANELS
# --------------------------------------------------
st.markdown("---")
st.write("### Simplex panels")

cols = st.columns(len(selected_levels))

for i, lvl in enumerate(selected_levels):
    fig, n_unique = make_simplex_for_level(wide_geo, lvl, compare_var)

    with cols[i]:
        if fig is None:
            st.info(f"No studies for **{lvl}**.")
        else:
            st.caption(f"n = {n_unique} unique studies")
            st.plotly_chart(fig, width="stretch")

# Optional sanity check
with st.expander("Debug: how many unique studies exist on this page?"):
    st.write(f"Unique studies with complete simplex parts: **{wide_geo['StudyID'].nunique()}**")
    st.write("Counts by selected level:")
    st.dataframe(
        wide_geo[wide_geo[compare_var].isin([str(x) for x in selected_levels])]
        .groupby(compare_var)["StudyID"]
        .nunique()
        .reset_index(name="n_unique_studies"),
        width="stretch"
    )
