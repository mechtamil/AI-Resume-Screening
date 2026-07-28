"""Streamlit workflow for private end-to-end resume screening."""
from __future__ import annotations

import streamlit as st

from config.settings import MAX_RESUMES_PER_SCREENING
from models.security_context import SecurityContext
from services.authorization_service import PERMISSION_SCREEN, AuthorizationService
from services.persistence_service import PersistenceService
from services.processing_service import ProcessingService
from services.upload_service import UploadService
from ui.brand_components import page_header_html


def show_resume_screening(context: SecurityContext) -> None:
    context.require_valid()
    AuthorizationService.require_permission(context, PERMISSION_SCREEN)
    st.markdown(
        page_header_html(
            title="Screen candidates",
            eyebrow="Private AI-assisted workflow",
            description=(
                "Every JD, resume, skill list and report is stored inside your "
                "tenant- and user-isolated screening workspace."
            ),
        ),
        unsafe_allow_html=True,
    )

    st.subheader("Project intelligence")
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project Name")
        client_name = st.text_input("Client Name")
        target_headcount = st.number_input(
            "Target Headcount",
            min_value=0,
            step=1,
            value=0,
        )
    with col2:
        hiring_manager = st.text_input("Hiring Manager")
        job_id = st.text_input("Job ID")
        project_status = st.selectbox("Project Status", ["Open", "On Hold", "Closed"])

    st.subheader("01 · Job description")
    uploaded_jd = st.file_uploader(
        "Upload Job Description",
        type=["pdf", "docx", "txt"],
        key="jd_upload",
    )

    st.subheader("02 · Supplemental skill list")
    uploaded_skill = st.file_uploader(
        "Upload an optional supplemental skill list",
        type=["xlsx", "csv", "txt"],
        key="skill_upload",
        help=(
            "Configured skills are added to the JD mandatory-skill requirements; "
            "they do not replace the JD."
        ),
    )

    st.subheader("03 · Candidate resumes")
    uploaded_resumes = st.file_uploader(
        "Upload one or more resumes",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="resume_uploads",
        help=f"Maximum {MAX_RESUMES_PER_SCREENING} resumes per screening session.",
    )

    resume_count = len(uploaded_resumes or [])
    if resume_count > MAX_RESUMES_PER_SCREENING:
        st.error(
            f"This screening contains {resume_count} resumes. The configured maximum is "
            f"{MAX_RESUMES_PER_SCREENING}."
        )

    can_analyze = (
        uploaded_jd is not None
        and bool(uploaded_resumes)
        and resume_count <= MAX_RESUMES_PER_SCREENING
    )

    if st.button(
        "Analyze and Save Candidates",
        disabled=not can_analyze,
        type="primary",
        use_container_width=True,
    ):
        scope = UploadService.create_workspace(context)
        persisted = False
        try:
            with st.spinner(
                "Creating your private workspace, screening candidates and saving the ranked session..."
            ):
                jd_asset = UploadService.save_job_description(context, scope, uploaded_jd)
                resume_assets = UploadService.save_multiple_resumes(
                    context,
                    scope,
                    uploaded_resumes,
                )
                skill_asset = (
                    UploadService.save_skill_list(context, scope, uploaded_skill)
                    if uploaded_skill
                    else None
                )

                result = ProcessingService.process_documents(
                    jd_path=jd_asset.absolute_path,
                    resume_paths=[item.absolute_path for item in resume_assets],
                    skill_list_path=(skill_asset.absolute_path if skill_asset else None),
                    job_id=job_id,
                    security_context=context,
                )
                result["project"] = {
                    "project_name": project_name,
                    "client_name": client_name,
                    "hiring_manager": hiring_manager,
                    "job_id": job_id,
                    "target_headcount": int(target_headcount),
                    "status": project_status,
                }
                result["storage"] = {
                    **scope.summary(),
                    "job_description": jd_asset.summary(),
                    "resumes": [item.summary() for item in resume_assets],
                    "skill_list": skill_asset.summary() if skill_asset else None,
                }

                persistence = PersistenceService.save_analysis_result(context, result)
                persisted = True
                st.session_state["analysis_result"] = result

            summary = result["summary"]
            st.success(
                f"Analysis complete and privately saved as Session "
                f"{persistence['session_id']}: "
                f"{summary['resumes_processed']} processed, "
                f"{summary['resumes_failed']} failed. Open Results from navigation."
            )
            if result["errors"]:
                with st.expander("Files that could not be processed"):
                    for error in result["errors"]:
                        st.error(f"{error['file']}: {error['error']}")
        except Exception as exc:
            if not persisted:
                UploadService.delete_workspace(context, scope)
            st.exception(exc)
        finally:
            UploadService.cleanup_temp_workspace(context, scope)
