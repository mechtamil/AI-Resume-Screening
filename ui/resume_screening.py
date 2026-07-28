"""Streamlit workflow for private multi-format resume screening."""
from __future__ import annotations

import streamlit as st

from config.settings import (
    MAX_RESUMES_PER_SCREENING,
    SUPPORTED_JD_TYPES,
    SUPPORTED_RESUME_TYPES,
    SUPPORTED_SKILL_TYPES,
)
from models.security_context import SecurityContext
from services.authorization_service import PERMISSION_SCREEN, AuthorizationService
from services.input_template_service import InputTemplateService
from services.persistence_service import PersistenceService
from services.processing_service import ProcessingService
from services.upload_service import UploadService
from ui.brand_components import page_header_html, workflow_stepper_html
from ui.navigation import queue_page


def _uploader_types(values: tuple[str, ...]) -> list[str]:
    return [value.lstrip(".") for value in values]


def _format_caption(values: tuple[str, ...]) -> str:
    return ", ".join(value.lstrip(".").upper() for value in values)


def show_resume_screening(context: SecurityContext) -> None:
    """Collect structured project inputs and execute one private screening session."""
    context.require_valid()
    AuthorizationService.require_permission(context, PERMISSION_SCREEN)

    st.markdown(
        page_header_html(
            title="Screen candidates",
            eyebrow="Guided private workflow",
            description=(
                "Use free-form documents or RecruitOS Excel templates. Common text, "
                "spreadsheet and image formats are normalized into one auditable pipeline."
            ),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(workflow_stepper_html(active_step=2), unsafe_allow_html=True)

    with st.expander("Start with RecruitOS templates for best extraction quality", expanded=True):
        st.write(
            "Templates do not artificially increase a candidate score. They improve input "
            "completeness and reduce ambiguity, which produces more reliable matching evidence."
        )
        template1, template2 = st.columns(2)
        with template1:
            st.download_button(
                "Download Job Description Excel Template",
                data=InputTemplateService.build_job_description_template(),
                file_name="RecruitOS_Job_Description_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_jd_template",
                use_container_width=True,
            )
        with template2:
            st.download_button(
                "Download Supplemental Skill List Template",
                data=InputTemplateService.build_skill_list_template(),
                file_name="RecruitOS_Supplemental_Skill_List_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_skill_template",
                use_container_width=True,
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
    st.caption(
        "Accepted formats: " + _format_caption(SUPPORTED_JD_TYPES) + ". "
        "Scanned PDFs and images are processed through OCR."
    )
    uploaded_jd = st.file_uploader(
        "Upload Job Description",
        type=_uploader_types(SUPPORTED_JD_TYPES),
        key="jd_upload",
        help="Use the Excel template when the JD has clearly separated requirements.",
    )

    st.subheader("02 · Supplemental skill list")
    st.caption("Accepted formats: " + _format_caption(SUPPORTED_SKILL_TYPES))
    uploaded_skill = st.file_uploader(
        "Upload an optional supplemental skill list",
        type=_uploader_types(SUPPORTED_SKILL_TYPES),
        key="skill_upload",
        help=(
            "Mandatory and preferred skills are merged into the corresponding JD sections; "
            "they do not replace the JD."
        ),
    )

    st.subheader("03 · Candidate resumes")
    st.caption(
        "Accepted formats: " + _format_caption(SUPPORTED_RESUME_TYPES) + ". "
        f"Maximum {MAX_RESUMES_PER_SCREENING} resumes per session."
    )
    uploaded_resumes = st.file_uploader(
        "Upload one or more resumes",
        type=_uploader_types(SUPPORTED_RESUME_TYPES),
        accept_multiple_files=True,
        key="resume_uploads",
    )

    resume_count = len(uploaded_resumes or [])
    if resume_count > MAX_RESUMES_PER_SCREENING:
        st.error(
            f"This screening contains {resume_count} resumes. The configured maximum is "
            f"{MAX_RESUMES_PER_SCREENING}."
        )

    st.subheader("04 · Review and run")
    input1, input2, input3 = st.columns(3)
    input1.metric("Job description", "Ready" if uploaded_jd else "Required")
    input2.metric("Skill list", "Included" if uploaded_skill else "Optional")
    input3.metric("Candidate resumes", resume_count)

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
                "Normalizing files, extracting evidence, matching candidates and saving the private session..."
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
                result["persistence"] = dict(persistence)
                st.session_state["analysis_result"] = result

            summary = result["summary"]
            st.success(
                f"Session {persistence['session_id']} saved: "
                f"{summary['resumes_processed']} processed and "
                f"{summary['resumes_failed']} failed."
            )
            if result["errors"]:
                with st.expander("Files that could not be processed"):
                    for error in result["errors"]:
                        st.error(f"{error['file']}: {error['error']}")

            if st.button(
                "View Ranked Results →",
                key="screening_view_results",
                type="primary",
                use_container_width=True,
            ):
                queue_page("Results")
        except Exception as exc:
            if not persisted:
                UploadService.delete_workspace(context, scope)
            st.exception(exc)
        finally:
            UploadService.cleanup_temp_workspace(context, scope)
