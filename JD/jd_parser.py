"""Section-aware, master-data-aware Job Description parser."""
from __future__ import annotations

import re
from typing import Any

from JD.jd_model import JobDescription
from parser.extractors.certification_extractor import CertificationExtractor
from parser.extractors.education_extractor import EducationExtractor
from parser.extractors.skill_extractor import SkillExtractor
from services.certification_repository import CertificationRepository
from services.education_repository import EducationRepository
from services.skill_repository import SkillRepository


class JDParser:
    EXPERIENCE_PATTERN = re.compile(
        r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:to|\-|–)?\s*(\d+(?:\.\d+)?)?\s*\+?\s*(?:years?|yrs?)",
        re.I,
    )

    HEADER_ALIASES = {
        "mandatory_skills": {
            "mandatory skills", "required skills", "must have skills", "must-have skills",
            "key skills", "technical skills", "skills required",
        },
        "preferred_skills": {
            "preferred skills", "good to have skills", "good-to-have skills", "desired skills",
            "optional skills", "nice to have", "nice-to-have",
        },
        "education": {"education", "qualification", "qualifications", "educational qualification"},
        "certifications": {"certifications", "certification", "required certifications"},
        "responsibilities": {
            "responsibilities", "roles and responsibilities", "key responsibilities", "job responsibilities",
        },
        "keywords": {"keywords", "key words"},
        "notes": {"notes", "additional information", "other requirements"},
    }

    LABEL_PATTERNS = {
        "job_title": re.compile(r"(?im)^\s*(?:job\s*title|position|role)\s*[:\-]\s*(.+?)\s*$"),
        "company_name": re.compile(r"(?im)^\s*(?:company|client|organization)\s*[:\-]\s*(.+?)\s*$"),
        "location": re.compile(r"(?im)^\s*(?:location|work location)\s*[:\-]\s*(.+?)\s*$"),
        "employment_type": re.compile(r"(?im)^\s*(?:employment type|job type)\s*[:\-]\s*(.+?)\s*$"),
    }

    @classmethod
    def _normalize_header(cls, line: str) -> str:
        value = re.sub(r"^[\s#*•\-]+|[\s:;\-]+$", "", line or "").strip().casefold()
        return re.sub(r"\s+", " ", value)

    @classmethod
    def _header_key(cls, line: str) -> str | None:
        normalized = cls._normalize_header(line)
        for key, aliases in cls.HEADER_ALIASES.items():
            if normalized in aliases:
                return key
        return None

    @classmethod
    def _extract_sections(cls, text: str) -> dict[str, list[str]]:
        sections = {key: [] for key in cls.HEADER_ALIASES}
        current: str | None = None
        for raw_line in (text or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            header = cls._header_key(line)
            if header:
                current = header
                continue
            # A labelled metadata line terminates a free-form section.
            if any(pattern.match(line) for pattern in cls.LABEL_PATTERNS.values()):
                current = None
                continue
            if current:
                sections[current].append(line)
        return sections

    @staticmethod
    def _clean_item(value: str) -> str:
        value = re.sub(r"^[\s•*\-–—\d.)]+", "", value or "").strip()
        return value.strip(" ;,|\t")

    @classmethod
    def _split_items(cls, lines: list[str]) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()
        for line in lines:
            for part in re.split(r"[;,|]", line):
                item = cls._clean_item(part)
                key = item.casefold()
                if item and key not in seen:
                    seen.add(key)
                    output.append(item)
        return output

    @staticmethod
    def _dedupe(values: list[str]) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = str(value or "").strip()
            key = cleaned.casefold()
            if cleaned and key not in seen:
                seen.add(key)
                output.append(cleaned)
        return output

    @classmethod
    def _standardize_skills(cls, lines: list[str]) -> list[str]:
        repo = SkillRepository()
        output: list[str] = []
        for item in cls._split_items(lines):
            exact = repo.find_standard_skill(item)
            if exact:
                output.append(exact)
                continue
            configured_matches = SkillExtractor.extract(item)
            output.extend(configured_matches if configured_matches else [item])
        return cls._dedupe(output)

    @classmethod
    def _standardize_education(cls, lines: list[str]) -> list[str]:
        if not lines:
            return []
        repo = EducationRepository()
        text = "\n".join(lines)
        extracted = EducationExtractor.extract(text)
        output = list(extracted)
        for item in cls._split_items(lines):
            standard = repo.find_standard_degree(item)
            embedded = EducationExtractor.extract(item)
            if standard:
                output.append(standard)
            elif embedded:
                output.extend(embedded)
            elif not any(item.casefold() == existing.casefold() for existing in output):
                output.append(item)
        return cls._dedupe(output)

    @classmethod
    def _standardize_certifications(cls, lines: list[str]) -> list[str]:
        if not lines:
            return []
        repo = CertificationRepository()
        text = "\n".join(lines)
        output = CertificationExtractor.extract(text)
        for item in cls._split_items(lines):
            standard = repo.find_standard_certification(item)
            embedded = CertificationExtractor.extract("Certifications\n" + item)
            if standard:
                output.append(standard)
            elif embedded:
                output.extend(embedded)
            elif not any(item.casefold() == existing.casefold() for existing in output):
                output.append(item)
        return cls._dedupe(output)

    @classmethod
    def parse(cls, document: dict[str, Any] | None) -> JobDescription:
        jd = JobDescription()
        if not document:
            return jd

        jd.source_file = str(document.get("file_name", "") or "").strip()
        jd.raw_text = str(document.get("text", "") or "").strip()
        text = jd.raw_text
        if not text:
            return jd

        for field_name, pattern in cls.LABEL_PATTERNS.items():
            match = pattern.search(text)
            if match:
                setattr(jd, field_name, match.group(1).strip())

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not jd.job_title and lines:
            for line in lines[:10]:
                normalized = cls._normalize_header(line)
                if normalized in {"job description", "jd", "position description"}:
                    continue
                if cls._header_key(line) or any(p.match(line) for p in cls.LABEL_PATTERNS.values()):
                    continue
                jd.job_title = line
                break

        experience = cls.EXPERIENCE_PATTERN.search(text)
        if experience:
            jd.experience_min = float(experience.group(1))
            jd.experience_max = float(experience.group(2) or experience.group(1))

        sections = cls._extract_sections(text)
        jd.mandatory_skills = cls._standardize_skills(sections["mandatory_skills"])
        jd.preferred_skills = cls._standardize_skills(sections["preferred_skills"])
        jd.education = cls._standardize_education(sections["education"])
        jd.certifications = cls._standardize_certifications(sections["certifications"])
        jd.responsibilities = cls._dedupe([cls._clean_item(v) for v in sections["responsibilities"]])
        jd.keywords = cls._split_items(sections["keywords"])
        jd.notes = "\n".join(sections["notes"]).strip()
        return jd
