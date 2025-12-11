import streamlit as st
import pandas as pd
import plotly.express as px

# ======================================================================
# LOAD DATA
# ======================================================================

df = pd.read_csv("dashboard_clean_input.csv")      # long format for plotting
meta = pd.read_csv("full_metadata.csv")            # full metadata if needed later

# Fix numeric types
df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

# Remove Unknown age group
df = df[df["Age_Group"].isin(["Children", "Adolescents", "Adult"])]

# Ensure age group ordering
df["Age_Group"] = pd.Categorical(
    df["Age_Group"],
    categories=["Children", "Adolescents", "Adult"],
    ordered=True
)

# ======================================================================
# SIDEBAR FILTERS
# ======================================================================

st.sidebar.header("Filters")

# All filters automatically adapt to dataset categories
def auto_multiselect(label, column):
    options = sorted(df[column].dropna().unique())
    return st.sidebar.multiselect(label, options=options, default=options)

age_filter     = auto_multiselect("Age Group", "Age_Group")
brand_filter   = auto_multiselect("Device Brand", "Device_Brand")
type_filter    = auto_multiselect("Device Type", "Device_Type")
country_filter = auto_multiselect("Country", "Country")
rate_filter    = auto_multiselect("Sampling Rate (Hz)", "Sampling_Rate_Hz")
sleep_filter   = auto_multiselect("Sleep Measurement Type", "Sleep_Measurement_Type")

# Apply filters
df_f = df.copy()
if age_filter:     df_f = df_f[df_f["Age_Group"].isin(age_filter)]
if brand_filter:   df_f = df_f[df_f["Device_Brand"].isin(brand_filter)]
if type_filter:    df_f = df_f[df_f["Device_Type"].isin(type_filter)]
if country_filter: df_f = df_f[df_f["Country"].isin(country_filter)]
if rate_filter:    df_f = df_f[df_f["Sampling_Rate_Hz"].isin(rate_filter)]
if sleep_filter:   df_f = df_f[df_f["Sleep_Measurement_Type"].isin(sleep_filter)]

# ======================================================================
# TITLE
# ======================================================================

st.title("24-Hour Movement Composition Explorer")
st.write("Compare arithmetic and geometric means across studies and visualize individual data points.")

# ======================================================================
# PLOT 1 — STACKED BAR PANELS (Arithmetic vs Geometric)
# ======================================================================

st.subheader("Arithmetic vs Geometric Means (by Age Group)")

arith = df_f[df_f["Mean_Type"] == "Arithmetic"]
geo   = df_f[df_f["Mean_Type"] == "Geometric"]

# Compute aggregated means
arith_means = (
    arith.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"].mean().reset_index()
)
geo_means = (
    geo.groupby(["Age_Group", "Behavior"], observed=False)["Minutes"].mean().reset_index()
)

col1, col2 = st.columns(2)

# ---- Arithmetic panel ----
with col1:
    st.write("**Arithmetic Means**")
    if not arith_means.empty:
        fig_a = px.bar(
            arith_means,
            x="Minutes", y="Age_Group",
            color="Behavior",
            orientation="h",
            title="Arithmetic Means",
            category_orders={"Age_Group": ["Children","Adolescents","Adult"]}
        )
        fig_a.update_layout(barmode="stack")
        st.plotly_chart(fig_a, width="stretch")
    else:
        st.info("No arithmetic data available after filtering.")

# ---- Geometric panel ----
with col2:
    st.write("**Geometric Means**")
    if not geo_means.empty:
        fig_g = px.bar(
            geo_means,
            x="Minutes", y="Age_Group",
            color="Behavior",
            orientation="h",
            title="Geometric Means",
            category_orders={"Age_Group": ["Children","Adolescents","Adult"]}
        )
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(fig_g, width="stretch")
    else:
        st.info("No geometric data available after filtering.")
# ======================================================================
# NEW FIXED SCATTER — COLLAPSE DUPLICATES & CLEAN FACETS
# ======================================================================

st.subheader("Individual Study Estimates by Behavior")

