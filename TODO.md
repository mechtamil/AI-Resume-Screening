# RecruitOS Engineering Backlog

## P0 — Keep green

- [ ] Keep the complete automated suite passing.
- [ ] Keep public self-registration disabled.
- [ ] Require SecurityContext and backend ownership filters for protected records.
- [ ] Never export permanent passwords or password hashes.
- [ ] Never commit CVs, uploads, runtime databases, logs, temporary files or generated reports.
- [x] Rebaseline Git from a policy-validated clean source package.
- [x] Add CI repository-policy, preflight, test and compilation gates.
- [ ] Keep configuration scoring total at 100 and recommendation ranges continuous.

## Completed product-experience corrections

- [x] Common text, spreadsheet, PDF and image/OCR input support.
- [x] JD and supplemental-skill Excel templates.
- [x] Mandatory/Preferred supplemental skill classification.
- [x] Guided page-to-page workflow actions.
- [x] Action-oriented home dashboard, dark mode, compact sidebar identity and bottom sign-out.

## P1 — Required before global production

- [x] Sprint 5.7.1B: isolate uploads, temporary files and exports by tenant/user/session.
- [x] Sprint 5.7.1C: tenant-specific configuration, immutable versions, cache isolation and screening snapshots.
- [ ] Sprint 5.7.1D: explicit Reader sharing and revocation.
- [ ] Implement production email/identity-provider password reset.
- [ ] Add MFA/enterprise SSO roadmap implementation.
- [ ] Add production database, concurrency and observability.
- [ ] Add privacy retention, audit viewer and data lifecycle controls.

## P2 — AI-powered screening foundation

- [ ] Sprint 5.7.2A: AI provider gateway and model registry.
- [ ] Sprint 5.7.2B: schema-validated AI resume/JD extraction with evidence.
- [ ] Sprint 5.7.2C: tenant-isolated embeddings and hybrid retrieval.
- [ ] Sprint 5.7.2D: explainable AI screening and human review.
- [ ] Sprint 5.7.2E: alternative-role intelligence.
- [ ] Sprint 5.7.2F: recruiter copilot and interview intelligence.
- [ ] Sprint 5.7.2G: prompt-injection, hidden-text, variance and fairness evaluation.

## P3 — Product quality

- [ ] Advanced experience timeline extraction.
- [ ] Stronger domain, role, company and location extraction.
- [ ] Private analytics, search, filters and pagination.
- [ ] Localization and time-zone presentation.

## P4 — Integrations

- [ ] Enterprise identity provider / Microsoft Entra ID.
- [ ] ATS integration.
- [ ] Controlled email/calendar workflows.
