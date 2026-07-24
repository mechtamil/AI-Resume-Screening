"""
============================================================
RecruitOS

Enterprise Certification Extractor

Version : 1.0
Author  : Tamilvanan A
============================================================
"""

from services.certification_repository import (
    CertificationRepository
)


class CertificationExtractor:

    @staticmethod
    def extract(text):

        text_lower = text.lower()

        certifications = []

        for certification in (

            CertificationRepository
            .get_all_certifications()

        ):

            if certification.lower() in text_lower:

                certifications.append(

                    certification

                )

                continue

            standard = (

                CertificationRepository
                .get_standard_name(
                    certification
                )
            )

            if standard:

                if standard not in certifications:

                    certifications.append(

                        standard

                    )

        return sorted(

            list(set(certifications))

        )