# RecruitOS Roadmap

## Completed baseline

### 5.5.x — Configuration & Repository Framework
Central workbook and domain repositories.

### 5.6.0 / 5.6.A — Parser Integration, Audit Remediation & Stabilization
Clean-clone reproducibility, parser fixes, modular matching, score/recommendation integration, end-to-end processing, tests and documentation.

### 5.7.0 — Report & Export Engine
Ranked Excel report and Results download integration.

### 5.7.1 — Persistence Integration
Private projects, sessions, candidates and MatchResult persistence/reopening.

### 5.7.1A — Multi-User Identity & Database Isolation
Server-side authentication sessions, SecurityContext and private owner-scoped repositories.

### 5.7.1A-R1 — Admin-Provisioned Identity, RBAC & ALTEN Experience
- public registration removed
- User ID/password login and Forgot Password request
- one-time System Owner bootstrap
- five-role RBAC model
- single-user and Excel bulk provisioning
- optional Time Zone
- configurable seven-day temporary credential
- mandatory first-login password change
- User Access Master and one-time temporary credential exports
- role/status/reset administration and audit records
- schema version 4
- premium responsive ALTEN-aligned theme and animations

## Remaining to v1.0

### 5.7.1B — Secure File & Export Isolation — **Completed**
- tenant/user/session-scoped JD, resume and skill-list paths
- owner-authorized file retrieval, listing and project-workspace deletion
- private temporary processing directories and cleanup
- private report-generation/output paths
- SHA-256 file metadata and randomized stored names
- cross-user file access, listing and deletion denial tests

### 5.7.1B-R1 — Repository Rebaseline & Deployment Guardrails — **Completed**
- comprehensive Git ignore and line-ending policy
- secrets/runtime/private-data repository guard
- deterministic source-only release package builder
- SHA-256 source manifest
- GitHub quality workflow
- fail-closed public System Owner bootstrap
- fresh repository cutover procedure

### 5.7.1C — Tenant Configuration Management — **Next**
- system default versus tenant configuration
- tenant-aware repository/cache construction
- workbook upload, validation, backup and versioning
- configuration snapshot per screening

### 5.7.1D — Controlled Sharing & Reader Workflow
- explicit project/session/report shares
- read-only Reader assignments
- share expiry and revocation
- audit records and access tests

### 5.8.0 — Audit, Privacy & Retention
- admin audit viewer
- retention/deletion policies
- user data export and deactivation lifecycle
- break-glass access design

### 5.8.1 — Advanced Parsing & Matching Quality
- employment timeline experience
- stronger domain/role/company/location normalization
- advanced preferred-skill and education semantics

### 5.8.2 — Production Database, Concurrency & Reliability
- production database strategy
- concurrent-user and batch processing
- structured observability, recovery and performance tests

### 5.9.0 — Private Analytics & Global UX
- owner-scoped analytics and funnel
- search/filter/pagination
- localization/time-zone presentation

### 5.9.1 — v1.0 Release Candidate
- full security, regression and acceptance suite
- dependency lock and deployment runbooks
- release notes, version tag and deployment smoke test

## Current estimate

After acceptance of `5.7.1B-R1`, **7 focused sprints** remain in the current v1.0 scope. Changes require an explicit roadmap update.
