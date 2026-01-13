import streamlit as st
from utils import load_data, apply_sidebar_filters

st.set_page_config(page_title="24-Hour Movement Composition Explorer", layout="wide")

df, meta = load_data()
df_f, filter_summaries = apply_sidebar_filters(df)

st.title("24-Hour Movement Composition Explorer")

st.markdown("### Current Selection Summary")
st.write(f"📊 **Number of studies meeting these criteria:** {df_f['StudyID'].nunique()}")
st.write("**Filters applied:**  \n" + " • " + "  \n • ".join(filter_summaries))

st.markdown("---")
st.write("Use the sidebar to navigate pages:")
st.write("• Explorer (plots)")
st.write("• Study Tables")
st.write("• Simplex")
st.write("• Results Engine")





