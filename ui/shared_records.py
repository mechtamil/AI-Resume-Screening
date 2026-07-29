"""Read-only Streamlit workspace for explicitly shared RecruitOS projects."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from models.security_context import SecurityContext
from services.authorization_service import (
    PERMISSION_SHARED_READ,
    AuthorizationService,
)
from services.sharing_service import SharingService
from ui.brand_components import page_header_html


def show_shared_records(context: SecurityContext) -> None:
    """Render received project shares and read-only screening evidence."""
    context.require_valid()
    AuthorizationService.require_permission(context, PERMISSION_SHARED_READ)
    st.markdown(
        page_header_html(
            title="Shared records",
            eyebrow="Reader and reviewer workspace",
            description=(
                "Open only the project evidence explicitly assigned to your account. "
                "Shared records remain owned by the recruiter and cannot be edited or exported here."
            ),
        ),
        unsafe_allow_html=True,
    )

    try:
        shares = SharingService.list_received_shares(context)
    except Exception as exc:
        st.error(f"Shared records could not be loaded: {exc}")
        return

    if not shares:
        st.info("No active project has been shared with your account.")
        return

    reader_count = sum(1 for item in shares if item.get("access_role") == "READER")
    reviewer_count = sum(1 for item in shares if item.get("access_role") == "REVIEWER")
    col1, col2, col3 = st.columns(3)
    col1.metric("Active shares", len(shares))
    col2.metric("Reader access", reader_count)
    col3.metric("Review assignments", reviewer_count)

    st.subheader("Assigned projects")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Share ID": item["id"],
                    "Project": item["project_name"],
                    "Client": item["client_name"],
                    "Role": item["job_title"],
                    "Owner": item["owner_name"],
                    "Access": item["access_role"].title(),
                    "Review Status": str(item["review_status"]).replace("_", " ").title(),
                    "Expires": item["expires_at"] or "No expiry",
                }
                for item in shares
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    share_options = {
        (
            f"{item['project_name']} — {item['job_title']} — "
            f"{item['access_role'].title()} — Share {item['id']}"
        ): item
        for item in shares
    }
    selected_label = st.selectbox("Select shared project", list(share_options))
    share = share_options[selected_label]
    share_id = int(share["id"])

    info1, info2, info3 = st.columns(3)
    info1.metric("Access", str(share["access_role"]).title())
    info2.metric("Owner", str(share["owner_name"] or "Not available"))
    info3.metric("Expiry", str(share["expires_at"] or "No expiry"))
    if str(share.get("note") or "").strip():
        st.info(f"Owner note: {share['note']}")

    if str(share.get("access_role") or "") == SharingService.ACCESS_REVIEWER:
        _show_review_progress(context, share)

    try:
        sessions = SharingService.list_shared_sessions(context, share_id)
    except Exception as exc:
        st.error(f"Shared sessions could not be loaded: {exc}")
        return

    if not sessions:
        st.info("The shared project has no saved screening session.")
        return

    st.subheader("Available screening sessions")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Session ID": item["id"],
                    "Created": item["created_at"],
                    "Processed": item["resumes_processed"],
                    "Failed": item["resumes_failed"],
                    "Shortlisted": item["shortlisted_count"],
                    "Status": item["status"],
                }
                for item in sessions
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    session_options = {
        (
            f"Session {item['id']} — {item['created_at']} — "
            f"{item['resumes_processed']} candidates"
        ): item
        for item in sessions
    }
    session_label = st.selectbox(
        "Select screening session",
        list(session_options),
        key=f"shared_session_{share_id}",
    )
    selected_session = session_options[session_label]
    session_id = int(selected_session["id"])
    result_key = f"shared_evidence_{context.user_id}_{share_id}_{session_id}"

    if st.button(
        "Open Read-Only Evidence",
        type="primary",
        use_container_width=True,
        key=f"open_shared_evidence_{share_id}_{session_id}",
    ):
        try:
            st.session_state[result_key] = SharingService.load_shared_session(
                context,
                share_id=share_id,
                session_id=session_id,
            )
        except Exception as exc:
            st.error(f"Shared evidence could not be opened: {exc}")

    result = st.session_state.get(result_key)
    if result:
        _show_read_only_evidence(result)

    with st.expander("Sharing audit history"):
        try:
            events = SharingService.list_share_audit(context, share_id)
            if not events:
                st.caption("No audit event is available for this share.")
            else:
                rows = []
                for event in events:
                    try:
                        details = json.loads(str(event.get("details_json") or "{}"))
                    except (TypeError, ValueError, json.JSONDecodeError):
                        details = {}
                    rows.append(
                        {
                            "Time": event.get("created_at"),
                            "Action": event.get("action"),
                            "Outcome": event.get("outcome"),
                            "Details": details,
                        }
                    )
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"Sharing audit history is unavailable: {exc}")


def _show_review_progress(context: SecurityContext, share: dict) -> None:
    share_id = int(share["id"])
    st.subheader("Reviewer progress")
    status_labels = {
        SharingService.REVIEW_ASSIGNED: "Assigned",
        SharingService.REVIEW_IN_REVIEW: "In Review",
        SharingService.REVIEW_COMPLETED: "Completed",
    }
    current_status = str(share.get("review_status") or SharingService.REVIEW_ASSIGNED)
    options = list(status_labels)
    default_index = options.index(current_status) if current_status in options else 0
    with st.form(f"review_progress_{share_id}"):
        review_status = st.selectbox(
            "Review status",
            options,
            index=default_index,
            format_func=lambda value: status_labels[value],
        )
        review_note = st.text_area(
            "Review note",
            value=str(share.get("review_note") or ""),
            max_chars=2000,
            help="This note records review progress only; it does not alter candidate evidence.",
        )
        submitted = st.form_submit_button(
            "Update Review Progress",
            type="primary",
            use_container_width=True,
        )
    if submitted:
        try:
            SharingService.update_review(
                context,
                share_id=share_id,
                review_status=review_status,
                review_note=review_note,
            )
            st.success("Reviewer progress was updated without changing screening evidence.")
            st.rerun()
        except Exception as exc:
            st.error(f"Reviewer progress could not be updated: {exc}")


def _show_read_only_evidence(result: dict) -> None:
    st.markdown("---")
    st.subheader("Read-only screening evidence")
    st.caption(
        "This view contains persisted ranking evidence only. Editing, deletion, "
        "re-screening and report export are disabled for shared access."
    )

    job = result["job_description"]
    matches = list(result.get("match_results") or [])
    col1, col2, col3 = st.columns(3)
    col1.metric("Job Title", job.job_title or "Not detected")
    col2.metric("Candidates", len(matches))
    col3.metric("Shortlisted", sum(1 for item in matches if item.shortlisted))
    st.write("**Mandatory Skills:**", ", ".join(job.mandatory_skills) or "None")
    st.write("**Preferred Skills:**", ", ".join(job.preferred_skills) or "None")

    configuration = dict(result.get("configuration") or {})
    if configuration:
        st.caption(
            "Configuration fingerprint: "
            f"{str(configuration.get('sha256') or '')[:12] or 'Not recorded'}"
        )

    if not matches:
        st.info("No processed candidate evidence is available in this session.")
        return

    st.dataframe(
        pd.DataFrame([item.summary() for item in matches]),
        use_container_width=True,
        hide_index=True,
    )

    for item in matches:
        label = (
            f"#{item.rank} {item.candidate_name or item.source_file} — "
            f"{item.overall_match_percentage:.2f}% — {item.recommendation}"
        )
        with st.expander(label):
            left, right = st.columns(2)
            with left:
                st.write("**Matched mandatory skills**", item.matched_skills or "None")
                st.write("**Missing mandatory skills**", item.missing_skills or "None")
                st.write(
                    "**Matched preferred skills**",
                    item.matched_preferred_skills or "None",
                )
                st.write(
                    "**Missing preferred skills**",
                    item.missing_preferred_skills or "None",
                )
                st.write("**Additional skills**", item.additional_skills or "None")
            with right:
                st.write("**Skill score**", f"{item.skill_score:.2f}%")
                st.write("**Experience score**", f"{item.experience_score:.2f}%")
                st.write("**Education score**", f"{item.education_score:.2f}%")
                st.write("**Certification score**", f"{item.certification_score:.2f}%")
                st.write("**Keyword score**", f"{item.keyword_score:.2f}%")
            st.write("**Weighted score breakdown**", item.weighted_score_breakdown)
            if item.remarks:
                st.write("**Remarks**")
                for remark in item.remarks:
                    st.write(f"• {remark}")
