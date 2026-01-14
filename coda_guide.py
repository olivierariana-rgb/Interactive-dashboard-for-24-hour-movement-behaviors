import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="CoDA Guide",
    page_icon="📘",
    layout="wide"
)

# ============================================================
# LOAD + PREP METADATA (ONE ROW PER STUDY, PREFER FULL)
# ============================================================

meta = pd.read_csv("full_metadata (1).csv", encoding="latin1")

# Optional: keep only studies you marked for the app
if "Include_in_app" in meta.columns:
    meta["Include_in_app"] = (
        meta["Include_in_app"].fillna("NO").astype(str).str.strip().str.upper()
    )
    meta = meta[meta["Include_in_app"] == "YES"].copy()

# Normalize subgroup + prefer Full
meta["Subgroup_clean"] = (
    meta.get("Subgroup")
        .fillna("Full")
        .replace({"": "Full", "full": "Full", "FULL": "Full", "NA": "Full"})
)

meta["is_full"] = (meta["Subgroup_clean"] == "Full").astype(int)

meta_base = (
    meta.sort_values(["StudyID", "is_full"], ascending=[True, False])
        .drop_duplicates(subset="StudyID", keep="first")
        .reset_index(drop=True)
)

n_total = meta_base["StudyID"].nunique() if "StudyID" in meta_base.columns else len(meta_base)

# ============================================================
# HEADER
# ============================================================

st.write("# Compositional Data Analysis (CoDA) Guide 📘")
st.write(
    "This page provides a **practical, evidence-backed guide** to how "
    "Compositional Data Analysis (CoDA) has been applied in studies of "
    "24-hour movement behaviors."
)

st.markdown(
    "Rather than presenting CoDA as a purely theoretical framework, "
    "**each step is grounded in what researchers actually did** in the studies "
    "included in this scoping review."
)

st.markdown("---")

# ------------------------------------------------------------
# HOW TO READ THIS GUIDE
# ------------------------------------------------------------
st.write("## How to use this guide")
st.write(
    "- Each section corresponds to a **key methodological decision** in CoDA.\n"
    "- First, we explain **what the step is and why it matters**.\n"
    "- Then, we show **how it was handled across studies** included in the review.\n"
    "- Tables and summaries are populated directly from the scoping review extraction.\n"
)

st.info(
    "🧭 This guide is intended for researchers, reviewers, and students "
    "who want to understand *both* best practices *and* real-world variability."
)

st.markdown("---")

# Small context badge
st.write(f"📊 **Studies available in metadata for this guide:** {n_total}")

# Helper for quick value-count tables
def value_counts_table(df, col, label=None):
    if col not in df.columns:
        st.warning(f"Column not found: `{col}`")
        return None

    s = df[col].copy()

    # Treat blanks as missing
    s = s.replace("", pd.NA)

    # Show NR explicitly where relevant
    s = s.fillna("NR").astype(str).str.strip()

    vc = s.value_counts(dropna=False).reset_index()
    vc.columns = [label or col, "n_studies"]
    vc["percent"] = (100 * vc["n_studies"] / vc["n_studies"].sum()).round(1)

    return vc

# ============================================================
# STEP 1 — DEFINING THE COMPOSITION
# ============================================================

st.write("## Step 1 — Defining the 24-hour composition")

st.write(
    "The first step in CoDA is defining **which behaviors make up the composition**. "
    "In 24-hour movement research, this typically includes Sleep, Sedentary Behavior (SB), "
    "Light Physical Activity (LPA), and Moderate-to-Vigorous Physical Activity (MVPA)."
)

st.write(
    "Some studies include **additional parts** (e.g., naps, screen time, other behaviors), "
    "which changes the dimensionality of the composition and downstream interpretation."
)

st.markdown("### What we observed in the literature")
st.caption("Summary pulled from extracted metadata fields related to CoDA parts.")

# ---- summary metrics (if available) ----
c1, c2, c3 = st.columns(3)

if "CODA_Parts_Number" in meta_base.columns:
    c1.metric(
        "Median number of CoDA parts",
        int(pd.to_numeric(meta_base["CODA_Parts_Number"], errors="coerce").median(skipna=True))
        if pd.to_numeric(meta_base["CODA_Parts_Number"], errors="coerce").notna().any()
        else "NR"
    )
