# Sprint 5.7.1B-R1 — Repository Rebaseline & Deployment Guardrails

## Purpose

Create a source-only RecruitOS baseline that can be uploaded to a fresh Git
repository without historical CVs, databases, logs, caches, secrets, legacy
workbooks or local sprint-package files.

## Included controls

- comprehensive `.gitignore` and `.gitattributes`;
- safe deployment variable example;
- repository-policy CLI and CI gate;
- deterministic source-release builder;
- SHA-256 source manifest inside every clean package;
- fail-closed initial System Owner setup for public/shared deployments;
- automated tests for repository, package and bootstrap security;
- security and contribution guidance.

## Fresh repository principle

A fresh repository must be initialized from the output of:

```powershell
python -m tools.build_clean_release
```

Do not copy the old `.git` directory into the clean source folder. Keep the old
repository only as a local backup bundle until the new GitHub and Streamlit
deployment are accepted.

## Prohibited source-control content

- real resumes, candidate data and uploaded JDs;
- SQLite databases and backups;
- logs, reports, temporary files and uploads;
- `.env`, Streamlit secrets, private keys and certificates;
- `__pycache__`, `.pyc`, test caches and IDE state;
- release ZIPs, package manifests and overlay instructions;
- separate legacy master workbooks.

## Acceptance gate

```powershell
python -m tools.repository_policy --tracked
python -m tools.preflight
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q app.py config database JD models parser reports services tests tools ui utils
python -m tools.build_clean_release
```
