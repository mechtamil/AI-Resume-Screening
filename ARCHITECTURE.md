# RecruitOS Architecture

## 1. Layered architecture

```text
Streamlit UI
  app.py / ui/*
        |
        v
Application Services
  UploadService
  ProcessingService
        |
        +-----------------------------+
        |                             |
        v                             v
Document/Parsing                 Matching
DocumentManager                  MatchingOrchestrator
ExtractionService                 |- SkillMatcher
JDParser                          |- ExperienceMatcher
ResumeParser                      |- EducationMatcher
                                  |- CertificationMatcher
                                  |- KeywordMatcher
                                  |- ScoreCalculator
                                         |
                                         v
                                 RecommendationRepository
        |
        v
Domain Models
Candidate / JobDescription / MatchResult
        |
        v
Configuration & Data Access
MasterRepository -> domain repositories -> RecruitOS_Configuration.xlsx
```

## 2. Dependency rules

- UI may call application services; UI must not parse files or calculate scores directly.
- `ProcessingService` is the application workflow coordinator.
- `DocumentManager` owns reader selection and returns one standardized document dictionary.
- Parsers produce domain models only.
- Matching components consume domain models and must not read files/workbooks directly.
- Repositories access master/config data only through `MasterRepository`.
- `MasterRepository` is the only central-workbook loading/caching layer.
- Business values belong in `RecruitOS_Configuration.xlsx`, not source constants.

## 3. Authoritative models

- Candidate: `models/candidate.py`
- JobDescription: `JD/jd_model.py`
- MatchResult: `models/match_result.py`

`models/job_description.py` is a compatibility re-export only.

## 4. Runtime data boundaries

Source-controlled:
- source code
- tests
- documentation
- central configuration workbook template/baseline
- synthetic text fixtures

Not source-controlled:
- uploaded resumes/JDs
- runtime SQLite databases
- logs
- generated reports/output
- temporary files

Runtime upload locations:
- `uploads/job_descriptions/`
- `uploads/resumes/`
- `uploads/skill_lists/`

## 5. Configuration path

```text
RecruitOS_Configuration.xlsx
       |
       v
MasterRepository (load/cache/schema validation)
       |
       +-> SkillRepository
       +-> EducationRepository
       +-> CertificationRepository
       +-> LocationRepository
       +-> ScoringRepository
       +-> RecommendationRepository
       +-> ConfigurationRepository
```

## 6. End-to-end screening path

```text
JD + Resumes + optional Skill List
             |
             v
        UploadService
             |
             v
      ProcessingService
       /           \
      v             v
 JDParser       ResumeParser
      \             /
       v           v
   JobDescription Candidate(s)
          \       /
           v     v
    MatchingOrchestrator
             |
             v
     ScoreCalculator
             |
             v
 RecommendationRepository
             |
             v
 Ranked MatchResult list
             |
             v
        Results UI
```

## 7. Matching architecture decision

The modular matching package under `services/matching/` is authoritative.

`services/matching_engine.py` exists only as a compatibility facade and delegates to `MatchingOrchestrator`. No independent scoring/recommendation logic is allowed there.

## 8. Recommendation range semantics

To support decimal scores, configured ranges are treated as half-open:

- `minimum <= score < maximum`
- highest/final maximum is inclusive

Example: `0-60`, `60-75`, `75-90`, `90-100` covers every value from 0 through 100 without overlap or decimal gaps.

## 9. Error handling

- Missing documents raise `FileNotFoundError`.
- Corrupt/unreadable PDF/DOCX/TXT errors propagate with context.
- One resume failure is isolated by `ProcessingService`; remaining resumes continue.
- Invalid configuration fails fast rather than silently falling back to hidden defaults.