else:
    c1.metric("Median number of CoDA parts", "NR")

if "CoDA_Additional_Parts_Number" in meta_base.columns:
    add_parts = pd.to_numeric(meta_base["CoDA_Additional_Parts_Number"], errors="coerce")
    c2.metric("Studies reporting additional parts", int(add_parts.notna().sum()))
else:
    c2.metric("Studies reporting additional parts", "NR")

if "CODA_Parts" in meta_base.columns:
    reported_parts = meta_base["CODA_Parts"].replace("", pd.NA).notna().sum()
    c3.metric("Studies listing CoDA parts", int(reported_parts))
else:
    c3.metric("Studies listing CoDA parts", "NR")

with st.expander("📊 View study-level definitions (from metadata)"):
    cols_to_show = [c for c in [
        "StudyID", "Year", "Age_Group",
        "CoDA_Models_Amount",
        "CODA_Parts_Number",
        "CODA_Parts",
        "CoDA_Additional_Parts_Number",
        "CoDA_Additional_Parts_Number2",
        "Extra_Behav_Name"
    ] if c in meta_base.columns]

    if len(cols_to_show) == 0:
        st.info("No CoDA composition fields found in metadata yet.")
    else:
        st.dataframe(meta_base[cols_to_show], width="stretch")

st.markdown("---")

# ============================================================
# STEP 2 — CLOSING THE DATA TO 24 HOURS
# ============================================================

st.write("## Step 2 — Closing the data to a 24-hour total")

st.write(
    "CoDA requires that all components sum to a constant (typically 24 hours or 1). "
    "This process is known as **closure**."
)

st.write(
    "However, studies vary in how explicitly this step is described. "
    "Some normalize raw minutes, others work with proportions, "
    "and some do not clearly report the closure method at all."
)

st.markdown("### What we observed in the literature")
st.caption("Pulled from closure-related metadata fields.")

# Closure summary table
closure_col = "Closure_Method" if "Closure_Method" in meta_base.columns else None
if closure_col is None:
    st.info("No `Closure_Method` column found yet in metadata.")
else:
    closure_tbl = value_counts_table(meta_base, closure_col, label="Closure method")
    st.dataframe(closure_tbl, width="stretch")

with st.expander("📊 Closure details by study (from metadata)"):
    cols_to_show = [c for c in [
        "StudyID", "Year", "Age_Group",
        "Data_Closure_24hr_Sum",
        "Closure_Method"
    ] if c in meta_base.columns]

    if len(cols_to_show) == 0:
        st.info("No closure fields found in metadata yet.")
    else:
        st.dataframe(meta_base[cols_to_show], width="stretch")

st.markdown("---")

# ============================================================
# STEP 3 — ZERO HANDLING
# ============================================================

st.write("## Step 3 — Handling zero values")

st.write(
    "Zero values pose a major challenge in CoDA because log-ratio transformations "
    "are undefined when zeros are present."
)

st.write(
    "Studies vary widely in how they address this issue, including:\n"
    "- Adding small constants\n"
    "- Using model-based zero replacement\n"
    "- Excluding participants with zeros\n"
    "- Not reporting zero handling at all"
)

st.warning(
    "⚠️ Zero handling decisions can substantially affect results and should be reported transparently."
)

st.markdown("### What we observed in the literature")
st.caption("Pulled from zero-handling metadata fields.")

# Zero handling summary
if "Zero_Handling_Reported_Yes_No" in meta_base.columns:
    zrep = value_counts_table(meta_base, "Zero_Handling_Reported_Yes_No", label="Zero handling reported?")
    st.dataframe(zrep, width="stretch")
else:
    st.info("No `Zero_Handling_Reported_Yes_No` field found yet in metadata.")

if "Zero_Handling_Method" in meta_base.columns:
    zmet = value_counts_table(meta_base, "Zero_Handling_Method", label="Zero handling method")
    st.dataframe(zmet, width="stretch")

with st.expander("📊 Zero handling strategies across studies (from metadata)"):
    cols_to_show = [c for c in [
        "StudyID", "Year", "Age_Group",
        "Zero_Handling_Reported_Yes_No",
        "Zero_Handling_Method",
        "Zero_Replacement_Value_in_secs"
    ] if c in meta_base.columns]

    if len(cols_to_show) == 0:
        st.info("No zero handling fields found in metadata yet.")
    else:
        st.dataframe(meta_base[cols_to_show], width="stretch")

