# RecruitOS — Master Project Specification

## 1. Project information

- **Project:** RecruitOS — AI Resume Screening & Recruitment Platform
- **Owner:** Tamilvanan A
- **Technology:** Python, Streamlit, pandas, SQLite, PyMuPDF, python-docx, openpyxl
- **Repository branch:** `main`
- **Audit source baseline:** Git HEAD `c94e34e` — `Sprint 5.6.0: Integrated master data into Resume Parser`
- **Current stabilized version:** `0.6.1`
- **Current milestone:** `5.6.A — Audit Remediation & Codebase Stabilization`
- **Status:** Active development; core screening pipeline is now wired end-to-end, while reporting, persistence/UI maturity, authentication, and deployment hardening remain future work.

## 2. Product objective

RecruitOS accepts a Job Description, an optional supplemental Skill List, and one or more resumes. It extracts structured candidate/JD data, standardizes configured master data, performs deterministic matching, calculates configuration-driven weighted scores, assigns recommendations, ranks candidates, and displays results.

## 3. Source-of-truth hierarchy

1. This `PROJECT_SPEC.md` defines product scope and current architecture decisions.
2. `ARCHITECTURE.md` defines technical boundaries and dependency direction.
3. `docs/CODEBASE_MAP.md` maps files to responsibilities.
4. `ROADMAP.md` defines remaining milestones.
5. `CHANGELOG.md` records completed changes.
6. `Master_Data/RecruitOS_Configuration.xlsx` is the business/master-data source of truth.
7. Source code is authoritative for implementation details when documentation and code conflict; such conflicts must be corrected immediately.

## 4. Functional workflow

### 4.1 Inputs

Required:
- Job Description: PDF, DOCX, or TXT
- One or more resumes: PDF, DOCX, or TXT

Optional:
- Supplemental Skill List: XLSX, CSV, or TXT

### 4.2 Processing flow

1. Validate and safely store uploads under `uploads/`.
2. Read documents through `DocumentManager`.
3. Clean/extract text through `ExtractionService`.
4. Parse JD through `JDParser`.
5. Parse resumes through `ResumeParser`.
6. Standardize Skills, Education, Certifications, and other configured values through repositories backed by the central workbook.
7. Supplement JD mandatory skills with the optional Skill List when supplied.
8. Run modular matchers.
9. Calculate weighted score from the `Scoring` sheet.
10. Resolve recommendation from the `Recommendation` sheet.
11. Rank candidates by overall match percentage.
12. Display results in Streamlit.

## 5. Core domain contracts

### Candidate
Authoritative model: `models/candidate.py`.

Key fields:
- personal/contact information
- total experience
- education
- certifications
- technical skills
- resume metadata/raw text

### JobDescription
Authoritative model: `JD/jd_model.py`.

`models/job_description.py` is only a compatibility re-export and must not define a second model.

### MatchResult
Authoritative model: `models/match_result.py`.

Contains:
- matched/missing mandatory and preferred skills
- experience/education/certification/keyword results
- component scores
- weighted score breakdown
- overall score
- recommendation
- rank
- explicit shortlist flag/status

## 6. Configuration architecture

The single authoritative workbook is:

`Master_Data/RecruitOS_Configuration.xlsx`

Required sheets:
- Skills
- Education
- Certifications
- Companies
- Locations
- Domains
- Languages
- Roles
- Industries
- Scoring
- Recommendation
- Configuration

Rules:
- Do not hardcode business master data in Python.
- Scoring weights must come from the Scoring sheet.
- Recommendation ranges must come from the Recommendation sheet.
- Runtime shortlisting threshold, when used, must come from Configuration (`Shortlist Minimum Score`).
- The workbook generator creates **structure only** and must not overwrite an existing workbook unless explicitly forced; forced replacement creates a backup first.

## 7. Matching rules currently implemented

- Mandatory skill score = matched mandatory skills / mandatory skills.
- Preferred skills are reported separately and do not silently add bonus points.
- Experience: full score when minimum experience is met; proportional score below minimum; no penalty for exceeding maximum.
- Education: full score when at least one standardized required education value matches; full neutral score if no requirement exists.
- Certifications: proportional required-certification match; full neutral score if no requirement exists.
- Keywords: proportional configured keyword occurrence in resume text; full neutral score if no keywords exist.
- Overall score = weighted component score using the Scoring sheet; active weights must total 100.
- Recommendations use contiguous half-open ranges (`min <= score < max`, final max inclusive) to support decimal scores without gaps.
- Ranking is descending overall score.
- Shortlisting is explicit and configuration-driven; no source-code threshold is allowed.

## 8. Parser rules currently implemented

### Resume
- Name extraction supports names ending in a one-letter initial and rejects contact/section lines.
- Education short aliases such as `BE`/`ME` are case-sensitive to avoid false positives from normal words (`be`, `me`).
- Certification extraction is context-aware and does not scan certification aliases across unrelated skill text.
- Experience extracts explicitly stated total experience; timeline inference is not yet implemented.

### Job Description
- Section-aware parsing prevents Mandatory Skills from consuming Preferred Skills, Education, or Responsibilities.
- Configured aliases are standardized when possible.
- Unknown user-provided requirements are preserved rather than silently discarded.

## 9. Security and data-governance rules

- Candidate resumes, uploaded JDs, generated outputs, logs, and runtime databases are not source-controlled.
- Uploaded filenames are sanitized and saved with collision-resistant identifiers.
- Path traversal through uploaded names is blocked by using basename-only sanitized names.
- CORS/XSRF protections are not disabled by project configuration.
- Tests must use temporary databases/files rather than production project data.

## 10. Testing standard

Primary command:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Rules:
- Tests must be noninteractive.
- Tests must contain assertions.
- Missing fixtures/files must fail instead of silently producing empty documents.
- Database tests must use temporary databases.
- Core imports/configuration must pass a clean-clone smoke test.

## 11. Implemented vs remaining scope

### Implemented/stabilized
- central configuration/repositories
- PDF/DOCX/TXT document contract
- resume parsing foundation
- section-aware JD parsing
- skill/education/certification standardization
- modular matching
- keyword matcher
- configuration-driven score calculator
- recommendation resolution with decimal coverage
- candidate ranking
- end-to-end ProcessingService
- Streamlit screening/results wiring
- safe runtime upload storage
- assertion-based automated test suite

### Remaining for v1.0
- production-grade report/export engine
- candidate/project persistence integration into UI workflow
- configuration management/validation UI
- authentication/authorization and role model
- advanced experience timeline extraction
- richer domain/role/company/location extraction
- analytics dashboard
- production deployment/observability/security review
- formal data-retention/privacy controls
