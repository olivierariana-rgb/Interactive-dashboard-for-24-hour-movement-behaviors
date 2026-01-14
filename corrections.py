# corrections.py
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Corrections & Feedback", page_icon="🛠️")

st.title("Corrections & Feedback")

st.caption(
    "This scoping review aims to accurately represent the methodological choices of all included studies. "
    "If you believe information related to your study has been misclassified or requires clarification, "
    "you may submit a correction request below. Requests do not automatically modify the dataset and will "
    "be reviewed by the authors."
)

st.markdown("---")

# ============================================================
# LOAD METADATA (for selecting StudyID and showing context)
# ============================================================

@st.cache_data
def load_meta():
    # Adjust filename if you renamed it
    meta = pd.read_csv("full_metadata (1).csv")
    # Make sure StudyID exists
    if "StudyID" not in meta.columns:
        raise ValueError("`StudyID` column not found in metadata CSV.")
    return meta

try:
    meta = load_meta()
except Exception as e:
    st.error(f"Could not load metadata file. Error: {e}")
    st.stop()

# Optional: try to make a nice label for study selection
def _study_label(row):
    year = row.get("Year", "")
    title = row.get("title", "")
    sid = row.get("StudyID", "")
    parts = []
    if pd.notna(year) and str(year).strip() != "":
        parts.append(str(year))
    if pd.notna(title) and str(title).strip() != "":
        parts.append(str(title)[:80] + ("..." if len(str(title)) > 80 else ""))
    parts.append(f"(StudyID: {sid})")
    return " — ".join(parts)

meta_for_picker = meta.copy()
meta_for_picker["__label__"] = meta_for_picker.apply(_study_label, axis=1)

st.subheader("Submit a correction request")

with st.form("correction_form", clear_on_submit=True):
    # Study selection
    study_choice = st.selectbox(
        "Which study is this about?",
        options=meta_for_picker["__label__"].tolist(),
    )

    # Extract StudyID from selected label
    picked_row = meta_for_picker.loc[meta_for_picker["__label__"] == study_choice].iloc[0]
    picked_studyid = picked_row["StudyID"]

    # Let them optionally specify subgroup
    subgroup = st.text_input(
        "Subgroup (optional)",
        placeholder="e.g., Boys, Girls, Full sample, etc."
    )

    # What field is wrong?
    common_fields = [
        "Device_Brand",
        "Device_Model",
        "Device_Type",
        "Sampling_Rate_Hz",
        "Sleep_Measurement_Type",
        "Cutpoint_Type",
        "Wear_Days_Instructed",
        "Valid_Hours_Per_Day",
        "Primary_Analysis_Type",
        "Other / Not sure"
    ]

    field = st.selectbox("What variable/field needs correction?", common_fields)

    # Current vs proposed
    current_value = st.text_input("What is currently shown (as displayed in the app)?", placeholder="Type what you see")
    proposed_value = st.text_input("What should it be instead?", placeholder="Type the corrected value")

    # Evidence / justification
    evidence = st.text_area(
        "Evidence / justification (recommended)",
        placeholder="Example: 'Methods section p.4: device was ActiGraph GT3X+. Sampling was 30 Hz.'"
    )

    # Optional link
    link = st.text_input(
        "Link to supporting source (optional)",
        placeholder="DOI link, publisher page, OSF, supplementary material link, etc."
    )

    # Contact (optional)
    contact = st.text_input(
        "Your email (optional)",
        placeholder="So we can follow up if needed"
    )

    # Optional file upload (PDF screenshot or notes)
    attachment = st.file_uploader(
        "Optional attachment (PDF/image) to support the correction",
        type=["pdf", "png", "jpg", "jpeg"]
    )

    # Consent checkbox
    consent = st.checkbox(
        "I understand this submission is a request and will be reviewed before any changes are made."
    )

    submitted = st.form_submit_button("Submit correction request")

if submitted:
    if not consent:
        st.warning("Please check the consent box before submitting.")
        st.stop()

    # Build the submission record
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "StudyID": str(picked_studyid),
        "Subgroup": subgroup.strip(),
        "Field": field,
        "Current_Value": current_value.strip(),
        "Proposed_Value": proposed_value.strip(),
        "Evidence": evidence.strip(),
        "Link": link.strip(),
        "Contact_Email": contact.strip(),
    }

    # Save attachment name only (file itself not persisted unless you implement storage)
    if attachment is not None:
        record["Attachment_Filename"] = attachment.name
        record["Attachment_Type"] = attachment.type
    else:
        record["Attachment_Filename"] = ""
        record["Attachment_Type"] = ""

    # ============================================================
    # STORAGE OPTION (LOCAL CSV)
    # ============================================================
    # This will work locally. On Streamlit Community Cloud, the file system is ephemeral,
    # so it may reset. This is still useful for testing.
    out_file = "correction_requests.csv"

    try:
        # Append safely
        try:
            existing = pd.read_csv(out_file)
            updated = pd.concat([existing, pd.DataFrame([record])], ignore_index=True)
        except FileNotFoundError:
            updated = pd.DataFrame([record])

        updated.to_csv(out_file, index=False)
        st.success("✅ Submitted! Thank you — your request has been recorded for review.")
        st.info("Note: This page does not automatically change the dataset. The review team will verify the request.")
    except Exception as e:
        st.error(
            "Your request could not be saved automatically. "
            "Please copy your request below and send it to the project team."
        )
        st.code(record)
        st.error(f"Error details: {e}")

st.markdown("---")

# ============================================================
# OPTIONAL: SHOW A SMALL 'HOW WE HANDLE REQUESTS' BOX
# ============================================================

with st.expander("How correction requests are handled"):
    st.write(
        "1) We verify the request against the original publication and supplementary materials.\n"
        "2) If a correction is confirmed, we update the extraction and document the change.\n"
        "3) If clarification is needed, we may contact you (if you provided an email).\n"
        "4) Confirmed corrections may appear in a future dataset release / app update."
    )

st.markdown("---")

# ============================================================
# OPTIONAL: ADMIN VIEW (HIDDEN)
# ============================================================
# You can set an environment variable ADMIN_PASSWORD in Streamlit secrets
# and access submissions inside the app. Leave it off for public releases.

st.subheader("Project team (optional)")

admin_pw = st.text_input("Admin password (optional)", type="password")
if admin_pw:
    secret_pw = None
    try:
        # Streamlit Cloud: store in Secrets as ADMIN_PASSWORD
        secret_pw = st.secrets.get("ADMIN_PASSWORD", None)
    except Exception:
        secret_pw = None

    if secret_pw is not None and admin_pw == secret_pw:
        st.success("Admin unlocked.")
        try:
            submissions = pd.read_csv("correction_requests.csv")
            st.dataframe(submissions, width="stretch")
        except Exception as e:
            st.warning("No submissions file found yet, or could not load it.")
            st.caption(str(e))
    else:
        st.error("Incorrect password (or no ADMIN_PASSWORD configured).")
