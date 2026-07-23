from JD.jd_parser import JDParser


sample_document = {

    "file_name": "TechnicalWriterJD.pdf",

    "text": """
Technical Writer

Experience : 3 to 5 Years

Skills

DITA
XML
Python
Arbortext
LISA
"""
}


def main():

    jd = JDParser.parse(sample_document)

    print("Job Title :", jd.job_title)

    print("Experience :", jd.experience_min, "-", jd.experience_max)

    print("Skills :", jd.mandatory_skills)


if __name__ == "__main__":
    main()