st.markdown("---")

# ============================================================
# STEP 4 — ILR TRANSFORMATION
# ============================================================

st.write("## Step 4 — Log-ratio transformation (ILR)")

st.write(
    "Most studies apply an **Isometric Log-Ratio (ILR)** transformation "
    "before modeling compositional data."
)

st.write(
    "However, reporting practices vary, including:\n"
    "- Explicit description of ILR coordinates\n"
    "- Reference to supplementary materials\n"
    "- Omission of transformation details"
)

st.markdown("### What we observed in the literature")
st.caption("Pulled from ILR / transformation metadata fields.")

if "ILR_Transformation_Type" in meta_base.columns:
    ilr_tbl = value_counts_table(meta_base, "ILR_Transformation_Type", label="ILR transformation type")
    st.dataframe(ilr_tbl, width="stretch")
else:
    st.info("No `ILR_Transformation_Type` field found yet in metadata.")

if "Transformation_Details" in meta_base.columns:
    with st.expander("📄 Transformation details (free text, by study)"):
        cols_to_show = [c for c in ["StudyID", "Year", "Transformation_Details"] if c in meta_base.columns]
        if len(cols_to_show) == 0:
            st.info("No transformation detail fields found.")
        else:
            st.dataframe(meta_base[cols_to_show], width="stretch")

if "CoDA_Packages_Used" in meta_base.columns:
    pkg_tbl = value_counts_table(meta_base, "CoDA_Packages_Used", label="CoDA packages used")
    with st.expander("📦 Packages used (summary)"):
        st.dataframe(pkg_tbl, width="stretch")

st.markdown("---")

# ============================================================
# STEP 5 — MODELING & INTERPRETATION
# ============================================================

st.write("## Step 5 — Modeling and interpretation")

st.write(
    "After transformation, compositional variables are typically entered into "
    "regression models to examine associations with health outcomes."
)

st.write(
    "Key sources of heterogeneity include:\n"
    "- Primary analysis type\n"
    "- Outcome definitions\n"
    "- Covariate adjustment strategies\n"
    "- Use of isotemporal substitution"
)

st.markdown("### What we observed in the literature")
st.caption("Pulled from modeling-related metadata fields.")

# Primary analysis type
if "Primary_Analysis_Type" in meta_base.columns:
    pa_tbl = value_counts_table(meta_base, "Primary_Analysis_Type", label="Primary analysis type")
    st.dataframe(pa_tbl, width="stretch")
else:
    st.info("No `Primary_Analysis_Type` field found yet in metadata.")

# Isotemporal / reallocation
if "Compositional_Isotemporal_Substitution_Applied_Yes_No" in meta_base.columns:
    iso_tbl = value_counts_table(
        meta_base,
        "Compositional_Isotemporal_Substitution_Applied_Yes_No",
        label="Isotemporal substitution applied?"
    )
    st.dataframe(iso_tbl, width="stretch")

with st.expander("📊 Modeling choices across studies (from metadata)"):
    cols_to_show = [c for c in [
        "StudyID", "Year", "Age_Group",
        "Primary_Analysis_Type",
        "Independent_Variable",
        "Outcome_Variable",
        "Covariates",
        "Compositional_Isotemporal_Substitution_Applied_Yes_No",
        "Time_Reallocation_Increment_minutes",
        "Stratified_Analyses",
        "Sensitivity_Analyses",
        "Bootstrap"
    ] if c in meta_base.columns]

    if len(cols_to_show) == 0:
        st.info("No modeling fields found in metadata yet.")
    else:
        st.dataframe(meta_base[cols_to_show], width="stretch")

st.markdown("---")

# ============================================================
# FINAL NOTES
# ============================================================

st.write("## Final notes")

st.write(
    "- This guide will evolve as the scoping review progresses.\n"
    "- All summaries are **empirically derived** from included studies.\n"
    "- The goal is transparency, not prescription — highlighting both consensus and variability."
)

st.info(
    "✨ This page is designed to bridge **methodological theory** and **research practice**."
)
