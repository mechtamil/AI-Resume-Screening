# RecruitOS

RecruitOS is a configuration-driven AI Resume Screening & Recruitment Platform under active development.

## Current version

`0.6.1` — Milestone `5.6.A Audit Remediation & Stabilization`

## Current working workflow

1. Upload a Job Description (PDF/DOCX/TXT).
2. Optionally upload a supplemental Skill List (XLSX/CSV/TXT).
3. Upload one or more resumes.
4. RecruitOS parses and standardizes JD/candidate data.
5. Modular matchers calculate component scores.
6. Scoring weights and recommendations are read from `Master_Data/RecruitOS_Configuration.xlsx`.
7. Candidates are ranked and displayed in Results.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m tools.preflight
python -m unittest discover -s tests -p "test_*.py" -v
streamlit run app.py
```

On Linux/macOS, use the appropriate virtual-environment activation command.

## Configuration

The authoritative workbook is:

`Master_Data/RecruitOS_Configuration.xlsx`

See `Master_Data/README.md` before editing or regenerating it.

## Documentation

- `PROJECT_SPEC.md` — source-of-truth product specification
- `ARCHITECTURE.md` — technical architecture and dependency rules
- `ROADMAP.md` — remaining v1.0 development plan
- `CHANGELOG.md` — implementation history
- `TODO.md` — prioritized backlog
- `docs/CODEBASE_MAP.md` — file/module responsibility map
- `docs/AUDIT_2026-07-24.md` — original deep audit baseline
- `docs/AUDIT_REMEDIATION_5.6.A.md` — remediation record

## Data privacy

Do not commit resumes, candidate PII, runtime databases, logs, or uploaded files. The `.gitignore` is configured to keep runtime data out of normal source control.
