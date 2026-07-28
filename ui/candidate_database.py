"""Streamlit private project and candidate database interface."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from models.security_context import SecurityContext
from services.persistence_service import PersistenceService
from ui.brand_components import page_header_html


def show_candidate_database(context: SecurityContext) -> None:
    context.require_valid()
    st.markdown(
        page_header_html(
            title="Candidate intelligence",
            eyebrow="Private talent database",
            description=(
                "Reopen ranked screening sessions, review candidate records and "
                "manage projects visible only inside your workspace."
            ),
        ),
        unsafe_allow_html=True,
    )

    try:
        projects = PersistenceService.list_projects(context)
    except Exception as exc:
        st.error(f"Candidate database could not be loaded: {exc}")
        return

    if not projects:
        st.info("No screening project has been saved in your workspace yet.")
        return

    project_rows = [
        {
            "Project ID": item["id"],
            "Project": item["project_name"],
            "Client": item["client_name"],
            "Job ID": item["job_id"],
            "Role": item["job_title"],
            "Status": item["status"],
            "Sessions": item["screening_sessions"],
            "Candidates": item["candidates"],
            "Shortlisted": item["shortlisted"],
            "Updated": item["updated_at"],
        }
        for item in projects
    ]

    st.subheader("Recruitment Projects")
    st.dataframe(
        pd.DataFrame(project_rows),
        use_container_width=True,
        hide_index=True,
    )

    project_options = {
        f"{item['project_name']} — {item['job_title']} — ID {item['id']}": item
        for item in projects
    }
    selected_label = st.selectbox("Select project", list(project_options))
    selected_project = project_options[selected_label]
    project_id = int(selected_project["id"])

    sessions = PersistenceService.list_sessions(context, project_id)
    st.subheader("Screening Sessions")

    if not sessions:
        st.info("This project has no saved screening session.")
        return

    session_rows = [
        {
            "Session ID": item["id"],
            "Created": item["created_at"],
            "Requested": item["resumes_requested"],
            "Processed": item["resumes_processed"],
            "Failed": item["resumes_failed"],
            "Shortlisted": item["shortlisted_count"],
            "Status": item["status"],
        }
        for item in sessions
    ]
    st.dataframe(
        pd.DataFrame(session_rows),
        use_container_width=True,
        hide_index=True,
    )

    session_options = {
        f"Session {item['id']} — {item['created_at']} — "
        f"{item['resumes_processed']} candidates": item
        for item in sessions
    }
    selected_session_label = st.selectbox(
        "Select screening session",
        list(session_options),
    )
    selected_session = session_options[selected_session_label]
    session_id = int(selected_session["id"])

    candidates = PersistenceService.list_candidate_records(
        context,
        project_id=project_id,
        session_id=session_id,
    )
    st.subheader("Candidates")
    candidate_rows = [
        {
            "Candidate ID": item["id"],
            "Name": item["full_name"],
            "Email": item["email"],
            "Phone": item["phone"],
            "Location": item["location"],
            "Experience": item["total_experience"],
            "Source File": item["source_file"],
            "Status": item["status"],
        }
        for item in candidates
    ]
    st.dataframe(
        pd.DataFrame(candidate_rows),
        use_container_width=True,
        hide_index=True,
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button(
            "📂 Reopen Selected Screening Results",
            type="primary",
            use_container_width=True,
        ):
            try:
                st.session_state["analysis_result"] = PersistenceService.load_session(
                    context,
                    session_id,
                )
                st.session_state["page"] = "Results"
                st.rerun()
            except Exception as exc:
                st.exception(exc)

    with col2:
        confirm_delete = st.checkbox("Confirm project deletion")
        if st.button(
            "🗑 Delete Project",
            disabled=not confirm_delete,
            use_container_width=True,
        ):
            try:
                deleted = PersistenceService.delete_project(context, project_id)
                if deleted:
                    st.success("Project and related sessions were deleted.")
                    st.rerun()
                else:
                    st.warning("The project was not available in your workspace.")
            except Exception as exc:
                st.exception(exc)
