# RecruitOS — Master Project Specification

## 1. Product baseline

- **Product:** RecruitOS — AI Resume Screening & Recruitment Platform
- **Organization:** ALTEN
- **Owner:** Tamilvanan A
- **Current version:** `0.7.5`
- **Current milestone:** `5.7.1C-R1 — Universal Intake Templates & Guided Workspace UX`
- **Database schema:** `5`
- **Technology:** Python, Streamlit, pandas, SQLite, openpyxl, PyMuPDF, python-docx, Pillow and Tesseract OCR
- **Status:** Active development. Identity, RBAC, private data/files, clean deployment guardrails and tenant-specific configuration versioning are implemented.

## 2. Product objective

RecruitOS accepts a Job Description, an optional supplemental Skill List and one or more resumes. It extracts structured data, standardizes configured master data, performs deterministic matching, calculates configuration-driven weighted scores, assigns recommendations, ranks candidates, persists private screening sessions and presents results through a modern ALTEN-aligned interface.

## 3. Source-of-truth hierarchy

1. `PROJECT_SPEC.md` — functional/product decisions.
2. `ARCHITECTURE.md` — technical boundaries and dependency direction.
3. `docs/CODEBASE_MAP.md` — file/module ownership.
4. `ROADMAP.md` — sprint plan.
5. `CHANGELOG.md` — completed changes.
6. `Master_Data/RecruitOS_Configuration.xlsx` — business/master data.
7. Source code and automated tests — executable implementation contract.

Conflicts must be corrected in the same sprint that introduces them.

## 4. Screening workflow

1. Authenticated User uploads one JD in a supported text, spreadsheet, PDF or image format, or completes the RecruitOS JD Excel template.
2. User may upload a supplemental Skill List in a supported format or use the RecruitOS skill-list template with Mandatory/Preferred classification.
3. User uploads one or more resumes in supported text, spreadsheet, PDF or image formats.
4. Uploads are validated and safely stored.
5. `DocumentManager` and `ExtractionService` extract text.
6. `JDParser` and `ResumeParser` create domain models.
7. Workbook-backed repositories standardize configured values.
8. Modular matchers calculate skill, experience, education, certification and keyword results.
9. `ScoreCalculator` uses weights from the `Scoring` sheet.
10. `RecommendationRepository` resolves the configured recommendation.
11. Candidates are ranked.
12. The private project/session/candidates/results are persisted.
13. Results and Excel exports are shown only to the authorized owner.

## 4.1 Universal intake contract

RecruitOS supports these common recruitment-document extensions:

- Text/documents: `PDF`, `DOCX`, `TXT`
- Spreadsheets: `XLSX`, `XLS`, `CSV`
- Images/OCR: `PNG`, `JPG`, `JPEG`, `WEBP`, `TIF`, `TIFF`

"Any format" means the listed common recruiter formats; unsupported proprietary or encrypted formats must be converted before upload. Scanned PDFs and images use OCR. Empty or unreadable extraction is rejected rather than silently producing an empty candidate.

The JD and supplemental-skill Excel templates are generated in memory by RecruitOS. Structured templates improve extraction completeness and evidence accuracy; they must not artificially change the configured scoring formula.

## 5. Identity and login contract

### 5.1 Login page

The public authentication page contains only:

- `User ID`
- `Password`
- `Sign In`
- `Forgot Password?`

The page must not display Organization Name, Organization Code, Country, Location, Region or public registration.

### 5.2 Account provisioning

- No user may self-register.
- The first System Owner is created through a one-time setup screen.
- Later accounts are created only by an authorized System Owner, Global Admin or scope-limited Tenant Admin.
- Accounts can be created individually in the UI or in bulk through an Excel import.
- User ID is stored as text and is globally unique, case-insensitively.
- Time Zone is optional.
- Country or Location remains an administrative profile/scope field; it is not requested at login.

### 5.3 Roles

Every active user must have one role:

| Role | Primary scope |
|---|---|
| `SYSTEM_OWNER` | Global policy, Global Admin governance and all administrative controls |
| `GLOBAL_ADMIN` | Global user administration except System Owner/Global Admin elevation |
| `TENANT_ADMIN` | User and Reader administration within assigned Country/Location |
| `USER` | Own screening projects, candidates, results and reports |
| `READER` | Explicitly shared read-only records only |

Role permission and record ownership are separate checks. Administrative authority does not automatically expose private resumes or results.

## 6. Credential lifecycle

- Temporary passwords are entered by Admin, supplied in the import workbook, or generated uniquely by RecruitOS.
- No shared temporary password is hardcoded in Python.
- Temporary password minimum is configurable and currently defaults to 6 characters.
- Temporary credentials default to a 7-day lifetime. Setting `RECRUITOS_TEMP_PASSWORD_EXPIRY_DAYS=0` disables expiry for a controlled deployment.
- A newly provisioned or reset account has status `RESET_REQUIRED`.
- A user authenticated with a temporary password can access only the mandatory password-change screen.
- Password change invalidates the temporary credential and all existing sessions, then issues a new session.
- Permanent passwords are hashed using PBKDF2-HMAC-SHA256 with a random per-user salt.
- Existing passwords are never exportable. Admins may download a User Access Master without passwords and a one-time temporary-credential file immediately after creation/reset/import.
- Forgot Password records a generic administrator-assisted request without confirming whether a User ID exists.

