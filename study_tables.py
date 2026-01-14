# pages/2_Study_Tables.py
import streamlit as st
import pandas as pd

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Study Tables", page_icon="📋", layout="wide")

st.markdown("# Study Tables 📋")
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
# LOAD DATA
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard_clean_input (1).csv")   # long format for plotting/tables
    meta = pd.read_csv("full_metadata (1).csv")         # one row per study/subgroup (metadata)
    return df, meta


df, meta = load_data()

# Clean numeric
if "Minutes" in df.columns:
    df["Minutes"] = clean_minutes(df["Minutes"])

# Keep only known age groups
df = df[df["Age_Group"].isin(["Children", "Adolescents", "Adult"])].copy()
df["Age_Group"] = pd.Categorical(df["Age_Group"], categories=["Children", "Adolescents", "Adult"], ordered=True)

# Normalize subgroup
df["Subgroup_clean"] = (
    df["Subgroup"]
    .fillna("Full")
    .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

# ============================================================
# SIDEBAR FILTERS (same style as Explorer)
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
# SUMMARY
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
# STUDY-LEVEL BREAKDOWN (1 row per StudyID)
# ============================================================
st.subheader("Study-Level Breakdown (1 row per study)")

if "StudyID" not in df_f.columns:
    st.warning("StudyID column not found in filtered dataset.")
    st.stop()

study_ids = df_f["StudyID"].dropna().unique()

if len(study_ids) == 0:
    st.warning("No studies match the current filters.")
else:
    st.info(f"Showing **{len(study_ids)} unique studies** based on current filters.")

    # Filter metadata to these studies
    meta_filtered = meta[meta["StudyID"].isin(study_ids)].copy()

    # Prefer Full subgroup row if available (if Subgroup exists in meta)
    if "Subgroup" in meta_filtered.columns:
        meta_filtered["Subgroup_clean"] = (
            meta_filtered["Subgroup"]
            .fillna("Full")
            .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
        )
        meta_filtered["is_full"] = (meta_filtered["Subgroup_clean"] == "Full").astype(int)

        meta_unique = (
            meta_filtered
            .sort_values(["StudyID", "is_full"], ascending=[True, False])
            .drop_duplicates(subset="StudyID", keep="first")
            .reset_index(drop=True)
        )
    else:
        meta_unique = (
            meta_filtered
            .sort_values("StudyID")
            .drop_duplicates(subset="StudyID", keep="first")
            .reset_index(drop=True)
        )

    # Columns to display (only keep those that exist)
    metadata_cols = [
        "StudyID", "Year", "title", "Country",
        "Age_Group", "SampleSize", "Device_Brand", "Device_Type",
        "Sampling_Rate_Hz", "Sleep_Measurement_Type"
    ]
    metadata_cols = [c for c in metadata_cols if c in meta_unique.columns]

    st.write("### Study Characteristics")
    st.dataframe(meta_unique[metadata_cols], width="stretch")

st.markdown("---")

# ============================================================
# SUBGROUP SUMMARY TABLE
# ============================================================
st.subheader("Subgroups Available Per Study")

if "Subgroup" not in df_f.columns:
    st.info("No subgroup column available in this dataset.")
else:
    subgroup_table = (
        df_f.groupby("StudyID")["Subgroup"]
            .unique()
            .reset_index()
            .rename(columns={"Subgroup": "Available_Subgroups"})
    )
    st.dataframe(subgroup_table, width="stretch")

st.markdown("---")

# ============================================================
# BEHAVIOR SUMMARY TABLE (WIDE FORMAT)
# ============================================================
st.subheader("Behavior Summary (Wide Format: 1 row per Study + Subgroup)")

behaviors = ["Sleep", "SB", "LPA", "MVPA"]

if "Behavior" not in df_f.columns or "Mean_Type" not in df_f.columns:
    st.warning("Behavior and/or Mean_Type columns are missing.")
    st.stop()

df_beh4 = df_f[df_f["Behavior"].isin(behaviors)].copy()

if df_beh4.empty:
    st.warning("No behavior data available for current filters.")
else:
    # Pivot arithmetic and geometric separately
    wide_arith = (
        df_beh4[df_beh4["Mean_Type"] == "Arithmetic"]
        .pivot_table(
            index=["StudyID", "Subgroup"],
            columns="Behavior",
            values="Minutes",
            aggfunc="mean"
        )
        .add_prefix("A_")
        .reset_index()
    )

    wide_geo = (
        df_beh4[df_beh4["Mean_Type"] == "Geometric"]
        .pivot_table(
            index=["StudyID", "Subgroup"],
            columns="Behavior",
            values="Minutes",
            aggfunc="mean"
        )
        .add_prefix("G_")
        .reset_index()
    )

    wide_all = pd.merge(wide_arith, wide_geo, on=["StudyID", "Subgroup"], how="outer")

    # Optional: sort if Year exists in meta
    if "Year" in meta.columns:
        wide_all = wide_all.merge(meta[["StudyID", "Year"]].drop_duplicates(), on="StudyID", how="left")
        wide_all = wide_all.sort_values(["Year", "StudyID"], na_position="last")
        # Put Year near front
        cols = ["Year"] + [c for c in wide_all.columns if c != "Year"]
        wide_all = wide_all[cols]

    st.dataframe(wide_all, width="stretch")
