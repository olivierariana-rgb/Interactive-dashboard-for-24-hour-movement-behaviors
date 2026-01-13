import streamlit as st
import pandas as pd
from utils import load_data, apply_sidebar_filters

df, meta = load_data()
df_f, _ = apply_sidebar_filters(df)

st.header("Study Tables")

study_ids = df_f["StudyID"].unique()
if len(study_ids) == 0:
    st.warning("No studies match the current filters.")
else:
    meta_filtered = meta[meta["StudyID"].isin(study_ids)].copy()
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

    st.subheader("Study Characteristics (1 row per study)")
    st.dataframe(meta_unique[metadata_cols], width="stretch")

    st.subheader("Subgroups Available Per Study")
    subgroup_table = (
        df_f.groupby("StudyID")["Subgroup"]
        .unique()
        .reset_index()
        .rename(columns={"Subgroup": "Available_Subgroups"})
    )
    st.dataframe(subgroup_table, width="stretch")
