# RecruitOS Changelog

## 0.6.1 — Milestone 5.6.A Audit Remediation & Stabilization — 24-Jul-2026

### Fixed
- Clean-clone import failure caused by plural/empty `skills_extractor.py` versus singular `skill_extractor.py`.
- Candidate name contract mismatch (`full_name` vs `name`).
- Name extraction for names ending in single-letter initials.
- Education `ME`/`BE` false positives caused by case-insensitive short aliases.
- Certification false positives caused by scanning certification aliases across all resume text.
- JD section bleed that incorrectly treated Preferred Skills/Education/Responsibilities as mandatory skills.
- Missing-file readers silently returning empty text.
- `SUPPORTED_EXTENSIONS` configuration drift.
- Hardcoded version strings across app/UI.
- Recommendation decimal-score gaps.
- Legacy MatchingEngine writing undeclared MatchResult attributes and hardcoded thresholds.

### Added
- Central configuration schema validation.
- ConfigurationRepository and LocationRepository.
- KeywordMatcher, ScoreCalculator, MatchingOrchestrator.
- Optional Skill List processing.
- End-to-end ProcessingService matching/ranking with per-resume failure isolation.
- Streamlit Analyze → backend → Results integration.
- Safe upload filenames and runtime upload directories.
- CI workflow and assertion-based unittest suite.
- Project documentation baseline and codebase map.

### Changed
- Modular matching architecture is now authoritative; legacy MatchingEngine is a facade.
- JobDescription has one authoritative model.
- Central configuration workbook includes migrated legacy skill/certification data and continuous recommendation ranges.
- Runtime DB/log/upload/resume data is excluded from source-control workflow.
- Configuration workbook generator creates structure only, protects existing workbook, and backs up before forced replacement.

### Removed from stabilized source package
- Candidate/resume PDF data.
- Runtime SQLite database and logs.
- Legacy separate master workbooks after relevant populated data migration.
- Empty obsolete placeholder modules replaced by current architecture.
