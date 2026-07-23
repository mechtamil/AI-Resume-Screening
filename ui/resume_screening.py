"""
============================================================
RecruitOS - AI Recruitment Platform
Module : Resume Screening
Version : 0.4.0
Author  : Tamilvanan A
============================================================
"""

import streamlit as st

from services.upload_service import UploadService


def show_resume_screening():

    st.title("📄 Resume Screening")

    st.markdown("---")

    st.subheader("Project Information")

    col1, col2 = st.columns(2)

    with col1:
        project_name = st.text_input(
            "Project Name",
            placeholder="Example: Volvo Technical Documentation"
        )

        client_name = st.text_input(
            "Client Name",
            placeholder="Example: Volvo"
        )

    with col2:
        hiring_manager = st.text_input(
            "Hiring Manager",
            placeholder="Example: Tamilvanan A"
        )

        job_id = st.text_input(
            "Job ID",
            placeholder="Example: JD-001"
        )

    st.markdown("---")

    st.subheader("STEP 1 - Upload Job Description")

    uploaded_jd = st.file_uploader(
        "Upload Job Description",
        type=["pdf", "docx", "txt"],
        key="jd_upload"
    )

    jd_saved_path = None

    if uploaded_jd:

        jd_saved_path = UploadService.save_job_description(uploaded_jd)

        st.success(f"✅ Job Description saved to:\n{jd_saved_path}")

    st.markdown("---")

    st.subheader("STEP 2 - Upload Skill List (Optional)")

    uploaded_skill = st.file_uploader(
        "Upload Skill List",
        type=["xlsx", "csv", "txt"],
        key="skill_upload"
    )

    skill_saved_path = None

    if uploaded_skill:

        skill_saved_path = UploadService.save_skill_list(uploaded_skill)

        st.success(f"✅ Skill List saved to:\n{skill_saved_path}")

    st.markdown("---")

    st.subheader("STEP 3 - Upload Resume(s)")

    upload_option = st.radio(
        "Resume Upload Type",
        [
            "Single Resume",
            "Multiple Resumes"
        ]
    )

    saved_resumes = []

    if upload_option == "Single Resume":

        uploaded_resume = st.file_uploader(
            "Upload Resume",
            type=["pdf", "docx", "txt"],
            key="single_resume"
        )

        if uploaded_resume:

            saved_file = UploadService.save_resume(uploaded_resume)

            saved_resumes.append(saved_file)

            st.success(f"✅ Resume saved:\n{saved_file}")

    else:

        uploaded_resumes = st.file_uploader(
            "Upload Multiple Resumes",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            key="multiple_resume"
        )

        if uploaded_resumes:

            saved_resumes = UploadService.save_multiple_resumes(
                uploaded_resumes
            )

            st.success(f"✅ {len(saved_resumes)} Resume(s) uploaded successfully.")

            with st.expander("View Uploaded Files"):

                for resume in saved_resumes:
                    st.write(resume)

    st.markdown("---")

    st.subheader("Recruitment Options")

    extract_details = st.checkbox(
        "Extract Candidate Details",
        value=True
    )

    skill_matching = st.checkbox(
        "Skill Matching",
        value=True
    )

    ai_summary = st.checkbox(
        "AI Resume Summary",
        value=True
    )

    interview_questions = st.checkbox(
        "Generate Interview Questions",
        value=True
    )

    export_excel = st.checkbox(
        "Export Excel Report",
        value=True
    )

    st.markdown("---")

    can_analyze = (
        uploaded_jd is not None
        and len(saved_resumes) > 0
    )

    if st.button(
        "🚀 Analyze Candidates",
        disabled=not can_analyze
    ):

        progress = st.progress(0)

        status = st.empty()

        steps = [
            "Saving Uploaded Files...",
            "Reading Job Description...",
            "Reading Resume(s)...",
            "Parsing Documents...",
            "Matching Skills...",
            "Generating Reports...",
            "Completed."
        ]

        for index, step in enumerate(steps):

            progress.progress((index + 1) * 100 // len(steps))

            status.info(step)

        st.success("🎉 Analysis Completed Successfully!")

        st.info(
            "The Resume Parser and AI Matching Engine "
            "will be connected in the next milestone."
        )