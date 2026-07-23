from parser.resume_parser import ResumeParser


sample_document = {

    "file_name": "Resume.pdf",

    "text": """
Tamilvanan A

Email:
tamil@example.com

Phone:
9876543210

Experience
6 Years

Python
XML
DITA
"""
}


def main():

    candidate = ResumeParser.parse(sample_document)

    print(candidate.summary())

    print(candidate.email)

    print(candidate.phone)


if __name__ == "__main__":
    main()