## 7. Data privacy and isolation

RecruitOS is private by default.

- Every protected operation receives a server-validated `SecurityContext`.
- Each user owns a private tenant/workspace.
- Project queries require both `tenant_id` and `owner_user_id`.
- Session, candidate and match queries require both `tenant_id` and `created_by_user_id`.
- Numeric database identifiers cannot bypass ownership filters.
- The same Job ID may exist independently for different users.
- Reader access requires a future explicit sharing record; there is no implicit visibility.
- Candidate files, databases, logs, temporary files and exports must not be committed to Git.

## 8. Administration functions

The Administration page provides:

- User list and User Access Master export
- Add Single User
- Excel template download
- Excel import validation, preview and commit
- One-time temporary credential export
- Temporary credential reset
- Role change within actor privilege boundaries
- Account status update
- Forgot Password request queue
- Audit events in the database

Bulk import validates required columns, identity, duplicate User IDs, role authority, location scope, temporary password and validity dates. Invalid rows do not block valid rows.

## 9. ALTEN visual experience

RecruitOS must be visually differentiated, responsive and accessible rather than a default Streamlit-style application.

- ALTEN colors and logo references are centralized in `config/brand.py`.
- Theme behavior is centralized in `ui/theme.py`.
- Reusable visual components are centralized in `ui/brand_components.py`.
- The interface uses layered gradients, glass panels, responsive layouts, micro-interactions and CSS animations.
- Animations must be lightweight and respect `prefers-reduced-motion`.
- The ALTEN logo must not be recolored, deformed, cropped, rotated or decorated.
- Approved local logo assets take priority; official media-library URLs are the fallback.
- A compact sidebar identity card must show each account detail once; Country/Location is hidden when it duplicates User ID.
- Sign Out is placed in the sidebar footer.
- Users can switch between light and dark workspace themes.
- Operational pages are linked through a guided workflow: Home → Resume Screening → Results → Candidate Database.
- Home must show real private-workspace counts and direct action buttons, not only decorative marketing cards.


## 10. Configuration architecture

The source-controlled system default is:

`Master_Data/RecruitOS_Configuration.xlsx`

Each private workspace may receive immutable, validated tenant versions under the runtime-only `Master_Data/private/tenant_<id>/` tree. The active configuration is resolved through a request-local `ConfigurationContext`; repository caches are keyed by workbook identity so one workspace cannot reuse another workspace's master data.

Required sheets include Skills, Education, Certifications, Companies, Locations, Domains, Languages, Roles, Industries, Scoring, Recommendation and Configuration.

Rules:

- Business/master values are not hardcoded in Python.
- Scoring weights and recommendations come from the resolved workbook.
- Active scoring weights must total 100.
- Recommendation ranges must cover 0–100 continuously without overlap.
- Uploaded workbooks are validated before publication and stored as immutable versions.
- Activation and rollback are explicit, RBAC-controlled and audit logged.
- Every screening session stores the configuration version, SHA-256 fingerprint and sheet summary used for that result.
- Authentication/security settings are deployment configuration, not business master data.
- Configuration snapshots are the future governance anchor for AI model, prompt, embedding and taxonomy versions.

## 11. Testing and quality gate

Primary command:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Required quality rules:

- Tests are noninteractive and assertion-based.
- Database tests use temporary databases.
- Cross-user and cross-role denial cases are mandatory.
- Missing files fail rather than silently parsing empty content.
- All Python source must compile.
- Preflight must pass before commit.

## 12. Private runtime file requirements

Version `0.7.2` stores active JDs, resumes, skill lists, temporary files and
generated reports under tenant/user/session workspaces. Every read, list, delete
and report operation requires the current `SecurityContext`; filenames and raw
paths do not grant access.

## 13. Current production boundary

Authentication, database and runtime file isolation are implemented. RecruitOS
still requires explicit Reader sharing, privacy
retention controls, production database/concurrency hardening and deployment
security acceptance before global internet-facing v1.0 release.
## 14. Repository and deployment integrity

RecruitOS source control contains only source code, tests, documentation, approved static assets and the central configuration workbook. Runtime databases, CVs, uploaded JDs, reports, logs, caches, secrets and package-overlay artifacts are prohibited.

- `tools.repository_policy` validates tracked or filesystem content.
- `tools.build_clean_release` builds a deterministic ZIP from policy-approved Git-tracked files only.
- `.github/workflows/quality.yml` runs policy, preflight, tests and compilation on every main-branch push and pull request.
- Shared deployments fail closed when the first System Owner is required but `RECRUITOS_INITIAL_SETUP_KEY` is absent.
- `.env.example` and `.streamlit/secrets.toml.example` document deployment variables without storing real secrets.
- Environment variables take priority, with Streamlit secrets fallback for hosted deployment.
- A fresh Git rebaseline must be created from a clean source package, never by copying the old `.git` directory.

