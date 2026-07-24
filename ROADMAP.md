# RecruitOS Roadmap

## Baseline

Audit source: `c94e34e` (`Sprint 5.6.0`).

Milestone `5.6.A` was introduced after the deep audit to stabilize reproducibility, parsing correctness, matching architecture, tests, documentation, and security hygiene before normal feature growth.

## Completed / incorporated into 5.6.A

### 5.5.x — Configuration & repository framework
- central workbook
- MasterRepository / BaseRepository
- Skill / Education / Certification repositories
- Scoring / Recommendation repositories

### 5.6.0 — Resume master-data integration
- ResumeParser integration
- subsequently corrected during 5.6.A

### 5.6.A — Audit Remediation & Stabilization
- clean-clone runtime file contract
- singular SkillExtractor authority
- central workbook migration/baseline
- candidate-name contract fix
- education false-positive protection
- certification context protection
- section-aware JD parsing and master-data normalization
- one authoritative JobDescription model
- modular matching orchestrator
- KeywordMatcher
- ScoreCalculator
- recommendation decimal coverage
- end-to-end ProcessingService and ranking
- Streamlit Analyze/Results wiring
- safe upload storage
- test-suite conversion to automated assertions
- privacy/repository hygiene baseline
- documentation baseline

## Remaining milestones to v1.0

### 5.7 — Product completion

#### 5.7.0 Report & Export Engine
- ranked Excel screening report
- candidate detail sheets / score breakdown
- export from Results UI
- deterministic report tests

#### 5.7.1 Project/Candidate Persistence Integration
- map Candidate/MatchResult/RecruitmentProject to database contracts
- migrations/schema versioning
- save/reopen screening sessions
- candidate database UI

#### 5.7.2 Configuration Management
- workbook validation dashboard
- missing/duplicate/ambiguous master-data diagnostics
- scoring/recommendation configuration validation before analysis
- optional controlled configuration editing/import

### 5.8 — Production hardening

#### 5.8.0 Advanced Parsing & Matching Quality
- employment timeline experience calculation
- domain/role/company/location normalization
- stronger education specialization semantics
- richer preferred-skill handling based on explicit business configuration

#### 5.8.1 Security, Privacy & Auditability
- authentication/authorization
- audit logs
- retention/deletion controls
- secret/config management
- upload malware/content safety strategy

#### 5.8.2 Performance & Reliability
- large batch processing
- progress/cancellation
- performance profiling
- structured logging/observability
- failure recovery

### 5.9 — Release readiness

#### 5.9.0 Analytics & UX
- analytics dashboard
- project metrics
- shortlist funnel
- improved filtering/search

#### 5.9.1 v1.0 Release Candidate
- full regression/acceptance suite
- install/deploy documentation
- dependency lock/reproducible environment
- release notes
- tagging/versioning
- deployment smoke test

## Current estimate

After 5.6.A stabilization: **8 focused sprints** remain in the current v1.0 scope. The count may change only through an explicit scope decision recorded in this roadmap.
