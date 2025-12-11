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
# NEW IMPROVED PLOT 2 — INDIVIDUAL STUDY POINTS WITH FACETS
# ======================================================================

st.subheader("Individual Study Estimates by Behavior")

selected_behavior = st.selectbox(
    "Choose a behavior to visualize",
    sorted(df_f["Behavior"].dropna().unique())
)

df_beh = df_f[df_f["Behavior"] == selected_behavior].copy()

if df_beh.empty:
    st.warning("No data for this behavior with current filters.")
else:
    # Make row index for visual spacing
    df_beh = df_beh.sort_values("Minutes").reset_index(drop=True)
    df_beh["row_id"] = df_beh.index.astype(str)

    # Compute arithmetic and geometric means per age group
    mean_df = (
        df_beh.groupby(["Age_Group", "Mean_Type"], observed=False)["Minutes"]
        .mean()
        .reset_index()
    )

    # Force all three facets to exist even if empty
    df_beh["Age_Group"] = pd.Categorical(
        df_beh["Age_Group"],
        categories=["Children", "Adolescents", "Adult"],
        ordered=True
    )
    mean_df["Age_Group"] = pd.Categorical(
        mean_df["Age_Group"],
        categories=["Children", "Adolescents", "Adult"],
        ordered=True
    )

    shape_map = {"Arithmetic": "circle", "Geometric": "triangle-up"}
    color_map = {"Arithmetic": "#2E86C1", "Geometric": "#C0392B"}

    # --------------------------
    # BUILD SCATTER WITH FACETS
    # --------------------------
    fig = px.scatter(
        df_beh,
        x="Minutes",
        y="row_id",
        color="Mean_Type",
        symbol="Mean_Type",
        hover_name="StudyID_display",
        hover_data=["StudyID_display", "Minutes"],
        color_discrete_map=color_map,
        symbol_map=shape_map,
        facet_col="Age_Group",
        facet_col_wrap=3,
        height=650,
        title=f"{selected_behavior}: Study-Level Arithmetic & Geometric Estimates",
    )

    # Make facet backgrounds distinct
    fig.for_each_xaxis(lambda a: a.update(showgrid=True, gridcolor="#CCCCCC"))
    fig.for_each_yaxis(lambda a: a.update(showgrid=False))
    fig.update_layout(plot_bgcolor="white")

    # --------------------------
    # ADD MEAN LINES PER FACET
    # --------------------------
    for _, r in mean_df.iterrows():

        x_mean = r["Minutes"]
        mean_type = r["Mean_Type"]
        age = r["Age_Group"]

        # Which facet this belongs to
        facet_index = ["Children", "Adolescents", "Adult"].index(age) + 1
        xref = f"x{facet_index}" if facet_index > 1 else "x"

        line_color = color_map[mean_type]

        fig.add_shape(
            type="line",
            x0=x_mean, x1=x_mean,
            y0=0, y1=1,
            xref=xref,
            yref="paper",  # stays within facet
            line=dict(color=line_color, width=3, dash="dash"),
            opacity=0.9,
        )

    # Replace row_id ticks with StudyID labels
    fig.update_yaxes(
        ticktext=df_beh["StudyID_display"].tolist(),
        tickvals=df_beh["row_id"].tolist(),
        automargin=True,
    )

    st.plotly_chart(fig, width="stretch")

# ======================================================================
# TABLE OUTPUT — Study-Level Rows
# ======================================================================

st.subheader("Study-Level Breakdown")

if df_f.empty:
    st.warning("No rows match your selected filters.")
else:
    st.dataframe(df_f.sort_values(["StudyID", "Behavior", "Mean_Type"]))
