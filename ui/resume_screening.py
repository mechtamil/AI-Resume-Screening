import streamlit as st


def show_resume_screening():

    st.title("📄 Resume Screening")

    st.markdown("---")

    upload_option = st.radio(
        "Select Upload Type",
        [
            "Single Resume",
            "Multiple Resumes"
        ]
    )

    if upload_option == "Single Resume":

        uploaded_resume = st.file_uploader(
            "Upload Resume",
            type=["pdf", "docx", "txt"]
        )

    else:

        uploaded_resume = st.file_uploader(
            "Upload Resumes",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )

    st.markdown("---")

    uploaded_jd = st.file_uploader(
        "Upload Job Description (Optional)",
        type=["pdf", "docx", "txt"]
    )

    st.markdown("---")

    st.subheader("Recruitment Options")

    st.checkbox("Extract Candidate Details", value=True)
    st.checkbox("Skill Matching", value=True)
    st.checkbox("AI Resume Summary", value=True)
    st.checkbox("Generate Interview Questions", value=True)
    st.checkbox("Export Excel Report", value=True)

    st.markdown("---")

    if st.button("🔍 Analyze"):

        progress = st.progress(0)

        status = st.empty()

        for i in range(100):

            progress.progress(i + 1)

            if i < 25:
                status.text("Reading Resume(s)...")

            elif i < 50:
                status.text("Extracting Information...")

            elif i < 75:
                status.text("Matching Skills...")

            else:
                status.text("Preparing Report...")

        st.success("Analysis Completed!")

        st.info("Actual resume parsing will be connected in the next milestone.")