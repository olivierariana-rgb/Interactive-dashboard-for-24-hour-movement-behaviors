import streamlit as st
import pandas as pd

def summarize_filter(label, selected, all_options):
    selected = list(selected) if selected is not None else []
    all_options = list(all_options) if all_options is not None else []

    if len(selected) == 0:
        return f"{label}: none"
    if set(map(str, selected)) == set(map(str, all_options)):
        return f"{label}: all"
    return f"{label}: {', '.join(map(str, selected))}"

@st.cache_data
def load_data():
    df = pd.read_csv("dashboard_clean_input.csv")
    meta = pd.read_csv("full_metadata.csv")

    df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")
    df = df[df["Age_Group"].isin(["Children", "Adolescents", "Adult"])]

    df["Age_Group"] = pd.Categorical(
        df["Age_Group"],
        categories=["Children", "Adolescents", "Adult"],
        ordered=True
    )

    df["Subgroup_clean"] = (
        df["Subgroup"]
        .fillna("Full")
        .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
    )
    return df, meta

def apply_sidebar_filters(df):
    st.sidebar.header("Filters")

    def auto_multiselect(label, column):
        options = sorted(df[column].dropna().unique())
        return st.sidebar.multiselect(label, options=options, default=options)

    age_filter     = auto_multiselect("Age Group", "Age_Group")
    brand_filter   = auto_multiselect("Device Brand", "Device_Brand")
    type_filter    = auto_multiselect("Device Type", "Device_Type")
    country_filter = auto_multiselect("Country", "Country")
    rate_filter    = auto_multiselect("Sampling Rate (Hz)", "Sampling_Rate_Hz")
    sleep_filter   = auto_multiselect("Sleep Measurement Type", "Sleep_Measurement_Type")

    st.sidebar.markdown("### Subgroup Selection")

    subgroups_available = sorted([s for s in df["Subgroup_clean"].unique() if s != "Full"])
    subgroup_mode = st.sidebar.radio(
        "Choose subgroup filtering mode:",
        ["Full sample only", "All subgroups", "Specific subgroups"]
    )

    df_f = df.copy()

    if age_filter:     df_f = df_f[df_f["Age_Group"].isin(age_filter)]
    if brand_filter:   df_f = df_f[df_f["Device_Brand"].isin(brand_filter)]
    if type_filter:    df_f = df_f[df_f["Device_Type"].isin(type_filter)]
    if country_filter: df_f = df_f[df_f["Country"].isin(country_filter)]
    if rate_filter:    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(rate_filter)]
    if sleep_filter:   df_f = df_f[df_f["Sleep_Measurement_Type"].isin(sleep_filter)]

    if subgroup_mode == "Full sample only":
        df_f = df_f[df_f["Subgroup_clean"] == "Full"]
    elif subgroup_mode == "Specific subgroups":
        chosen_groups = st.sidebar.multiselect("Choose one or more subgroups:", options=subgroups_available)
        if chosen_groups:
            df_f = df_f[df_f["Subgroup_clean"].isin(chosen_groups)]
        else:
            st.sidebar.warning("Select at least one subgroup or switch mode.")

    filter_summaries = [
        summarize_filter("Age group", age_filter, df["Age_Group"].unique()),
        summarize_filter("Device brand", brand_filter, df["Device_Brand"].unique()),
        summarize_filter("Device type", type_filter, df["Device_Type"].unique()),
        summarize_filter("Country", country_filter, df["Country"].unique()),
        summarize_filter("Sampling rate", rate_filter, df["Sampling_Rate_Hz"].unique()),
        summarize_filter("Sleep measurement", sleep_filter, df["Sleep_Measurement_Type"].unique()),
        f"Subgroup mode: {subgroup_mode}",
    ]

    return df_f, filter_summaries
