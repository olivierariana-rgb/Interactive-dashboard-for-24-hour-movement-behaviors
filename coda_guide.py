import streamlit as st

st.set_page_config(
    page_title="CoDA Guide",
    page_icon="📘",
    layout="wide"
)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
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
    "- Tables and summaries will be populated directly from the scoping review extraction.\n"
)

st.info(
    "🧭 This guide is intended for researchers, reviewers, and students "
    "who want to understand *both* best practices *and* real-world variability."
)

st.markdown("---")

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
st.caption("This section will summarize how compositions were defined across studies.")

# Placeholder for future results
with st.expander("📊 View study-level definitions (placeholder)"):
    st.write(
        "This table will show:\n"
        "- Number of parts in the composition\n"
        "- Names of compositional parts\n"
        "- Whether additional behaviors were included\n\n"
        "_(Results will be populated from the scoping review extraction.)_"
    )

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
st.caption("This section will document how closure was handled and reported.")

with st.expander("📊 Closure methods used across studies (placeholder)"):
    st.write(
        "This section will include:\n"
        "- Whether closure was explicitly reported\n"
        "- Closure target (e.g., 1440 minutes, proportions)\n"
        "- Description of normalization steps\n\n"
        "_(Results pending integration from cleaned metadata.)_"
    )

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

with st.expander("📊 Zero handling strategies across studies (placeholder)"):
    st.write(
        "This table will show:\n"
        "- Whether zero handling was reported\n"
        "- Method used (if any)\n"
        "- Replacement values\n\n"
        "_(To be filled once CoDA-specific extraction is finalized.)_"
    )

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

with st.expander("📊 ILR reporting practices (placeholder)"):
    st.write(
        "This section will summarize:\n"
        "- ILR types used\n"
        "- Whether balances were described\n"
        "- Software/packages reported\n\n"
        "_(Results will be linked to extracted metadata.)_"
    )

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

with st.expander("📊 Modeling choices across studies (placeholder)"):
    st.write(
        "This table will later include:\n"
        "- Primary analysis types\n"
        "- Outcomes modeled\n"
        "- Covariates included\n"
        "- Whether isotemporal substitution was applied\n\n"
        "_(Pending integration from results extraction.)_"
    )

st.markdown("---")

# ============================================================
# FINAL NOTES
# ============================================================

st.write("## Final notes")

st.write(
    "- This guide will evolve as the scoping review progresses.\n"
    "- All summaries will be **empirically derived** from included studies.\n"
    "- The goal is transparency, not prescription — highlighting both consensus and variability."
)

st.info(
    "✨ This page is designed to bridge **methodological theory** and **research practice**."
)
