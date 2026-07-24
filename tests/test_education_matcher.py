from models.candidate import Candidate
from JD.jd_model import JobDescription
from models.match_result import MatchResult

from services.matching.education_matcher import (
    EducationMatcher
)

candidate = Candidate()

candidate.full_name = "Tamilvanan A"

candidate.education = [

    "B.E Mechanical Engineering"

]

job = JobDescription()

job.job_title = "Technical Documentation Engineer"

job.education = [

    "B.E Mechanical Engineering"

]

result = MatchResult()

result.candidate_name = candidate.full_name

result.job_title = job.job_title

result = EducationMatcher.match(

    candidate,

    job,

    result

)

result.display()

print()

print(result.summary())