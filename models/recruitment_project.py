"""
============================================================
RecruitOS - AI Recruitment Platform
Module      : Recruitment Project Model
Version     : 0.4.0
Author      : Tamilvanan A

Description:
Represents a hiring project inside RecruitOS.
============================================================
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RecruitmentProject:

    project_name: str = ""

    client_name: str = ""

    job_title: str = ""

    hiring_manager: str = ""

    location: str = ""

    target_headcount: int = 0

    uploaded_resumes: int = 0

    processed_resumes: int = 0

    shortlisted: int = 0

    rejected: int = 0

    interviewed: int = 0

    offered: int = 0

    joined: int = 0

    created_date: datetime = field(default_factory=datetime.now)

    status: str = "Open"

    def summary(self):

        return {
            "Project": self.project_name,
            "Client": self.client_name,
            "Role": self.job_title,
            "Target HC": self.target_headcount,
            "Uploaded": self.uploaded_resumes,
            "Processed": self.processed_resumes,
            "Shortlisted": self.shortlisted,
            "Rejected": self.rejected,
            "Interviewed": self.interviewed,
            "Offered": self.offered,
            "Joined": self.joined,
            "Status": self.status,
        }

    def display(self):

        print("\n========== Recruitment Project ==========")

        for key, value in self.summary().items():
            print(f"{key:<15}: {value}")

        print("========================================")