from models.job_description import JobDescription

jd = JobDescription()

jd.job_title = "Technical Documentation Engineer"

jd.client_name = "Volvo"

jd.experience = "4 to 8 Years"

jd.location = "Bangalore"

jd.mandatory_skills = [
    "DITA",
    "XML",
    "Arbortext",
    "Technical Publications"
]

jd.preferred_skills = [
    "Python",
    "FrameMaker"
]

jd.display()