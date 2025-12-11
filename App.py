import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# ---------------------------------------------------
# LOAD DATASET FILES
# (Must be uploaded to your Streamlit repo)
# ---------------------------------------------------
df = pd.read_csv("dashboard_clean.csv")      # Long, tidy dataset for plotting
full = pd.read_csv("FullData.csv", encoding="latin1")   # Full study metadata


# ---------------------------------------------------
# Clean & Prepare
# ---------------------------------------------------
# Ordered age groups
df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult", "Unknown"],
    ordered=True
)

# Filters in sidebar
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
    options=sorted(df["Sleep_Objective_Yes_No"].dropna().unique()),
    default=None
)

country_filter = st.sidebar.multiselect(
    "Country",
    options=sorted(df["Country"].dropna().unique()),
    default=None
)


# ---------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------
df_f = df.copy()

if len(age_filter) > 0:
    df_f = df_f[df_f["Age_Group"].isin(age_filter)]

if device_filter:
    df_f = df_f[df_f["Device_Brand"].isin(device_filter)]

if sampling_filter:
    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(sampling_filter)]

if sleep_filter:
    df_f = df_f[df_f["Sleep_Objective_Yes_No"].isin(sleep_filter)]

if country_filter:
    df_f = df_f[df_f["Country"].isin(country_filter)]


# ---------------------------------------------------
# TITLE
# ---------------------------------------------------
st.title("24-Hour Movement Composition Explorer")
st.write("Visualize arithmetic vs geometric means, and see detailed study-level information.")


# ---------------------------------------------------
# SPLIT INTO ARITHMETIC VS GEOMETRIC
# ---------------------------------------------------
arith = df_f[df_f["Mean_Type"] == "Arithmetic"]
geo = df_f[df_f["Mean_Type"] == "Geometric"]


# ---------------------------------------------------
# COMPUTE GROUP-LEVEL MEANS
# ---------------------------------------------------
def compute_means(df_in):
    if df_in.empty:
        return pd.DataFrame(columns=["Age_Group", "Behavior", "Minutes"])
    return (
        df_in.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"]
        .mean()
        .reset_index()
    )

arith_means = compute_means(arith)
geo_means = compute_means(geo)


# ---------------------------------------------------
# CLOSURE CHECK (does Mean Sleep + SB + LPA + MVPA = 1440?)
# ---------------------------------------------------
st.subheader("24-Hour Closure Check")

if "Data_Closure_24hr_Sum" in df_f.columns:
    bad_rows = df_f[df_f["Data_Closure_24hr_Sum"] != 1440]
    if not bad_rows.empty:
        st.error(f"⚠️ {len(bad_rows)} rows do NOT close to 1440 minutes.")
        st.dataframe(bad_rows[["StudyID", "Subgroup", "Data_Closure_24hr_Sum"]])
    else:
        st.success("✔ All filtered rows correctly sum to 24 hours.")
else:
    st.info("No closure variable found in dataset.")


# ---------------------------------------------------
# PLOTS (side-by-side)
# ---------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Arithmetic Means")
    if arith_means.empty:
        st.warning("No arithmetic mean data for these filters.")
    else:
        fig = px.bar(
            arith_means,
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            barmode="stack",
            orientation="h",
            title="Arithmetic Means (Minutes)",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult", "Unknown"]},
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Geometric Means")
    if geo_means.empty:
        st.warning("No geometric mean data for these filters.")
    else:
        fig = px.bar(
            geo_means,
            x="Minutes",
            y="Age_Group",
            color="Behavior",
            barmode="stack",
            orientation="h",
            title="Geometric Means (Minutes)",
            category_orders={"Age_Group": ["Children", "Adolescents", "Adult", "Unknown"]},
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------
# STUDY-LEVEL SECTION (MERGED WITH FULL METADATA)
# ---------------------------------------------------
st.subheader("Study-Level Metadata Table")

if df_f.empty:
    st.info("No studies match your filters.")
else:
    # Merge filtered dataset with full metadata
    merged = df_f.merge(full, on="StudyID", how="left")

    # Create ONE row per Study × Subgroup × Mean_Type
    study_table = merged[
        [
            "StudyID",
            "Year",
            "title",
            "Age_Group",
            "Subgroup",
            "Mean_Type",
            "Behavior",
            "Minutes",
            "Mean_Sleep_Min",
            "Mean_SB",
            "Mean_LPA",
            "Mean_MVPA",
            "Geo_Mean_Sleep",
            "Geo_Mean_SB",
            "Geo_Mean_LPA",
            "Geo_Mean_MVPA",
            "Country",
            "Device_Brand",
            "Sampling_Rate_Hz",
            "Sleep_Objective_Yes_No",
            "SampleSize",
            "Cutpoint_Type",
            "SB_Threshold",
            "LPA_Threshold",
            "MVPA_Threshold",
        ]
    ].drop_duplicates()

    st.dataframe(study_table, use_container_width=True)
