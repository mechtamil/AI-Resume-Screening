"""Streamlit private project and candidate database interface."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from models.security_context import SecurityContext
from services.authorization_service import (
    PERMISSION_SHARED_MANAGE_OWN,
    AuthorizationService,
)
from services.persistence_service import PersistenceService
from services.sharing_service import SharingService
from ui.brand_components import page_header_html
from ui.navigation import queue_page


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
        if st.button("Start Resume Screening →", type="primary", use_container_width=True):
            queue_page("Resume Screening")
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

    if AuthorizationService.has_permission(context, PERMISSION_SHARED_MANAGE_OWN):
        _show_project_sharing(context, selected_project)

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
                queue_page("Results")
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

def _show_project_sharing(context: SecurityContext, project: dict) -> None:
    """Grant and revoke explicit read-only project access."""
    project_id = int(project["id"])
    with st.expander("Share project and assign review", expanded=False):
        st.caption(
            "Projects remain private until an explicit share is created. Reader and "
            "Reviewer access is read-only; Reviewer assignments may update review progress only."
        )
        try:
            recipients = SharingService.list_shareable_users(context)
            shares = SharingService.list_owned_shares(
                context,
                project_id=project_id,
            )
        except Exception as exc:
            st.error(f"Sharing controls could not be loaded: {exc}")
            return

        if recipients:
            recipient_options = {
                (
                    f"{item['employee_user_id']} — {item['display_name']} — "
                    f"{item['role_code']} — {item['country_location']}"
                ): item
                for item in recipients
            }
            with st.form(f"grant_project_share_{project_id}"):
                selected_recipient = st.selectbox(
                    "Recipient",
                    list(recipient_options),
                )
                access_role = st.selectbox(
                    "Assignment",
                    [SharingService.ACCESS_READER, SharingService.ACCESS_REVIEWER],
                    format_func=lambda value: (
                        "Reader — read-only evidence"
                        if value == SharingService.ACCESS_READER
                        else "Reviewer — read-only evidence and review progress"
                    ),
                )
                expiry_days = st.number_input(
                    "Access expiry in days",
                    min_value=0,
                    max_value=3650,
                    value=30,
                    step=1,
                    help="Use 0 only for an approved non-expiring assignment.",
                )
                note = st.text_area(
                    "Assignment note (optional)",
                    max_chars=500,
                )
                grant = st.form_submit_button(
                    "Grant Project Access",
                    type="primary",
                    use_container_width=True,
                )
            if grant:
                recipient = recipient_options[selected_recipient]
                expires_at = (
                    datetime.now(timezone.utc) + timedelta(days=int(expiry_days))
                    if int(expiry_days) > 0
                    else None
                )
                try:
                    SharingService.grant_project_share(
                        context,
                        project_id=project_id,
                        grantee_user_id=int(recipient["id"]),
                        access_role=access_role,
                        expires_at=expires_at,
                        note=note,
                    )
                    st.success("Project access was granted and recorded in the audit trail.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Project access could not be granted: {exc}")
        else:
            st.info(
                "No active recipient is available in your sharing scope. "
                "Provision a Reader or User in Administration first."
            )

        st.markdown("**Sharing history**")
        if not shares:
            st.caption("This project has never been shared.")
            return

        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Share ID": item["id"],
                        "Recipient": item["grantee_name"],
                        "User ID": item["grantee_login_id"],
                        "Assignment": str(item["access_role"]).title(),
                        "Status": str(item["status"]).title(),
                        "Review": str(item["review_status"]).replace("_", " ").title(),
                        "Expires": item["expires_at"] or "No expiry",
                        "Created": item["created_at"],
                    }
                    for item in shares
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

        active = [item for item in shares if item.get("status") == "ACTIVE"]
        if active:
            revoke_options = {
                (
                    f"Share {item['id']} — {item['grantee_name']} — "
                    f"{str(item['access_role']).title()}"
                ): item
                for item in active
            }
            revoke_label = st.selectbox(
                "Active access to revoke",
                list(revoke_options),
                key=f"revoke_share_select_{project_id}",
            )
            confirm_revoke = st.checkbox(
                "Confirm access revocation",
                key=f"confirm_revoke_share_{project_id}",
            )
            if st.button(
                "Revoke Selected Access",
                disabled=not confirm_revoke,
                use_container_width=True,
                key=f"revoke_share_button_{project_id}",
            ):
                try:
                    revoked = SharingService.revoke_share(
                        context,
                        int(revoke_options[revoke_label]["id"]),
                    )
                    if revoked:
                        st.success("Shared access was revoked immediately.")
                        st.rerun()
                    st.warning("The selected active share was not available.")
                except Exception as exc:
                    st.error(f"Shared access could not be revoked: {exc}")

