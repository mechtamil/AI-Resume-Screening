"""
============================================================
RecruitOS

Enterprise Certification Repository

Version : 1.0
Author  : Tamilvanan A

Description:
Loads certification master from Excel and provides
standard certification lookup services.
============================================================
"""

from pathlib import Path

import pandas as pd

from config.paths import CERTIFICATION_MASTER_FILE


class CertificationRepository:

    _repository = {}

    _loaded = False

    # --------------------------------------------------

    @classmethod
    def load(cls):

        if cls._loaded:

            return

        file = Path(CERTIFICATION_MASTER_FILE)

        if not file.exists():

            raise FileNotFoundError(

                f"Certification master not found:\n{file}"

            )

        df = pd.read_excel(file)

        df.fillna("", inplace=True)

        for _, row in df.iterrows():

            certification = str(

                row["Certification"]

            ).strip()

            category = str(

                row["Category"]

            ).strip()

            priority = str(

                row["Priority"]

            ).strip()

            active = str(

                row["Active"]

            ).strip().lower()

            synonyms = [

                s.strip()

                for s in str(

                    row["Synonyms"]

                ).split(";")

                if s.strip()

            ]

            values = [

                certification,

                *synonyms

            ]

            for value in values:

                cls._repository[
                    value.lower()
                ] = {

                    "standard": certification,

                    "category": category,

                    "priority": priority,

                    "active": active

                }

        cls._loaded = True

    # --------------------------------------------------

    @classmethod
    def get_standard_name(cls, value):

        cls.load()

        item = cls._repository.get(

            value.lower()

        )

        if item:

            return item["standard"]

        return None

    # --------------------------------------------------

    @classmethod
    def exists(cls, value):

        cls.load()

        return value.lower() in cls._repository

    # --------------------------------------------------

    @classmethod
    def get_all_certifications(cls):

        cls.load()

        return sorted({

            value["standard"]

            for value in cls._repository.values()

        })

    # --------------------------------------------------

    @classmethod
    def total_certifications(cls):

        cls.load()

        return len(

            cls.get_all_certifications()

        )