"""
============================================================
RecruitOS
Job Description Model
Version : 0.6
Author  : Tamilvanan A
============================================================
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobDescription:

    job_title: str = ""

    client_name: str = ""

    experience: str = ""

    location: str = ""

    mandatory_skills: list = field(default_factory=list)

    preferred_skills: list = field(default_factory=list)

    responsibilities: list = field(default_factory=list)

    education: str = ""

    created_date: datetime = field(default_factory=datetime.now)

    def display(self):

        print("\n========== Job Description ==========")

        print("Job Title :", self.job_title)

        print("Client :", self.client_name)

        print("Experience :", self.experience)

        print("Location :", self.location)

        print("\nMandatory Skills")

        for skill in self.mandatory_skills:
            print("•", skill)

        print("\nPreferred Skills")

        for skill in self.preferred_skills:
            print("•", skill)

        print("=====================================")