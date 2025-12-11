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
# PLOT 2 — INDIVIDUAL STUDY POINTS + MEAN MARKERS
# ======================================================================

st.subheader("Individual Study Estimates by Behavior")

# Select behavior to display
selected_behavior = st.selectbox(
    "Choose a behavior to visualize",
    sorted(df_f["Behavior"].dropna().unique())
)

df_beh = df_f[df_f["Behavior"] == selected_behavior].copy()

if df_beh.empty:
    st.warning("No data for this behavior with the current filters.")
else:

    # Sort studies by minutes for cleaner plotting
    df_beh = df_beh.sort_values("Minutes")

    # Compute mean for each Mean_Type × Age_Group
    mean_df = df_beh.groupby(["Age_Group", "Mean_Type"], observed=False)["Minutes"].mean().reset_index()

    fig = px.scatter(
        df_beh,
        x="Minutes",
        y="StudyID_display",
        color="Mean_Type",
        symbol="Mean_Type",
        title=f"{selected_behavior}: Individual Study Points with Means",
        category_orders={
            "Age_Group": ["Children", "Adolescents", "Adult"],
        },
        facet_col="Age_Group",
        facet_col_wrap=3,
        height=600
    )

    # Add mean markers
    for _, r in mean_df.iterrows():
        fig.add_shape(
            type="line",
            x0=r["Minutes"], x1=r["Minutes"],
            y0=0, y1=1,
            xref=f"x{mean_df['Age_Group'].tolist().index(r['Age_Group'])+1}",
            yref=f"paper",
            line=dict(
                dash="dot",
                width=2,
                color="red" if r["Mean_Type"] == "Arithmetic" else "blue"
            ),
        )

    fig.update_yaxes(matches=None, showticklabels=True)
    st.plotly_chart(fig, width="stretch")

# ======================================================================
# TABLE OUTPUT — Study-Level Rows
# ======================================================================

st.subheader("Study-Level Breakdown")

if df_f.empty:
    st.warning("No rows match your selected filters.")
else:
    st.dataframe(df_f.sort_values(["StudyID", "Behavior", "Mean_Type"]))
