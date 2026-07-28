"""Premium RecruitOS home page."""
from __future__ import annotations

import streamlit as st

from models.security_context import SecurityContext
from ui.brand_components import feature_grid_html, page_header_html


def show_home(context: SecurityContext) -> None:
    context.require_valid()
    st.markdown(
        page_header_html(
            title=f"Welcome, {context.display_name.split()[0]}",
            eyebrow="Talent intelligence workspace",
            description=(
                "Move from resume volume to decision clarity with private, "
                "configuration-driven candidate screening."
            ),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(feature_grid_html(), unsafe_allow_html=True)

    result = st.session_state.get("analysis_result")
    if result:
        summary = result.get("summary", {})
        matches = result.get("match_results", [])
        shortlisted = sum(1 for item in matches if item.shortlisted)
        average = (
            sum(item.overall_match_percentage for item in matches) / len(matches)
            if matches
            else 0.0
        )
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Resumes processed", summary.get("resumes_processed", 0))
        col2.metric("Shortlisted", shortlisted)
        col3.metric("Average match", f"{average:.1f}%")
        col4.metric("Private sessions", "1 loaded")
        st.success(
            "Your latest screening session is active. Open Results or Candidate "
            "Database to continue."
        )
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Workspace", "Private")
        col2.metric("Role", context.role.replace("_", " ").title())
        col3.metric("User ID", context.login_id)
        st.info(
            "No screening session is loaded. Open Resume Screening to create your "
            "first ranked candidate list."
        )
