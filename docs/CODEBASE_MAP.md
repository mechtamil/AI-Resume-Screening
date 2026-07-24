# RecruitOS Codebase Map

This map is the operational reference for what each file/folder owns. Before adding or changing behavior, check the owning module here to avoid duplicate implementations.

## Root

| Path | Responsibility |
|---|---|
| `app.py` | Streamlit entry point and page routing only |
| `VERSION` | Single application semantic version value |
| `requirements.txt` | Python runtime dependencies |
| `PROJECT_SPEC.md` | Product/source-of-truth specification |
| `ARCHITECTURE.md` | Technical boundaries/dependency direction |
| `ROADMAP.md` | Remaining milestone plan |
| `CHANGELOG.md` | Release/change history |
| `TODO.md` | Prioritized backlog |
| `.gitignore` | Runtime/private/generated-data exclusion policy |
| `.streamlit/config.toml` | Streamlit server/theme configuration |
| `.devcontainer/devcontainer.json` | Development container definition |
| `.github/workflows/tests.yml` | CI unit-test workflow |

## `config/`

| File | Responsibility |
|---|---|
| `config/paths.py` | Single filesystem-path authority; runtime directory creation |
| `config/settings.py` | App metadata, version loading, file types, upload limits, compatibility aliases |
| `config/sheet_names.py` | Central workbook sheet names and structural required columns |
| `config/__init__.py` | Package marker |

Do not create new independent path/version/scoring-constant modules. Business scoring values belong in Excel.

## `Master_Data/`

| File | Responsibility |
|---|---|
| `RecruitOS_Configuration.xlsx` | Single authoritative master/config/business-rule workbook |
| `README.md` | Workbook governance and generation instructions |

Legacy separate master workbooks are retired.

## `services/` — application/data services

| File | Responsibility |
|---|---|
| `base_repository.py` | Shared DataFrame normalization/filter/search helpers |
| `master_repository.py` | Central workbook load/cache/schema validation |
| `skill_repository.py` | Skill names/categories/synonyms/normalization |
| `education_repository.py` | Degree/alias/priority normalization |
| `certification_repository.py` | Certification/alias/category normalization |
| `location_repository.py` | Configured location search values |
| `scoring_repository.py` | Active score-component weights |
| `recommendation_repository.py` | Score-range recommendation rules and coverage |
| `configuration_repository.py` | Generic Key/Value application settings from workbook |
| `document_manager.py` | Reader selection and standardized processed-document contract |
| `extraction_service.py` | Text cleanup, basic section detection, metadata |
| `upload_service.py` | Safe runtime upload persistence and filename sanitation |
| `skill_list_service.py` | Optional Skill List ingestion/normalization |
| `processing_service.py` | End-to-end application workflow coordinator |
| `matching_engine.py` | Backward-compatible facade only; delegates to modular orchestrator |
| `logger.py` | Logging setup |

## `services/matching/` — authoritative matching engine

| File | Responsibility |
|---|---|
| `matching_orchestrator.py` | Runs all matchers, scoring, recommendation, shortlist state, ranking entry point |
| `skill_matcher.py` | Mandatory/preferred/additional skill comparison |
| `experience_matcher.py` | Minimum-experience score/match logic |
| `education_matcher.py` | Standardized education comparison |
| `certification_matcher.py` | Required certification comparison |
| `keyword_matcher.py` | JD keyword occurrence comparison |
| `score_calculator.py` | Weighted overall score from ScoringRepository |
| `__init__.py` | Exposes MatchingOrchestrator |

Do not add scoring/recommendation thresholds to individual matchers.

## `parser/`

| File | Responsibility |
|---|---|
| `pdf_reader.py` | PDF text extraction; raises on missing/corrupt input |
| `docx_reader.py` | DOCX text extraction; raises on missing/corrupt input |
| `txt_reader.py` | TXT text extraction |
| `resume_parser.py` | Processed resume dictionary → Candidate |
| `__init__.py` | Package marker |

