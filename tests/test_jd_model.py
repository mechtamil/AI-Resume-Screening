from JD.jd_model import JobDescription


def main():

    jd = JobDescription()

    jd.job_title = "Technical Writer"

    jd.company_name = "ALTEN"

    jd.experience_min = 3

    jd.experience_max = 6

    jd.mandatory_skills.extend([
        "XML",
        "DITA",
        "Arbortext"
    ])

    jd.preferred_skills.extend([
        "KOLA",
        "LISA"
    ])

    print("Job Title :", jd.job_title)

    print("Company :", jd.company_name)

    print("Mandatory Skills :", jd.total_required_skills())

    print("Preferred Skills :", jd.total_preferred_skills())

    print(jd.summary())


if __name__ == "__main__":
    main()