# RecruitOS Changelog

## 0.7.7 — Sprint 5.7.1D Explicit Reader Sharing & Review Assignment

### Added
- Schema version 6 with explicit `record_shares` assignments and owner/recipient indexes.
- Reader and Reviewer project assignments with optional expiry and owner notes.
- Read-only Shared Records workspace for persisted ranking evidence.
- Reviewer progress metadata separated from immutable candidate evidence.
- Owner-side grant, sharing-history and immediate revocation controls.
- Sharing audit events for grant, review, expiry and revocation.
- Cross-user allowance, denial, session-boundary, expiry and revocation tests.

### Changed
- Application version increased to `0.7.7`.
- Standard Users can receive explicit Shared Records access while retaining private-by-default ownership.
- Candidate Database now manages access only for projects owned by the authenticated user.

### Security
- Existing owner-scoped repositories remain unchanged and cannot be bypassed by a numeric ID.
- Shared session loading requires an active, unexpired assignment for the current recipient.
- Shared evidence disables export, deletion, re-screening and raw-resume-text exposure.
- Non-global sharing is restricted to the actor's Country/Location scope.

## 0.7.6 — Sprint 5.7.1C-R2 Accessibility, Brand Governance & Portable OCR Runtime

### Added
- Environment/Streamlit-secret Tesseract executable discovery with operating-system PATH fallback.
- Final accessibility override layer for mode-safe controls, tabs, uploads and file removal.
- ALTEN UI governance documentation and interaction-visibility acceptance tests.

### Changed
- Application version increased to `0.7.6`.
- Light/dark control contrast, sidebar actions and uploaded-file removal visibility were corrected.

## 0.7.5 — Sprint 5.7.1C-R1 Universal Intake Templates & Guided Workspace UX

### Added
- Multi-format JD, supplemental-skill and resume intake for PDF, DOCX, TXT, XLSX, XLS, CSV and common image formats.
- OCR image reader and scanned-PDF page fallback using Tesseract.
- Spreadsheet normalization for field/value and generic tabular recruitment data.
- Downloadable Job Description and Supplemental Skill List Excel templates.
- Mandatory/Preferred classification in supplemental skill-list spreadsheets.
- Guided operational navigation across Home, Resume Screening, Results and Candidate Database.
- Action-oriented home dashboard using private project/session/candidate/shortlist counts.
- Compact non-duplicated sidebar identity card, dark mode and bottom sign-out placement.
- New multi-format, template, navigation and UI contract tests.

### Changed
- Application version increased to `0.7.5`.
- Empty text extraction now fails clearly rather than creating empty screening records.
- Resume Screening now shows accepted formats, input readiness and a direct Results action.
- Home is an operational launchpad rather than a static feature-only page.

### Deployment
- Added `packages.txt` for the Tesseract Linux runtime.
- Added Pillow, pytesseract and xlrd dependencies.

## 0.7.4 — Sprint 5.7.1C Tenant-Specific Configuration & AI-Ready Taxonomy Foundation

### Added
- Immutable tenant/workspace configuration versions with SHA-256 integrity checks.
- RBAC-controlled configuration upload, validation, activation, rollback and download.
- Context-local configuration selection using `ContextVar` for concurrent Streamlit users.
- Workbook cache isolation by resolved file path, file size and modification time.
- Database schema version 5 with `tenant_configuration_versions` and screening-session configuration snapshots.
- Configuration page with active-source health, sheet coverage and version history.
- Audit events for configuration publication, activation and fallback to system default.
- End-to-end tests proving that two users can screen the same text with different private taxonomies without cache leakage.
- AI reference adoption plan covering structured extraction, hybrid retrieval, explainability, alternative-role intelligence, recruiter copilot and AI safety.

### Changed
- Application version increased to `0.7.4`.
- `ProcessingService` resolves one immutable configuration for the complete screening operation.
- Resume/JD extractors no longer retain process-global repository instances.
- Results display the configuration source and fingerprint used for the screening.
- Runtime tenant workbooks are ignored by Git and remain outside clean source releases.

### Security and governance
- Users can view only their own active configuration; authorized administrators may manage permitted target workspaces.
- Tenant Admin configuration authority remains country/location scoped.
- Uploaded workbooks are validated before storage and revalidated before activation.
- Configuration files are stored in tenant-specific paths and verified before use.
- Reopened screening sessions retain the exact configuration version and SHA-256 provenance.

