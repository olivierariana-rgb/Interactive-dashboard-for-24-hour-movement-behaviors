import streamlit as st
import pandas as pd

# ---------------------------
# Helper: readable filter summary
# ---------------------------
def summarize_filter(label, selected, all_options):
    selected = list(selected) if selected is not None else []
    all_options = list(all_options) if all_options is not None else []

    if len(selected) == 0:
        return f"{label}: none"

    if set(map(str, selected)) == set(map(str, all_options)):
        return f"{label}: all"

    return f"{label}: {', '.join(map(str, selected))}"


# ---------------------------
# Helper: sidebar multiselect with "all" default
# ---------------------------
def auto_multiselect(df, label, column):
    options = sorted(df[column].dropna().unique())
    return st.sidebar.multiselect(label, options=options, default=options)


# ---------------------------
# Load data (cached)
# ---------------------------
@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv("dashboard_clean_input (1).csv")
    meta = pd.read_csv("full_metadata (1).csv")

    # numeric
    df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

    # keep only known age groups
    df = df[df["Age_Group"].isin(["Children", "Adolescents", "Adult"])].copy()

    df["Age_Group"] = pd.Categorical(
        df["Age_Group"],
        categories=["Children", "Adolescents", "Adult"],
        ordered=True
    )

    return df, meta


# ---------------------------
# Apply sidebar filters + subgroup mode
# Returns df_f plus a dict with the selected filter values
# ---------------------------
def apply_filters(df):
    st.sidebar.header("Filters")

    age_filter     = auto_multiselect(df, "Age Group", "Age_Group")
    brand_filter   = auto_multiselect(df, "Device Brand", "Device_Brand")
    type_filter    = auto_multiselect(df, "Device Type", "Device_Type")
    country_filter = auto_multiselect(df, "Country", "Country")
    rate_filter    = auto_multiselect(df, "Sampling Rate (Hz)", "Sampling_Rate_Hz")
    sleep_filter   = auto_multiselect(df, "Sleep Measurement Type", "Sleep_Measurement_Type")

    # --- subgroup cleaning ---
    df2 = df.copy()
    df2["Subgroup_clean"] = (
        df2["Subgroup"]
        .fillna("Full")
        .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
    )

    subgroups_available = sorted([s for s in df2["Subgroup_clean"].unique() if s != "Full"])

    st.sidebar.markdown("### Subgroup Selection")
    subgroup_mode = st.sidebar.radio(
        "Choose subgroup filtering mode:",
        ["Full sample only", "All subgroups", "Specific subgroups"]
    )

    # --- apply base filters ---
    df_f = df2.copy()
    if age_filter:     df_f = df_f[df_f["Age_Group"].isin(age_filter)]
    if brand_filter:   df_f = df_f[df_f["Device_Brand"].isin(brand_filter)]
    if type_filter:    df_f = df_f[df_f["Device_Type"].isin(type_filter)]
    if country_filter: df_f = df_f[df_f["Country"].isin(country_filter)]
    if rate_filter:    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(rate_filter)]
    if sleep_filter:   df_f = df_f[df_f["Sleep_Measurement_Type"].isin(sleep_filter)]

    # --- apply subgroup mode ---
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

    selections = {
        "age_filter": age_filter,
        "brand_filter": brand_filter,
        "type_filter": type_filter,
        "country_filter": country_filter,
        "rate_filter": rate_filter,
        "sleep_filter": sleep_filter,
        "subgroup_mode": subgroup_mode
    }

    return df_f, selections
