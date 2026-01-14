import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Results Engine", page_icon="🧠", layout="wide")

# ============================================================
# LOAD DATA (page-local)
# ============================================================
df = pd.read_csv("dashboard_clean_input (1).csv")
meta = pd.read_csv("full_metadata (1).csv")

df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

# Keep standard age groups if present
if "Age_Group" in df.columns:
    df = df[df["Age_Group"].isin(["Children", "Adolescents", "Adult"])]

# Normalize subgroup in metadata (prefer Full row per study if multiple)
if "Subgroup" in meta.columns:
    meta["Subgroup_clean"] = (
        meta["Subgroup"]
        .fillna("Full")
        .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
    )
else:
    meta["Subgroup_clean"] = "Full"

meta["is_full"] = (meta["Subgroup_clean"] == "Full").astype(int)
meta_one = (
    meta.sort_values(["StudyID", "is_full"], ascending=[True, False])
        .drop_duplicates(subset="StudyID", keep="first")
        .reset_index(drop=True)
)

# ============================================================
# HEADER
# ============================================================
st.write("## Results Engine — Method Comparison Grid 🧠")
st.caption(
    "Each cell summarizes how much reported minutes vary **across methodological choices** for a given dimension. "
    "Dot = median across choices. Thick line = IQR. Thin line = full range."
)

st.markdown("---")

# ============================================================
# CONTROLS (lightweight)
# ============================================================
behaviors = ["Sleep", "SB", "LPA", "MVPA"]

mean_type = st.radio(
    "Mean type to summarize:",
    ["Geometric", "Arithmetic"],
    horizontal=True
)

age_opts = ["All"]
if "Age_Group" in df.columns:
    age_opts += ["Children", "Adolescents", "Adult"]

age_choice = st.selectbox("Age group (optional):", age_opts)

# Pick which method dimensions to show (rows)
default_methods = [
    "Cutpoint_Type",
    "Device_Brand",
    "Device_Type",
    "Sampling_Rate_Hz",
    "Sleep_Measurement_Type",
]

available_methods = [m for m in default_methods if m in meta_one.columns]

method_rows = st.multiselect(
    "Method dimensions to compare (rows):",
    options=sorted(meta_one.columns),
    default=available_methods
)

# If user picks something that doesn't exist, guard
method_rows = [m for m in method_rows if m in meta_one.columns]

if len(method_rows) == 0:
    st.warning("Pick at least one methodological dimension.")
    st.stop()

# ============================================================
# HELPERS
# ============================================================
def _clean_minutes(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )

def summarize_choice_variation(df_long, meta_one_row, behavior, mean_type, method_col, age_choice="All"):
    """
    Produces ONE summary for a (behavior, mean_type, method_col):
      - Get one value per StudyID (median if duplicates)
      - Attach method choice per StudyID (from meta_one_row)
      - For each method choice: median across studies
      - Summarize distribution of choice-medians (min/q25/median/q75/max)
    """
    if method_col not in meta_one_row.columns:
        return None

    d = df_long[(df_long["Behavior"] == behavior) & (df_long["Mean_Type"] == mean_type)].copy()
    if d.empty:
        return None

    if age_choice != "All" and "Age_Group" in d.columns:
        d = d[d["Age_Group"] == age_choice].copy()
        if d.empty:
            return None

    d["Minutes"] = _clean_minutes(d["Minutes"])
    d = d.dropna(subset=["StudyID", "Minutes"])
    if d.empty:
        return None

    # One value per StudyID (median protects against duplicates/subgroups)
    per_study = (
        d.groupby("StudyID", as_index=False)["Minutes"]
         .median()
         .rename(columns={"Minutes": "StudyValue"})
    )

    # Attach method choice from metadata (one row per StudyID)
    m = meta_one_row[["StudyID", method_col]].copy()
    m[method_col] = m[method_col].fillna("NR").astype(str)

    merged = per_study.merge(m, on="StudyID", how="left")
    merged[method_col] = merged[method_col].fillna("NR").astype(str)

    # For each choice: median across studies
    by_choice = (
        merged.groupby(method_col)["StudyValue"]
              .agg(choice_median="median", n_studies="count")
              .reset_index()
              .rename(columns={method_col: "Choice"})
              .sort_values("choice_median", ascending=True)
              .reset_index(drop=True)
    )

    vals = by_choice["choice_median"].dropna().values
    if len(vals) == 0:
        return None

    # Compute quantiles
    q25 = float(np.percentile(vals, 25))
    q75 = float(np.percentile(vals, 75))
    med = float(np.median(vals))

    return {
        "n_choices": int(by_choice["Choice"].nunique()),
        "min": float(np.min(vals)),
        "q25": q25,
        "median": med,
        "q75": q75,
        "max": float(np.max(vals)),
        "by_choice": by_choice
    }