## 0.7.3 — Milestone 5.7.1B-R1 Repository Rebaseline & Deployment Guardrails

### Added
- Repository policy scanner for secrets, runtime data, databases, caches, package artifacts and legacy workbooks.
- Deterministic source-only ZIP builder with SHA-256 manifest.
- GitHub quality workflow for policy, preflight, tests and compilation.
- `.gitattributes`, safe `.env.example`, Streamlit secrets example, `SECURITY.md` and `CONTRIBUTING.md`.
- Environment-variable priority with Streamlit secrets fallback for hosted deployments.
- Automated repository-policy, source-release and deployment-bootstrap tests.

### Changed
- Application version increased to `0.7.3`.
- Initial System Owner setup now fails closed on shared/public deployments when no setup key is configured.
- Git ignore rules now cover runtime, privacy, secret, package and development artifacts comprehensively.

### Removed from clean source baseline
- `README_APPLY.txt`.
- `PACKAGE_MANIFEST_SHA256.txt`.
- Any historical cache, database, CV, report, log or local sprint-package artifact.

## 0.7.2 — Sprint 5.7.1B Secure File, Temporary Storage & Export Isolation

### Added
- Tenant/user/workspace-scoped upload, temporary and report roots.
- `StorageScope` and `StoredFile` models.
- Owner-validated secure storage read, write, list, delete and cleanup operations.
- Randomized stored filenames and SHA-256 content metadata.
- Secure in-memory Excel generation with private report persistence.
- Cross-user and cross-tenant file denial tests.

### Changed
- UploadService now requires authenticated context and private storage scope.
- Screening filesystem workspace uses the persisted database session key.
- Results export requires the authenticated context.
- Application version increased to `0.7.2`.

### Security
- Shared runtime upload/output paths are removed from the active UI workflow.
- Guessed absolute paths cannot bypass owner checks.
- Path traversal and symbolic-link escape controls are enforced.
- Failed screening workspaces are removed without affecting another user.
- Project deletion removes only the owner's associated session workspaces.

## 0.7.1 — Sprint 5.7.1A-R1 Admin-Provisioned Identity, RBAC & ALTEN Experience

### Added
- One-time System Owner setup.
- Employee User ID authentication.
- `SYSTEM_OWNER`, `GLOBAL_ADMIN`, `TENANT_ADMIN`, `USER` and `READER` roles.
- Role-permission policy and role-aware page navigation.
- Single-user creation through Administration.
- Excel user-import template, preview, row validation and commit.
- Optional Time Zone and administrative profile fields.
- Admin-entered, Excel-provided or generated temporary passwords.
- Configurable seven-day temporary-password expiry.
- Mandatory first-login password change.
- Forgot Password request queue with non-enumerating response.
- User Access Master export without passwords.
- One-time temporary credential export.
- Credential reset, role change and account-status administration.
- Roles, permissions, assignments, reset requests, import jobs and audit tables.
- Central ALTEN brand tokens, reusable visual components and animated responsive theme.
- RBAC, provisioning, Excel import, credential export and visual contract tests.

### Changed
- Database schema version increased from 3 to 4.
- Public self-registration was removed.
- Login page now contains only User ID, Password, Sign In and Forgot Password.
- Existing active schema-3 identities receive deterministic migration roles and login IDs.
- Legacy-data claim uses User ID rather than email.
- Application version increased to `0.7.1`.

### Security
- User IDs are globally unique case-insensitively.
- Temporary passwords are never hardcoded in source.
- Plaintext temporary credentials are available only in the immediate creation/reset/import result.
- User Access Master never contains plaintext passwords or password hashes.
- Role authority does not override private-record ownership.
- Session revocation occurs after password or role changes.

### Known boundary
- Uploaded and generated files are not yet tenant/user/session isolated. Internet-facing production deployment remains blocked until Sprint `5.7.1B`.

## 0.7.0 — Sprint 5.7.1A Multi-User Identity & Database Isolation

- Added SecurityContext, users/tenants/memberships and opaque server-side sessions.
- Added private owner-scoped persistence and cross-user database isolation tests.
- Preserved pre-multi-user data under a disabled legacy owner.

## 0.6.1 — Milestone 5.6.A Audit Remediation & Stabilization

- Corrected clean-clone, parser, model, matching, configuration and test defects.
- Added modular matching, end-to-end ProcessingService and documentation baseline.
