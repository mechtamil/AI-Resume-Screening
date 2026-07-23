import streamlit as st

from ui.home import show_home
from ui.resume_screening import show_resume_screening

st.set_page_config(
    page_title="RecruitOS",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize page
if "page" not in st.session_state:
    st.session_state.page = "Home"

# Sidebar
st.sidebar.title("🤖 RecruitOS")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Resume Screening",
        "Candidate Database",
        "Analytics",
        "Settings"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("RecruitOS Version 0.2")

# Page Routing
if page == "Home":
    show_home()

elif page == "Resume Screening":
    show_resume_screening()

elif page == "Candidate Database":
    st.title("👥 Candidate Database")
    st.info("Coming Soon")

elif page == "Analytics":
    st.title("📊 Analytics")
    st.info("Coming Soon")

elif page == "Settings":
    st.title("⚙ Settings")
    st.info("Coming Soon")