from models.candidate import Candidate
from JD.jd_model import JobDescription
from models.match_result import MatchResult

from services.matching.experience_matcher import (
    ExperienceMatcher
)

candidate = Candidate()

candidate.full_name = "Tamilvanan A"

candidate.total_experience = 6


job = JobDescription()

job.job_title = "Python Developer"

job.experience_min = 5


result = MatchResult()

result.candidate_name = candidate.full_name

result.job_title = job.job_title


result = ExperienceMatcher.match(

    candidate,

    job,

    result

)

result.display()

print()

print(result.summary())