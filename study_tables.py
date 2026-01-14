# study_tables.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Study Tables", page_icon="📋", layout="wide")

st.title("Study Tables")
st.caption(
    "This page shows the full extraction tables (metadata + behavior estimates) to support verification. "
    "It is not affected by filters on other pages."
)

st.markdown("---")

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_meta():
    meta = pd.read_csv("full_metadata (2).csv")
    if "StudyID" not in meta.columns:
        raise ValueError("`StudyID` column not found in full_metadata CSV.")
    return meta

@st.cache_data
def load_long():
    df = pd.read_csv("dashboard_clean_input (1).csv")
    if "StudyID" not in df.columns:
        raise ValueError("`StudyID` column not found in dashboard_clean_input CSV.")
    return df

try:
    meta = load_meta()
    df_long = load_long()
except Exception as e:
    st.error(f"Could not load data files. Error: {e}")
    st.stop()

# Clean Minutes if present
if "Minutes" in df_long.columns:
    df_long["Minutes"] = pd.to_numeric(
        df_long["Minutes"].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )

# ============================================================
# CONTROLS (LIGHT FILTERING + SEARCH)
# ============================================================

st.subheader("Full Metadata Table (one row per record in your extraction sheet)")

colA, colB, colC, colD = st.columns([2, 1, 1, 1])

with colA:
    search = st.text_input(
        "Search (StudyID, title, country, device brand, etc.)",
        placeholder="Try: ActiGraph, Canada, 2019, GT3X, etc."
    )

with colB:
    if "Year" in meta.columns:
        years = sorted(meta["Year"].dropna().unique().tolist())
        year_pick = st.multiselect("Year", options=years, default=years)
    else:
        year_pick = None

with colC:
    if "Age_Group" in meta.columns:
        ages = sorted(meta["Age_Group"].dropna().unique().tolist())
        age_pick = st.multiselect("Age group", options=ages, default=ages)
    else:
        age_pick = None

with colD:
    show_cols_mode = st.selectbox(
        "Columns",
        ["Key columns", "All columns"],
        index=0
    )

meta_view = meta.copy()

# Apply light filters
if year_pick is not None and "Year" in meta_view.columns:
    meta_view = meta_view[meta_view["Year"].isin(year_pick)]

if age_pick is not None and "Age_Group" in meta_view.columns:
    meta_view = meta_view[meta_view["Age_Group"].isin(age_pick)]

# Apply search across multiple text-like columns
if search.strip():
    s = search.strip().lower()
    # pick a reasonable set of columns to search
    candidate_cols = [c for c in meta_view.columns if meta_view[c].dtype == "object"] + \
                     [c for c in ["StudyID", "Year"] if c in meta_view.columns]
    candidate_cols = list(dict.fromkeys(candidate_cols))  # unique preserving order

    mask = False
    for c in candidate_cols:
        mask = mask | meta_view[c].astype(str).str.lower().str.contains(s, na=False)
    meta_view = meta_view[mask]

# Choose columns to display
key_cols = [
    "StudyID", "Year", "title", "Country", "Age_Group", "SampleSize",
    "Device_Brand", "Device_Model", "Device_Type", "Sampling_Rate_Hz",
    "Sleep_Measurement_Type", "Cutpoint_Type",
    "Wear_Days_Instructed", "Valid_Hours_Per_Day",
    "Primary_Analysis_Type"
]
if show_cols_mode == "Key columns":
    cols_to_show = [c for c in key_cols if c in meta_view.columns]
else:
    cols_to_show = list(meta_view.columns)

# Sort option
sort_col = st.selectbox(
    "Sort by",
    options=[c for c in ["Year", "StudyID", "Country", "Device_Brand", "Age_Group"] if c in meta_view.columns],
    index=0 if "Year" in meta_view.columns else 0
)
sort_asc = st.checkbox("Ascending", value=True)

if sort_col in meta_view.columns:
    meta_view = meta_view.sort_values(sort_col, ascending=sort_asc)

st.info(f"Showing **{len(meta_view)}** rows from metadata.")
st.dataframe(meta_view[cols_to_show], width="stretch")

# Download
st.download_button(
    "Download metadata table as CSV",
    data=meta_view.to_csv(index=False).encode("utf-8"),
    file_name="metadata_table_filtered.csv",
    mime="text/csv"
)

st.markdown("---")

# ============================================================
# BEHAVIOR ESTIMATES TABLE (LONG + OPTIONAL WIDE)
# ============================================================

st.subheader("Behavior Estimates (long format)")

col1, col2, col3 = st.columns([1.2, 1, 1])

with col1:
    # Limit to behaviors if present
    if "Behavior" in df_long.columns:
        beh_opts = sorted(df_long["Behavior"].dropna().unique().tolist())
        beh_pick = st.multiselect("Behaviors", options=beh_opts, default=beh_opts)
    else:
        beh_pick = None

