from models.candidate import Candidate
from JD.jd_model import JobDescription


def create_mock_result():

    jd = JobDescription()

    jd.job_title = "Technical Writer"

    jd.experience_min = 3

    jd.experience_max = 5

    jd.mandatory_skills = [
        "XML",
        "DITA",
        "Python"
    ]

    candidate = Candidate()

    candidate.full_name = "Tamilvanan"

    candidate.email = "tamil@test.com"

    candidate.phone = "9876543210"

    candidate.total_experience = 6

    candidate.technical_skills = [
        "Python",
        "XML",
        "DITA"
    ]

    return {

        "job_description": jd,

        "candidates": [candidate]

    }


if __name__ == "__main__":

    result = create_mock_result()

    print(result)