selected_behavior = st.selectbox(
    "Choose a behavior to visualize",
    sorted(df_f["Behavior"].dropna().unique())
)

df_beh = df_f[df_f["Behavior"] == selected_behavior].copy()

# Remove Unknown age group
df_beh = df_beh[df_beh["Age_Group"].isin(["Children","Adolescents","Adult"])]

if df_beh.empty:
    st.warning("No data for this behavior with current filters.")
else:

    # ---------------------------------------------------------
    # REMOVE DUPLICATES:
    df_beh = (
        df_beh
        .sort_values("Minutes")
        .drop_duplicates(subset=["StudyID","Subgroup","Behavior","Mean_Type"])
        .reset_index(drop=True)
    )

    # --------------------------
    # Order studies
    # --------------------------
    df_beh = df_beh.sort_values("Minutes", ascending=True)
    df_beh["row_id"] = df_beh.index

    # --------------------------
    # Ensure ordered facet levels
    # --------------------------
    valid_levels = ["Children","Adolescents","Adult"]
    existing_levels = [lvl for lvl in valid_levels if lvl in df_beh["Age_Group"].unique()]

    df_beh["Age_Group"] = pd.Categorical(df_beh["Age_Group"], categories=existing_levels, ordered=True)

    # Compute means
    mean_df = (
        df_beh.groupby(["Age_Group","Mean_Type"], observed=False)["Minutes"]
        .mean().reset_index()
    )
    mean_df["Age_Group"] = pd.Categorical(mean_df["Age_Group"], categories=existing_levels, ordered=True)

    # --------------------------
    # Build scatter figure
    # --------------------------
    fig2 = px.scatter(
        df_beh,
        x="Minutes",
        y="row_id",
        color="Mean_Type",
        symbol="Mean_Type",
        hover_name="StudyID_display",
        hover_data=["Minutes","Subgroup"],
        facet_col="Age_Group",
        category_orders={"Age_Group": existing_levels},
        height=900,
        color_discrete_map={"Arithmetic":"#1f77b4","Geometric":"#d62728"},
        title=f"{selected_behavior}: Study-Level Arithmetic & Geometric Estimates"
    )

    # Replace row_id ticks with study names
    fig2.update_yaxes(
        tickvals=df_beh["row_id"],
        ticktext=df_beh["StudyID_display"],
        automargin=True
    )

    # ---------------------------------------------------------
    # ADD MEAN LINES — dynamically map facets
    # ---------------------------------------------------------
    # Plotly facet columns: col index 1..N for each age group
    facet_map = {age: i+1 for i, age in enumerate(existing_levels)}

    for _, row in mean_df.iterrows():
        age = row["Age_Group"]
        mtype = row["Mean_Type"]
        xval = row["Minutes"]

        col_index = facet_map.get(age)
        if col_index is None:
            continue  # Skip if facet doesn't exist

        line_color = "#1f77b4" if mtype == "Arithmetic" else "#d62728"
        fig2.add_vline(
            x=xval,
            line_dash="dash",
            line_color=line_color,
            row=1,
            col=col_index
        )

    # ---------------------------------------------------------
    # Light gray background for each facet
    # ---------------------------------------------------------
    for i in range(1, len(existing_levels)+1):
        fig2.layout[f"xaxis{i}"]["showgrid"] = True
        fig2.layout[f"yaxis{i}"]["showgrid"] = False
        fig2.layout[f"xaxis{i}"]["domain"]  # just forces layout to compute
        fig2.update_xaxes(matches=None, row=1, col=i)

    fig2.update_layout(
        plot_bgcolor="#f7f7f7",
        paper_bgcolor="white"
    )

    # ---------------------------------------------------------
    st.plotly_chart(fig2, width="stretch")

# ======================================================================
# TABLE OUTPUT — Study-Level Rows
# ======================================================================

st.subheader("Study-Level Breakdown")

if df_f.empty:
    st.warning("No rows match your selected filters.")
else:
    st.dataframe(df_f.sort_values(["StudyID", "Behavior", "Mean_Type"]))
