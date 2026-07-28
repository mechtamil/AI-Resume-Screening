"""Private Streamlit screening-results dashboard and secure report export."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from models.security_context import SecurityContext
from models.storage_asset import StorageScope
from services.authorization_service import PERMISSION_RESULTS, AuthorizationService
from services.secure_export_service import SecureExportService
from services.secure_storage_service import SecureStorageService
from ui.brand_components import page_header_html


def show(context: SecurityContext) -> None:
    context.require_valid()
    AuthorizationService.require_permission(context, PERMISSION_RESULTS)
    st.markdown(
        page_header_html(
            title="Screening results",
            eyebrow="Private evidence dashboard",
            description=(
                "Review candidate ranking, score evidence and a securely generated "
                "Excel report available only in your workspace."
            ),
        ),
        unsafe_allow_html=True,
    )

    result = st.session_state.get("analysis_result")
    if not result:
        st.warning("No analysis is available. Run Resume Screening first or reopen a saved session.")
        return

    jd = result["job_description"]
    matches = result.get("match_results", [])

    st.subheader("Job description")
    col1, col2, col3 = st.columns(3)
    col1.metric("Job Title", jd.job_title or "Not detected")
    col2.metric("Experience", _experience_label(jd.experience_min, jd.experience_max))
    col3.metric("Candidates", len(matches))
    st.write("**Mandatory Skills:**", ", ".join(jd.mandatory_skills) or "None")
    st.write("**Preferred Skills:**", ", ".join(jd.preferred_skills) or "None")

    if not matches:
        st.info("No candidates were successfully processed.")
        _show_processing_errors(result)
        return

    st.subheader("Candidate ranking")
    rows = [item.summary() for item in matches]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Secure export")
    scope = _scope_from_result(context, result)
    cache_key = f"secure_excel_{context.tenant_id}_{context.user_id}_{scope.workspace_id}"
    try:
        if cache_key not in st.session_state:
            artifact = SecureExportService().build_excel_report(context, scope, result)
            st.session_state[cache_key] = {
                "filename": artifact.filename,
                "data": artifact.data,
                "stored_file": artifact.stored_file.summary(),
            }
        report = st.session_state[cache_key]
        st.download_button(
            label="⬇️ Download private ranked screening report",
            data=report["data"],
            file_name=report["filename"],
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )
        st.caption(
            "The generated report is stored under your private tenant/user/session "
            "workspace and cannot be read through another user's security context."
        )
    except Exception as exc:
        st.warning(f"The private Excel report could not be prepared: {exc}")

    st.subheader("Candidate details")
    for item in matches:
        label = (
            f"#{item.rank} {item.candidate_name or item.source_file} — "
            f"{item.overall_match_percentage:.2f}% — {item.recommendation}"
        )
        with st.expander(label):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Matched mandatory skills**", item.matched_skills or "None")
                st.write("**Missing mandatory skills**", item.missing_skills or "None")
                st.write(
                    "**Matched preferred skills**",
                    item.matched_preferred_skills or "None",
                )
                st.write(
                    "**Missing preferred skills**",
                    getattr(item, "missing_preferred_skills", []) or "None",
                )
                st.write("**Additional skills**", item.additional_skills or "None")
            with col2:
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

    _show_processing_errors(result)


def _scope_from_result(context: SecurityContext, result: dict) -> StorageScope:
    storage = dict(result.get("storage") or {})
    persistence = dict(result.get("persistence") or {})
    workspace_id = str(
        storage.get("workspace_id")
        or persistence.get("session_key")
        or ""
    ).strip().lower()
    if not workspace_id:
        scope = SecureStorageService.create_scope(context)
        result["storage"] = scope.summary()
        return scope
    scope = StorageScope(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        workspace_id=workspace_id,
    )
    scope.require_valid()
    return scope


def _experience_label(minimum: float, maximum: float) -> str:
    if maximum:
        return f"{minimum:g}–{maximum:g} years"
    if minimum:
        return f"{minimum:g}+ years"
    return "Not specified"


def _show_processing_errors(result: dict) -> None:
    errors = result.get("errors", [])
    if errors:
        st.subheader("Processing errors")
        for error in errors:
            st.error(f"{error['file']}: {error['error']}")