def plot_cell(summary, title, x_label="Minutes/day"):
    """
    One-line “forest-ish” cell:
      - thin line = min -> max
      - thick line = q25 -> q75
      - dot = median
    """
    fig = go.Figure()

    if summary is None:
        fig.add_annotation(
            text="No data",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False
        )
        fig.update_layout(
            title=title,
            height=220,
            margin=dict(l=10, r=10, t=45, b=35),
            xaxis_title=x_label,
            yaxis_visible=False
        )
        return fig

    # thin range
    fig.add_shape(
        type="line",
        x0=summary["min"], x1=summary["max"],
        y0=0, y1=0,
        xref="x", yref="y",
        line=dict(width=3),
        opacity=0.25
    )

    # thick IQR
    fig.add_shape(
        type="line",
        x0=summary["q25"], x1=summary["q75"],
        y0=0, y1=0,
        xref="x", yref="y",
        line=dict(width=8),
        opacity=0.35
    )

    # median dot
    fig.add_trace(
        go.Scatter(
            x=[summary["median"]],
            y=[0],
            mode="markers",
            marker=dict(size=12),
            showlegend=False,
            hovertemplate=(
                f"Median across choices: {summary['median']:.1f}<br>"
                f"IQR: [{summary['q25']:.1f}, {summary['q75']:.1f}]<br>"
                f"Range: [{summary['min']:.1f}, {summary['max']:.1f}]<br>"
                f"n choices: {summary['n_choices']}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=title,
        height=220,
        margin=dict(l=10, r=10, t=45, b=35),
        xaxis_title=x_label,
        yaxis_visible=False,
        yaxis_range=[-1, 1]
    )

    return fig

# ============================================================
# BUILD GRID
# ============================================================
details_grid = {}  # details_grid[method_col][behavior] = summary dict

for method_col in method_rows:
    st.write(f"### {method_col} — {mean_type} estimates")
    cols = st.columns(4)
    details_grid[method_col] = {}

    for i, b in enumerate(behaviors):
        summ = summarize_choice_variation(df, meta_one, b, mean_type, method_col, age_choice=age_choice)
        details_grid[method_col][b] = summ

        fig = plot_cell(
            summ,
            title=b,
            x_label="Minutes/day"
        )
        cols[i].plotly_chart(fig, width="stretch")

    st.markdown("---")

# ============================================================
# OPTIONAL DETAILS TABLES
# ============================================================
with st.expander("Show details (choice medians used inside each cell)"):
    st.write(
        "For each method dimension and behavior, this table shows the **median minutes within each choice** "
        "(e.g., each cutpoint type). The cell summaries are computed from these choice-medians."
    )

    for method_col in details_grid:
        st.write(f"#### {method_col}")
        for b in behaviors:
            s = details_grid[method_col].get(b)
            if s is None:
                st.write(f"**{b}**: No data")
            else:
                st.write(f"**{b}** (n choices = {s['n_choices']})")
                st.dataframe(s["by_choice"], width="stretch")
