"""Action-oriented RecruitOS home workspace."""
from __future__ import annotations

import streamlit as st

from models.security_context import SecurityContext
from services.authorization_service import AuthorizationService
from services.persistence_service import PersistenceService
from ui.brand_components import page_header_html, workflow_stepper_html
from ui.navigation import queue_page


def show_home(context: SecurityContext) -> None:
    """Show meaningful workspace activity and direct next-step actions."""
    context.require_valid()
    first_name = context.display_name.split()[0] if context.display_name.split() else "User"
    st.markdown(
        page_header_html(
            title=f"Welcome, {first_name}",
            eyebrow="Talent intelligence workspace",
            description=(
                "Start a screening, reopen saved candidate intelligence, or continue "
                "from your latest private session."
            ),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(workflow_stepper_html(active_step=1), unsafe_allow_html=True)

    result = st.session_state.get("analysis_result")
    allowed_pages = AuthorizationService.pages_for_context(context)
    try:
        projects = PersistenceService.list_projects(context)
    except Exception:
        projects = []

    project_count = len(projects)
    session_count = sum(int(item.get("screening_sessions", 0) or 0) for item in projects)
    candidate_count = sum(int(item.get("candidates", 0) or 0) for item in projects)
    shortlisted_count = sum(int(item.get("shortlisted", 0) or 0) for item in projects)

    st.subheader("Workspace pulse")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Projects", project_count)
    col2.metric("Screening sessions", session_count)
    col3.metric("Candidates", candidate_count)
    col4.metric("Shortlisted", shortlisted_count)

    st.subheader("Quick actions")
    action1, action2, action3 = st.columns(3)
    with action1:
        st.markdown(
            "**Start a new screening**  \nUpload a JD, optional skill list and candidate resumes."
        )
        if "Resume Screening" in allowed_pages:
            if st.button(
                "Start Resume Screening →",
                key="home_start_screening",
                type="primary",
                use_container_width=True,
            ):
                queue_page("Resume Screening")
        else:
            st.caption("Screening is not available for your role.")

    with action2:
        st.markdown(
            "**Continue candidate review**  \nReopen saved sessions and inspect candidate records."
        )
        if "Candidate Database" in allowed_pages:
            if st.button(
                "Open Candidate Database →",
                key="home_open_database",
                use_container_width=True,
            ):
                queue_page("Candidate Database")
        else:
            st.caption("Candidate records are not available for your role.")

    with action3:
        st.markdown(
            "**Review current results**  \nOpen the ranked list and secure report for the loaded session."
        )
        if "Results" in allowed_pages:
            if st.button(
                "Open Results →",
                key="home_open_results",
                disabled=not bool(result),
                use_container_width=True,
            ):
                queue_page("Results")
        else:
            st.caption("Results are not available for your role.")

    if result:
        summary = dict(result.get("summary") or {})
        matches = list(result.get("match_results") or [])
        average = (
            sum(float(item.overall_match_percentage or 0.0) for item in matches) / len(matches)
            if matches
            else 0.0
        )
        st.success(
            f"Loaded session: {summary.get('resumes_processed', 0)} candidates processed, "
            f"{average:.1f}% average match. Continue to Results for evidence and export."
        )
    elif project_count:
        latest = projects[0]
        st.info(
            f"Latest project: {latest.get('project_name') or 'Untitled project'} · "
            f"{latest.get('candidates', 0)} candidates. Open Candidate Database to continue."
        )
    else:
        st.info(
            "Your private workspace is ready. Begin with Resume Screening; the guided "
            "workflow will take you through preparation, screening, review and export."
        )
