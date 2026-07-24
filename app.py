"""RecruitOS Streamlit application entry point."""
import streamlit as st

from config.settings import VERSION
from ui.home import show_home
from ui.results import show as show_results
from ui.resume_screening import show_resume_screening

st.set_page_config(page_title="RecruitOS", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

st.sidebar.title("🤖 RecruitOS")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    ["Home", "Resume Screening", "Results", "Candidate Database", "Analytics", "Settings"],
)
st.sidebar.markdown("---")
st.sidebar.info(f"RecruitOS Version {VERSION}")

if page == "Home":
    show_home()
elif page == "Resume Screening":
    show_resume_screening()
elif page == "Results":
    show_results()
elif page == "Candidate Database":
    st.title("👥 Candidate Database")
    st.info("Database UI is planned for a later milestone.")
elif page == "Analytics":
    st.title("📊 Analytics")
    st.info("Analytics is planned for a later milestone.")
else:
    st.title("⚙ Settings")
    st.info("Configuration is currently managed through Master_Data/RecruitOS_Configuration.xlsx.")
