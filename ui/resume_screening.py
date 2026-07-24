"""Streamlit workflow for end-to-end resume screening."""
from __future__ import annotations

import streamlit as st

from services.processing_service import ProcessingService
from services.upload_service import UploadService


def show_resume_screening() -> None:
    st.title("📄 Resume Screening")
    st.caption("JD + optional skill list + resume(s) → parse → match → score → rank")

    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project Name")
        client_name = st.text_input("Client Name")
    with col2:
        hiring_manager = st.text_input("Hiring Manager")
        job_id = st.text_input("Job ID")

    st.subheader("1. Job Description")
    uploaded_jd = st.file_uploader("Upload Job Description", type=["pdf", "docx", "txt"], key="jd_upload")

    st.subheader("2. Skill List (Optional)")
    uploaded_skill = st.file_uploader(
        "Upload an optional supplemental skill list",
        type=["xlsx", "csv", "txt"],
        key="skill_upload",
        help="Configured skills are added to the JD mandatory-skill requirements; they do not replace the JD.",
    )

    st.subheader("3. Resume(s)")
    uploaded_resumes = st.file_uploader(
        "Upload one or more resumes",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="resume_uploads",
    )

    can_analyze = uploaded_jd is not None and bool(uploaded_resumes)
    if st.button("🚀 Analyze Candidates", disabled=not can_analyze, type="primary"):
        try:
            with st.spinner("Saving files and running RecruitOS screening..."):
                jd_path = UploadService.save_job_description(uploaded_jd)
                resume_paths = UploadService.save_multiple_resumes(uploaded_resumes)
                skill_path = UploadService.save_skill_list(uploaded_skill) if uploaded_skill else None
                result = ProcessingService.process_documents(
                    jd_path=jd_path,
                    resume_paths=resume_paths,
                    skill_list_path=skill_path,
                    job_id=job_id,
                )
                result["project"] = {
                    "project_name": project_name,
                    "client_name": client_name,
                    "hiring_manager": hiring_manager,
                    "job_id": job_id,
                }
                st.session_state["analysis_result"] = result

            summary = result["summary"]
            st.success(
                f"Analysis complete: {summary['resumes_processed']} processed, "
                f"{summary['resumes_failed']} failed. Open **Results** from the sidebar."
            )
            if result["errors"]:
                with st.expander("Files that could not be processed"):
                    for error in result["errors"]:
                        st.error(f"{error['file']}: {error['error']}")
        except Exception as exc:
            st.exception(exc)
