import streamlit as st


def show_home():

    st.title("🤖 RecruitOS")

    st.subheader("AI Recruitment Platform")

    st.markdown("---")

    st.success("Welcome Tamilvanan!")

    st.write(
        """
RecruitOS helps recruiters:

- Upload resumes
- Compare resumes with Job Descriptions
- Rank candidates
- Generate interview questions
- Export reports
"""
    )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Resumes Processed", "0")

    with col2:
        st.metric("Candidates Shortlisted", "0")

    with col3:
        st.metric("Average Match", "0%")

    st.markdown("---")

    if st.button("🚀 Start Resume Screening"):

        st.session_state.page = "Resume Screening"

        st.success("Please select 'Resume Screening' from the left menu.")