"""RecruitOS home page."""
import streamlit as st


def show_home() -> None:
    st.title("🤖 RecruitOS")
    st.subheader("AI Resume Screening & Recruitment Platform")
    st.markdown(
        "Upload a Job Description and one or more resumes to parse, standardize, "
        "score, rank, and review candidates using configuration-driven rules."
    )

    result = st.session_state.get("analysis_result")
    if result:
        summary = result.get("summary", {})
        matches = result.get("match_results", [])
        shortlisted = sum(1 for item in matches if item.shortlisted)
        average = (
            sum(item.overall_match_percentage for item in matches) / len(matches)
            if matches else 0.0
        )
        col1, col2, col3 = st.columns(3)
        col1.metric("Resumes Processed", summary.get("resumes_processed", 0))
        col2.metric("Candidates Shortlisted", shortlisted)
        col3.metric("Average Match", f"{average:.1f}%")
    else:
        st.info("No screening run is loaded in this session yet.")
