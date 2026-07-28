"""RecruitOS Streamlit application entry point."""
from __future__ import annotations

import streamlit as st

from config.settings import VERSION
from services.authorization_service import AuthorizationService
from ui.admin_users import show_user_administration
from ui.authentication import (
    get_authenticated_context,
    show_authenticated_user,
    show_authentication,
    show_forced_password_change,
    show_sidebar_footer,
)
from ui.brand_components import page_header_html, sidebar_brand_html
from ui.candidate_database import show_candidate_database
from ui.configuration_management import show_configuration_management
from ui.home import show_home
from ui.navigation import apply_queued_page, render_workflow_navigation
from ui.results import show as show_results
from ui.resume_screening import show_resume_screening
from ui.theme import apply_alten_theme

st.set_page_config(
    page_title="RecruitOS | ALTEN",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_alten_theme("dark" if st.session_state.get("dark_mode") else "light")

security_context = get_authenticated_context()
if security_context is None:
    show_authentication()
    st.stop()

if security_context.must_change_password:
    show_forced_password_change(security_context)
    st.stop()

pages = AuthorizationService.pages_for_context(security_context)
if not pages:
    st.error("Your RecruitOS role has no active page permission.")
    st.stop()

apply_queued_page(pages)
if "page" not in st.session_state or st.session_state["page"] not in pages:
    st.session_state["page"] = pages[0]

st.sidebar.markdown(sidebar_brand_html(), unsafe_allow_html=True)
show_authenticated_user(security_context)
st.sidebar.markdown("---")
st.sidebar.radio("Navigation", pages, key="page", label_visibility="collapsed")
st.sidebar.caption(f"RecruitOS {VERSION} · Private workspace")
show_sidebar_footer()

page = st.session_state["page"]
if page == "Home":
    show_home(security_context)
elif page == "Resume Screening":
    show_resume_screening(security_context)
elif page == "Results":
    show_results(security_context)
elif page == "Candidate Database":
    show_candidate_database(security_context)
elif page == "Administration":
    show_user_administration(security_context)
elif page == "Configuration":
    show_configuration_management(security_context)
elif page == "Shared Records":
    st.markdown(
        page_header_html(
            title="Shared records",
            eyebrow="Reader workspace",
            description=(
                "Only projects explicitly shared with this account will appear here. "
                "Controlled sharing is delivered in Sprint 5.7.1D."
            ),
        ),
        unsafe_allow_html=True,
    )
    st.info("No shared record is available yet.")
else:
    st.error("The selected page is not available.")

render_workflow_navigation(
    page,
    pages,
    has_results=bool(st.session_state.get("analysis_result")),
)
