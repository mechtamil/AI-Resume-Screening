# RecruitOS Roadmap

## Current baseline

- **Version:** `0.7.5`
- **Completed sprint:** `5.7.1C-R1 — Universal Intake Templates & Guided Workspace UX`
- **Database schema:** `5`
- **Deployment target:** Streamlit development environment

## Completed platform foundation

- `5.6.A` — audited remediation and stabilized parsing/matching baseline
- `5.7.0` — ranked Excel report engine
- `5.7.1` — project, candidate and screening-session persistence
- `5.7.1A` — multi-user identity and database isolation
- `5.7.1A-R1` — admin provisioning, RBAC and ALTEN experience
- `5.7.1B` — secure upload, temporary-file and export isolation
- `5.7.1B-R1` — clean repository rebaseline and deployment guardrails
- `5.7.1C` — tenant-specific configuration versions, cache isolation and screening provenance
- `5.7.1C-R1` — multi-format intake, OCR, Excel templates, guided navigation and sidebar/home UX

## Next platform sprint

### 5.7.1D — Explicit Reader Sharing & Review Assignment

- private-by-default project sharing
- Reader and reviewer assignment
- read-only evidence views
- expiry and revocation
- backend ownership/share authorization
- sharing audit trail
- cross-user sharing denial/allowance tests

## AI-powered screening milestone

The deterministic matching engine remains authoritative and traceable. AI adds structured evidence, semantic retrieval and recruiter assistance; it does not silently replace mandatory rules or auto-reject candidates.

### 5.7.2A — AI Provider Gateway & Model Registry
- local/hosted provider abstraction
- tenant model policy
- secret-safe provider configuration
- structured-output validation
- latency/cost/error telemetry
- model and prompt version registry

### 5.7.2B — AI Structured Resume/JD Extraction
- section-specific extraction schemas
- evidence and source-section mapping
- deterministic/AI conflict detection
- multilingual-ready text handling
- confidence and human correction workflow

### 5.7.2C — Embeddings & Hybrid Retrieval
- tenant-isolated vector indexes
- keyword + taxonomy + semantic retrieval
- fusion and reranking
- small-to-big resume retrieval
- large-candidate-pool benchmarks

### 5.7.2D — Explainable AI Screening
- role-specific evaluation packs
- evidence-grounded assessment
- confidence and uncertainty
- deterministic score shown separately
- human review and override

### 5.7.2E — Alternative Role Intelligence
- configurable role taxonomy
- TF-IDF/SVM baseline
- embedding and supervised-model comparison
- top-K adjacent-role recommendations
- transferable-skill evidence

### 5.7.2F — Recruiter Copilot & Interview Intelligence
- authorized candidate search and comparison
- ranking explanations
- evidence-grounded recruiter Q&A
- candidate-specific interview questions
- no cross-tenant retrieval

### 5.7.2G — AI Safety, Fairness & Evaluation
- prompt-injection and hidden-text detection
- repeated-run variance testing
- benchmark datasets and confusion matrices
- bias/fairness review
- model approval, rollback and audit metadata

## Production hardening

### 5.8.0 — Privacy, Retention & Audit Operations
### 5.8.1 — Advanced Parsing & Matching Quality
### 5.8.2 — Production Database, Object Storage & Concurrency
### 5.9.0 — Private Analytics, Localization & Global UX
### 5.9.1 — v1.0 Release Candidate

## Current estimate

After acceptance of `5.7.1C-R1`, **11 focused sprints** remain in the expanded platform + AI v1.0 scope. Scope changes require an explicit roadmap update.
