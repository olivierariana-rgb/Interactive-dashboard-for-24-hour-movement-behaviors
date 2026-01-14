# --------------------------------------------------
# SIMPLEX — Comparison mode (no Explorer filters)
# --------------------------------------------------

st.write("## Compare simplex across methodological choices")

compare_var = st.selectbox(
    "Compare by:",
    ["Device_Brand", "Device_Type", "Sampling_Rate_Hz", "Country", "Year", "Cutpoint_Type", "Sleep_Measurement_Type"]
)

# available levels
levels = meta[compare_var].dropna().astype(str).unique().tolist()
levels = sorted(levels)

selected_levels = st.multiselect(
    f"Select 2–4 {compare_var} levels to compare:",
    options=levels,
    default=levels[:2] if len(levels) >= 2 else levels
)

overlay_mode = st.checkbox("Overlay in one simplex (color by level)", value=False)

if len(selected_levels) < 2:
    st.info("Pick at least 2 levels to compare.")
    st.stop()

if len(selected_levels) > 4:
    st.warning("For readability, keep it to 2–4 levels.")
    st.stop()

# --------------------------------------------------
# Build geometric wide table (Sleep, SB, MVPA) for ALL studies
# --------------------------------------------------
beh_keep = ["Sleep", "SB", "MVPA"]

d_geo = df[df["Mean_Type"] == "Geometric"].copy()
d_geo = d_geo[d_geo["Behavior"].isin(beh_keep)].copy()

# normalize subgroup
d_geo["Subgroup_clean"] = (
    d_geo["Subgroup"].fillna("Full").replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

wide_geo = (
    d_geo.pivot_table(
        index=["StudyID", "Subgroup_clean"],
        columns="Behavior",
        values="Minutes",
        aggfunc="mean"
    )
    .reset_index()
)

wide_geo = wide_geo.merge(meta[["StudyID", compare_var]], on="StudyID", how="left")
wide_geo[compare_var] = wide_geo[compare_var].astype(str)

# Keep only selected levels
wide_geo = wide_geo[wide_geo[compare_var].isin(selected_levels)].copy()

# Drop missing simplex parts
wide_geo = wide_geo.dropna(subset=beh_keep)
if wide_geo.empty:
    st.warning("No studies available for that comparison.")
    st.stop()

# Close compositions
wide_geo["sum_minutes"] = wide_geo["Sleep"] + wide_geo["SB"] + wide_geo["MVPA"]
wide_geo = wide_geo[wide_geo["sum_minutes"] > 0].copy()

wide_geo["Sleep_cl"] = wide_geo["Sleep"] / wide_geo["sum_minutes"]
wide_geo["SB_cl"]    = wide_geo["SB"]    / wide_geo["sum_minutes"]
wide_geo["MVPA_cl"]  = wide_geo["MVPA"]  / wide_geo["sum_minutes"]

# --------------------------------------------------
# Plot
# --------------------------------------------------
if overlay_mode:
    fig = px.scatter_ternary(
        wide_geo,
        a="Sleep_cl",
        b="SB_cl",
        c="MVPA_cl",
        color=compare_var,
        hover_name="StudyID",
        hover_data=["Subgroup_clean", compare_var],
        title=f"Overlay simplex by {compare_var}"
    )
    fig.update_traces(marker=dict(size=11, opacity=0.85))
    fig.update_layout(height=720, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, width="stretch")

else:
    # Facet: one simplex per level (side-by-side)
    fig = px.scatter_ternary(
        wide_geo,
        a="Sleep_cl",
        b="SB_cl",
        c="MVPA_cl",
        facet_col=compare_var,
        facet_col_wrap=len(selected_levels),  # makes 1 row when 2–4
        hover_name="StudyID",
        hover_data=["Subgroup_clean", compare_var],
        title=f"Simplex comparison across {compare_var}"
    )
    fig.update_traces(marker=dict(size=10, opacity=0.85))

    # Make facets readable
    fig.update_layout(
        height=560,
        margin=dict(l=10, r=10, t=60, b=10)
    )

    st.plotly_chart(fig, width="stretch")

with st.expander("Show simplex data (closed proportions)"):
    st.dataframe(
        wide_geo[["StudyID", "Subgroup_clean", compare_var, "Sleep_cl", "SB_cl", "MVPA_cl"]],
        width="stretch"
    )
