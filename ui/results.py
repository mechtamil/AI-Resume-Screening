"""
============================================================
RecruitOS
Results Screen
Version : 1.0
Author  : Tamilvanan A

Description:
Displays parsed Job Description and Candidate details.
============================================================
"""

import streamlit as st


def show():

    st.title("📊 Resume Screening Results")

    result = st.session_state.get("analysis_result")

    if result is None:
        st.warning("No analysis available.")
        return

    # -----------------------------
    # Job Description
    # -----------------------------
    jd = result["job_description"]

    st.header("Job Description")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Job Title**")
        st.write(jd.job_title)

        st.write("**Experience**")
        st.write(
            f"{jd.experience_min} - {jd.experience_max} Years"
        )

    with col2:
        st.write("**Mandatory Skills**")
        st.write(len(jd.mandatory_skills))

        st.write("**Preferred Skills**")
        st.write(len(jd.preferred_skills))

    if jd.mandatory_skills:

        st.subheader("Mandatory Skills")

        st.write(jd.mandatory_skills)

    # -----------------------------
    # Candidates
    # -----------------------------
    st.divider()

    st.header("Candidates")

    candidates = result["candidates"]

    if len(candidates) == 0:

        st.info("No resumes processed.")

        return

    for index, candidate in enumerate(candidates, start=1):

        with st.expander(f"{index}. {candidate.full_name}"):

            col1, col2 = st.columns(2)

            with col1:

                st.write("**Email**")

                st.write(candidate.email)

                st.write("**Phone**")

                st.write(candidate.phone)

            with col2:

                st.write("**Experience**")

                st.write(candidate.total_experience)

                st.write("**Skills**")

                st.write(candidate.total_skills())

            if candidate.technical_skills:

                st.write("### Technical Skills")

                st.write(candidate.technical_skills)

            if candidate.tools:

                st.write("### Tools")

                st.write(candidate.tools)

            if candidate.projects:

                st.write("### Projects")

                st.write(candidate.projects)