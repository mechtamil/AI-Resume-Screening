from models.candidate import Candidate


def main():

    candidate = Candidate()

    candidate.full_name = "Tamil"

    candidate.total_experience = 6

    candidate.technical_skills.extend([
        "XML",
        "DITA",
        "Python"
    ])

    candidate.tools.extend([
        "Arbortext",
        "LISA"
    ])

    candidate.projects.extend([
        "Volvo SPI",
        "Volvo TI"
    ])

    print(candidate.summary())


if __name__ == "__main__":
    main()