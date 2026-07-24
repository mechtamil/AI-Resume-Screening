
"""
============================================================
RecruitOS - AI Recruitment Platform
Module      : Resume Model
Author      : Tamilvanan A

Description:
Defines the Resume object used throughout RecruitOS.
============================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib


@dataclass
class Resume:
    """
    Represents an uploaded resume.
    """

    file_name: str = ""
    file_path: str = ""
    file_type: str = ""

    file_size: int = 0

    page_count: int = 0

    word_count: int = 0

    character_count: int = 0

    extracted_text: str = ""

    uploaded_time: datetime = field(default_factory=datetime.now)

    file_hash: str = ""

    status: str = "Pending"

    def calculate_statistics(self):
        """
        Calculate word and character statistics.
        """

        self.word_count = len(self.extracted_text.split())

        self.character_count = len(self.extracted_text)

    def generate_hash(self):
        """
        Generate SHA256 hash for duplicate detection.
        """

        if self.file_path and Path(self.file_path).exists():

            with open(self.file_path, "rb") as file:

                self.file_hash = hashlib.sha256(
                    file.read()
                ).hexdigest()

    def mark_processed(self):

        self.status = "Processed"

    def mark_failed(self):

        self.status = "Failed"

    def summary(self):
        """
        Return Resume Summary
        """

        return {
            "File Name": self.file_name,
            "File Type": self.file_type,
            "File Size (KB)": round(self.file_size / 1024, 2),
            "Pages": self.page_count,
            "Words": self.word_count,
            "Characters": self.character_count,
            "Status": self.status,
            "Uploaded": self.uploaded_time.strftime("%d-%b-%Y %I:%M %p")
        }

    def display(self):

        print("\n========== Resume Information ==========")

        print(f"File Name      : {self.file_name}")

        print(f"File Type      : {self.file_type}")

        print(f"File Size      : {round(self.file_size / 1024,2)} KB")

        print(f"Pages          : {self.page_count}")

        print(f"Words          : {self.word_count}")

        print(f"Characters     : {self.character_count}")

        print(f"Status         : {self.status}")

        print(f"Uploaded Time  : {self.uploaded_time}")

        print(f"Hash           : {self.file_hash[:15]}...")

        print("========================================")