### `parser/extractors/`

| File | Responsibility |
|---|---|
| `personal_extractor.py` | Aggregates name/email/phone/location/social extraction |
| `name_extractor.py` | Candidate-name heuristic |
| `email_extractor.py` | Standalone email extraction utility |
| `phone_extractor.py` | Standalone phone extraction utility |
| `skill_extractor.py` | Configuration-driven skill/alias detection |
| `education_extractor.py` | Configuration-driven education detection with short-alias safeguards |
| `certification_extractor.py` | Context-aware certification detection |
| `__init__.py` | Package marker |

`skills_extractor.py` (plural) is obsolete and must not exist.

### `parser/dictionaries/`

Package retained only for compatibility/organization. Business dictionaries were intentionally removed because central workbook repositories are authoritative.

### `parser/utils/`

Package marker only. Add utilities here only when multiple parser modules genuinely share them.

## `JD/`

| File | Responsibility |
|---|---|
| `jd_model.py` | Authoritative JobDescription dataclass |
| `jd_parser.py` | Section-aware, master-data-aware JD parsing |
| `sample_jd.txt` | Synthetic non-PII parser fixture/example |
| `__init__.py` | Package marker |

No second JD matcher/model should be created here.

## `models/`

| File | Responsibility |
|---|---|
| `candidate.py` | Candidate domain model |
| `match_result.py` | Authoritative matching/result contract |
| `job_description.py` | Compatibility re-export of `JD.jd_model.JobDescription` |
| `resume.py` | Uploaded resume metadata model |
| `recruitment_project.py` | Recruitment-project domain model |
| `__init__.py` | Package marker |

## `database/`

| File | Responsibility |
|---|---|
| `database.py` | SQLite connection and schema bootstrap; path injectable for tests |
| `candidate_repository.py` | Candidate persistence operations |
| `__init__.py` | Package marker |

Runtime `recruitos.db` is not source-controlled. Database persistence is not yet fully integrated into the primary screening workflow.

## `ui/`

| File | Responsibility |
|---|---|
| `home.py` | Home/session summary |
| `resume_screening.py` | Input form/upload/analyze workflow; calls services only |
| `results.py` | Ranked result/score detail presentation |
| `settings.py` | Compatibility export of central app metadata |

Candidate Database/Analytics/Settings product pages remain future scope and must not duplicate backend logic.

## `utils/`

| File | Responsibility |
|---|---|
| `file_utils.py` | File extension/size/validation helpers |
| `__init__.py` | Package marker |

## `tools/`

| File | Responsibility |
|---|---|
| `create_configuration_workbook.py` | Safely creates an empty central workbook structure; protects existing files |
| `create_skill_repository.py` | Deprecated command that exits with migration guidance |
| `__init__.py` | Package marker |

## `tests/`

All `test_*.py` files are standard-library `unittest` tests and must be noninteractive/assertion-based.

High-value regression coverage:
- repository/configuration validation
- clean-clone/core import smoke
- name/education/certification false-positive regressions
- JD section isolation
- document reader error semantics
- matching/scoring/recommendation contracts
- optional skill-list ingestion
- end-to-end parse → match → score → rank → recommend
- database tests use temporary DBs

Run all tests:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

## `Resume/`, `uploads/`, `output/`, `temp/`, `logs/`

Runtime/local-data folders. Only `.gitkeep` should be source-controlled where necessary. Never place committed candidate PII in these directories.

## `reports/`

Reserved for the future report/export implementation. There is currently no authoritative report engine; see ROADMAP 5.7.0.

## Architectural anti-duplication rules

Before creating a new file:
1. Search this map for the responsibility.
2. Extend the owning module when the responsibility already exists.
3. Do not create parallel models, scoring engines, workbook systems, or upload paths.
4. Update this map whenever responsibility moves or a new authoritative module is introduced.
