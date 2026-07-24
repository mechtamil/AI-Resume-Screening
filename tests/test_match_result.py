from models.match_result import MatchResult


result = MatchResult()

result.candidate_name = "Tamilvanan A"

result.skill_score = 90

result.experience_score = 95

result.education_score = 85

result.certification_score = 70

result.keyword_score = 92

result.overall_score = 89.4

result.recommendation = "Highly Recommended"

result.matched_skills = [
    "Python",
    "SQL",
    "Docker"
]

result.missing_skills = [
    "AWS"
]

result.add_remark(
    "Matched 3 of 4 mandatory skills."
)

result.display()

print()

print(result.summary())