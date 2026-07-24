from services.matching.skill_matcher import SkillMatcher

from models.candidate import Candidate

from JD.jd_model import JobDescription


candidate = Candidate()

candidate.full_name = "Tamilvanan A"

candidate.email = "tamil@example.com"

candidate.technical_skills = [

    "Python",

    "SQL",

    "Docker",

    "Git",

    "Linux"

]


job = JobDescription()

job.job_title = "Python Developer"

job.mandatory_skills = [

    "Python",

    "SQL",

    "Docker",

    "REST API",

    "Git"

]


result = SkillMatcher.match(
    candidate,
    job
)

result.display()