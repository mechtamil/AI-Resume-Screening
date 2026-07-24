from services.certification_repository import (
    CertificationRepository
)

print()

print(

    CertificationRepository.total_certifications()

)

print()

print(

    CertificationRepository.get_standard_name(

        "AWS CCP"

    )

)

print()

print(

    CertificationRepository.exists(

        "PMP"

    )

)
