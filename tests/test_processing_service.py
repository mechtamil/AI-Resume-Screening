from services.processing_service import ProcessingService


def main():

    jd_path = "JD/sample_jd.docx"

    resumes = [

        "Resume/resume1.pdf",

        "Resume/resume2.pdf"

    ]

    result = ProcessingService.process_documents(

        jd_path,

        resumes

    )

    print(result["job_description"])

    print(len(result["candidates"]))


if __name__ == "__main__":
    main()