from models.match_result import MatchResult

result = MatchResult(
    candidate_name="Tamilvanan",
    matched_skills=["Python", "Streamlit"],
    missing_skills=["SQL"],
    additional_skills=["Power BI"],
    skill_match_percentage=66.67,
    overall_match_percentage=74,
    recommendation="Shortlist"
)

print(result.summary())

print(result.is_shortlisted())