with col2:
    if "Mean_Type" in df_long.columns:
        mt_opts = sorted(df_long["Mean_Type"].dropna().unique().tolist())
        mt_pick = st.multiselect("Mean type", options=mt_opts, default=mt_opts)
    else:
        mt_pick = None

with col3:
    wide_mode = st.selectbox("View", ["Long table", "Wide (A_ and G_ columns)"], index=0)

df_view = df_long.copy()

if beh_pick is not None and "Behavior" in df_view.columns:
    df_view = df_view[df_view["Behavior"].isin(beh_pick)]

if mt_pick is not None and "Mean_Type" in df_view.columns:
    df_view = df_view[df_view["Mean_Type"].isin(mt_pick)]

# Optional: merge key study info for easier checking
meta_cols_for_merge = [c for c in ["StudyID", "Year", "title", "Country", "Age_Group", "Device_Brand", "Device_Model"] if c in meta.columns]
if "StudyID" in meta_cols_for_merge and "StudyID" in df_view.columns:
    df_view = df_view.merge(meta[meta_cols_for_merge].drop_duplicates("StudyID"), on="StudyID", how="left")

# Columns to show (long)
long_cols = [c for c in [
    "StudyID", "Year", "title", "Country", "Age_Group",
    "Subgroup", "Behavior", "Mean_Type", "Minutes"
] if c in df_view.columns]

if wide_mode == "Long table":
    st.info(f"Showing **{len(df_view)}** rows of behavior estimates (long format).")
    st.dataframe(df_view[long_cols], width="stretch")

    st.download_button(
        "Download behavior estimates (long) as CSV",
        data=df_view[long_cols].to_csv(index=False).encode("utf-8"),
        file_name="behavior_estimates_long.csv",
        mime="text/csv"
    )

else:
    # Wide: 1 row per StudyID + Subgroup, columns A_* and G_*
    needed_cols = [c for c in ["StudyID", "Subgroup", "Behavior", "Mean_Type", "Minutes"] if c in df_view.columns]
    if len(needed_cols) < 5:
        st.warning("Wide view requires columns: StudyID, Subgroup, Behavior, Mean_Type, Minutes.")
    else:
        df_w = df_view[needed_cols].copy()

        wide_arith = (
            df_w[df_w["Mean_Type"] == "Arithmetic"]
            .pivot_table(index=["StudyID", "Subgroup"], columns="Behavior", values="Minutes", aggfunc="median")
            .add_prefix("A_")
            .reset_index()
        )
        wide_geo = (
            df_w[df_w["Mean_Type"] == "Geometric"]
            .pivot_table(index=["StudyID", "Subgroup"], columns="Behavior", values="Minutes", aggfunc="median")
            .add_prefix("G_")
            .reset_index()
        )

        wide_all = pd.merge(wide_arith, wide_geo, on=["StudyID", "Subgroup"], how="outer")

        # Add key metadata
        if "StudyID" in wide_all.columns:
            wide_all = wide_all.merge(meta[meta_cols_for_merge].drop_duplicates("StudyID"), on="StudyID", how="left")

        # Order columns nicely
        front = [c for c in ["StudyID", "Year", "title", "Country", "Age_Group", "Device_Brand", "Device_Model", "Subgroup"] if c in wide_all.columns]
        rest = [c for c in wide_all.columns if c not in front]
        wide_all = wide_all[front + rest]

        st.info(f"Showing **{len(wide_all)}** rows (wide format).")
        st.dataframe(wide_all, width="stretch")

        st.download_button(
            "Download behavior estimates (wide) as CSV",
            data=wide_all.to_csv(index=False).encode("utf-8"),
            file_name="behavior_estimates_wide.csv",
            mime="text/csv"
        )

st.markdown("---")

# ============================================================
# DRILL-DOWN: ONE STUDY VIEW
# ============================================================

st.subheader("Drill-down: Check one study")

# Make a nice picker
meta_picker = meta.copy()
if "title" in meta_picker.columns:
    meta_picker["__label__"] = meta_picker.apply(
        lambda r: f"{r.get('Year','')} — {str(r.get('title',''))[:90]} (StudyID: {r['StudyID']})",
        axis=1
    )
else:
    meta_picker["__label__"] = meta_picker["StudyID"].astype(str)

pick_label = st.selectbox("Select a study", options=meta_picker["__label__"].tolist())
picked = meta_picker.loc[meta_picker["__label__"] == pick_label].iloc[0]
sid = picked["StudyID"]

st.markdown(f"### Selected StudyID: `{sid}`")

# Show metadata row(s) for this study
st.write("**Metadata**")
st.dataframe(meta[meta["StudyID"] == sid], width="stretch")

# Show behavior rows for this study
st.write("**Behavior estimates (all rows)**")
df_sid = df_long[df_long["StudyID"] == sid].copy()
show_cols = [c for c in ["StudyID", "Subgroup", "Behavior", "Mean_Type", "Minutes"] if c in df_sid.columns]
if len(df_sid) == 0:
    st.warning("No behavior estimates found for this StudyID in the long dataset.")
else:
    st.dataframe(df_sid[show_cols], width="stretch")
