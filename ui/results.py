"""Streamlit screening-results dashboard."""
from __future__ import annotations

import pandas as pd
import streamlit as st


def show() -> None:
    st.title("📊 Resume Screening Results")
    result = st.session_state.get("analysis_result")
    if not result:
        st.warning("No analysis is available. Run Resume Screening first.")
        return

    jd = result["job_description"]
    matches = result.get("match_results", [])

    st.subheader("Job Description")
    col1, col2, col3 = st.columns(3)
    col1.metric("Job Title", jd.job_title or "Not detected")
    col2.metric("Experience", f"{jd.experience_min:g}–{jd.experience_max:g} years")
    col3.metric("Candidates", len(matches))
    st.write("**Mandatory Skills:**", ", ".join(jd.mandatory_skills) or "None")
    st.write("**Preferred Skills:**", ", ".join(jd.preferred_skills) or "None")

    if not matches:
        st.info("No candidates were successfully processed.")
        return

    rows = [item.summary() for item in matches]
    st.subheader("Candidate Ranking")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Candidate Details")
    for item in matches:
        label = f"#{item.rank} {item.candidate_name or item.source_file} — {item.overall_match_percentage:.2f}% — {item.recommendation}"
        with st.expander(label):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Matched mandatory skills**", item.matched_skills or "None")
                st.write("**Missing mandatory skills**", item.missing_skills or "None")
                st.write("**Matched preferred skills**", item.matched_preferred_skills or "None")
            with col2:
                st.write("**Experience score**", f"{item.experience_score:.2f}%")
                st.write("**Education score**", f"{item.education_score:.2f}%")
                st.write("**Certification score**", f"{item.certification_score:.2f}%")
                st.write("**Keyword score**", f"{item.keyword_score:.2f}%")
            st.write("**Weighted score breakdown**", item.weighted_score_breakdown)
            if item.remarks:
                st.write("**Remarks**")
                for remark in item.remarks:
                    st.write(f"• {remark}")

    errors = result.get("errors", [])
    if errors:
        st.subheader("Processing Errors")
        for error in errors:
            st.error(f"{error['file']}: {error['error']}")
