"""
============================================================
RecruitOS
Job Description Parser
Version : 1.0
Author  : Tamilvanan A

Description:
Parses a processed Job Description document into a
JobDescription model.
============================================================
"""

import re
from JD.jd_model import JobDescription


class JDParser:
    """
    Parses a processed document dictionary into
    a JobDescription object.
    """

    EXPERIENCE_PATTERN = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:to|-)?\s*(\d+(?:\.\d+)?)?\s*(?:years|yrs|year)",
        re.IGNORECASE
    )

    @classmethod
    def parse(cls, document: dict) -> JobDescription:

        jd = JobDescription()

        jd.source_file = document.get("file_name", "")
        jd.raw_text = document.get("text", "")

        text = jd.raw_text

        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        # -----------------------------
        # Job Title
        # -----------------------------
        if lines:
            jd.job_title = lines[0]

        # -----------------------------
        # Experience
        # -----------------------------
        experience = cls.EXPERIENCE_PATTERN.search(text)

        if experience:

            jd.experience_min = float(experience.group(1))

            if experience.group(2):
                jd.experience_max = float(experience.group(2))
            else:
                jd.experience_max = jd.experience_min

        # -----------------------------
        # Skills
        # -----------------------------
        skill_headers = {
            "skills",
            "technical skills",
            "mandatory skills",
            "required skills"
        }

        current_section = None

        for line in lines:

            lower = line.lower()

            if lower in skill_headers:
                current_section = "skills"
                continue

            if current_section == "skills":

                if ":" in line:
                    continue

                if len(line) < 2:
                    continue

                jd.mandatory_skills.append(line)

        # Remove duplicates

        jd.mandatory_skills = sorted(
            list(set(jd.mandatory_skills))
        )

        return jd