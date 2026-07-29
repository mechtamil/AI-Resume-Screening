# RecruitOS Architecture

## 1. Runtime architecture

```text
Browser / Streamlit
        |
        v
Premium ALTEN UI
app.py + ui/* + ui/theme.py + ui/brand_components.py + ui/navigation.py
        |
        +---------------- Authentication ----------------+
        |                                                |
        v                                                v
AuthService -> UserRepository -> SQLite             AuthorizationService
        |                                                |
        v                                                v
SecurityContext(user_id, tenant_id, role, owner scope) --+
        |
        +---------------- Screening ---------------------+
        |                                                |
        v                                                v
UploadService / ProcessingService                  PersistenceService
        |                                                |
        v                                                v
DocumentManager / OCR / Spreadsheet Reader / Parsers / Matchers          Project/Session/Candidate repos
        |                                                |
        v                                                v
ConfigurationContext / TenantConfigurationService  Private SQLite records
        |                                                |
        v                                                v
System default or immutable tenant workbook      Configuration snapshot metadata
```

## 2. Dependency rules

- UI calls services; UI does not calculate scores, parse documents or authorize database IDs itself.
- `AuthService` authenticates and resolves server-side sessions.
- `AuthorizationService` decides role permission.
- Repositories enforce record ownership in SQL.
- `ProcessingService` coordinates document-to-ranking flow.
- `PersistenceService` coordinates transactional persistence/reopening.
- `MasterRepository` and domain repositories own workbook access.
- Domain models do not import Streamlit, SQLite or workbook code.
- `ui/theme.py` owns global styling; page modules do not invent independent brand palettes.

## 3. Authentication flow

```text
User ID + Password
        |
        v
UserRepository.get_user_by_login_id
        |
        v
Account / validity / lock / temp-expiry checks
        |
        v
PBKDF2 password verification
        |
        v
Opaque random session token
        |
        +--> Browser stores raw token in Streamlit session state
        |
        +--> SQLite stores SHA-256 token hash only
        |
        v
SecurityContext resolved on every Streamlit rerun
```

Public self-registration does not exist. When no System Owner exists, the bootstrap form is exposed only when a deployment setup key is configured or an explicit isolated-development override is enabled.

## 4. RBAC and ownership

Authorization requires both:

```text
Role permission + record ownership/scope
```

Role hierarchy:

```text
SYSTEM_OWNER
  -> manages GLOBAL_ADMIN, TENANT_ADMIN, USER, READER
GLOBAL_ADMIN
  -> manages TENANT_ADMIN, USER, READER globally
TENANT_ADMIN
  -> manages USER and READER in the same Country/Location
USER
  -> operates only on own private screening data
READER
  -> reads only records authorized by an active `record_shares` assignment
```

Administrative roles do not inherit unrestricted access to private candidate content.

## 5. Database schema lifecycle

Schema version `6` includes tenant configuration provenance plus explicit sharing and review assignments:

- `tenant_configuration_versions`
- immutable version number and workbook fingerprint
- activation status and audit actors/timestamps
- screening-session `configuration_version_id`
- screening-session `configuration_sha256`
- screening-session `configuration_snapshot_json`
- configuration view/manage permissions
- `record_shares` owner, recipient, project, role, expiry and revocation metadata
- Reviewer assignment status and notes separated from screening evidence
- partial unique index preventing duplicate active project/recipient assignments
- `SHARED_RECORDS_READ` and `SHARED_RECORDS_MANAGE_OWN` permissions

Existing schema-3 through schema-5 databases migrate forward idempotently. Historical screening sessions remain readable; new sessions carry exact configuration provenance.

## 6. Private persistence scope

```text
recruitment_projects
  WHERE tenant_id = context.tenant_id
    AND owner_user_id = context.user_id

screening_sessions / candidates / resumes / match_results
  WHERE tenant_id = context.tenant_id
    AND created_by_user_id = context.user_id
```

The same project key or Job ID may exist for different owners.

## 7. User administration architecture

```text
Administration UI
      |
      v
UserManagementService
      +--> AuthorizationService privilege checks
      +--> PasswordService hash/generation
      +--> UserRepository create/update/session revoke
      +--> Excel import/template/export
      +--> Audit event
```

Plaintext temporary passwords exist only in the immediate service response used for one-time display/download. They are never written to the user table, audit details or User Access Master.

## 8. Visual architecture

- `config/brand.py`: ALTEN tokens and approved logo sources.
- `ui/theme.py`: CSS variables, gradients, glass surfaces, responsive rules, hover states, animations and reduced-motion override.
- `ui/brand_components.py`: login visual, page hero, sidebar brand and reusable feature cards.
- `.streamlit/config.toml`: base Streamlit theme aligned to central tokens.

The visual layer uses CSS-only GPU-friendly motion. No animation may block interaction or ignore reduced-motion preferences.

## 9. Matching architecture

The modular package under `services/matching/` is authoritative:

```text
SkillMatcher
ExperienceMatcher
EducationMatcher
CertificationMatcher
KeywordMatcher
        |
        v
ScoreCalculator -> RecommendationRepository -> ranked MatchResult
```

`services/matching_engine.py` is a compatibility facade only.

## 10. Configuration and cache boundary

```text
System default workbook
        |
        +--> immutable tenant version(s)
                    |
                    v
TenantConfigurationService
        +--> validation
        +--> RBAC and target scope
        +--> SHA-256 integrity
        +--> activation/rollback audit
                    |
                    v
ConfigurationContext (ContextVar)
                    |
                    v
MasterRepository cache keyed by path + size + mtime
                    |
                    v
Skill/Education/Certification/Scoring/Recommendation repositories
```

The active workbook is resolved once for the complete screening operation. Parser and matcher repositories are created inside the request-local context. No process-global extractor repository is retained when production dependency injection is not supplied.

## 11. Private file and export boundary

Version `0.7.2` derives every active upload, temporary and report path from:

```text
SecurityContext -> tenant_id -> user_id -> session workspace_id
```

The filesystem workspace identifier is the same as the persisted screening
`session_key`. `SecureStorageService` is the only authorized path constructor.
Reads, listings, deletions and export downloads repeat owner validation. Shared
legacy upload folders remain only for compatibility and are not used by the
active Streamlit screening workflow.

## 12. Current deployment boundary

Authentication, database ownership, filesystem ownership, clean repository policy and tenant configuration isolation are implemented. Retention, managed database/object storage, concurrency hardening and AI governance remain required before a global internet-facing v1.0 release.
## 13. Repository and release architecture

```text
Git-tracked source
      |
      v
RepositoryPolicy
  - rejects secrets, CVs, databases, logs, caches and release artifacts
      |
      +--> GitHub quality workflow
      |
      v
BuildCleanRelease
  - packages tracked files only
  - deterministic ZIP metadata
  - SHA-256 source manifest
      |
      v
Fresh repository / Streamlit deployment
```

The clean release builder never packages ignored working-tree content. A clean Git status is required for normal CLI release builds.



## 13. Universal intake and guided UX boundary

```text
PDF / DOCX / TXT / XLSX / XLS / CSV / IMAGE
                    |
                    v
DocumentManager reader registry
  +--> PyMuPDF text extraction
  +--> scanned-page OCR fallback
  +--> Pillow + Tesseract image OCR
  +--> pandas spreadsheet normalization
                    |
                    v
ExtractionService -> JDParser / ResumeParser
```

`InputTemplateService` creates the JD and supplemental-skill Excel templates in memory. `SkillListService` preserves Mandatory and Preferred classification. `ui/navigation.py` queues authorized page transitions before the sidebar radio widget is rendered, avoiding unsafe same-run widget-state mutation.

The sidebar contains one identity card, appearance control and a bottom sign-out action. Theme selection is browser-session-local and does not alter tenant business configuration.

## 15. Explicit sharing architecture

```text
Owner Candidate Database
        |
        v
SharingService -> SharingRepository -> record_shares + audit_events
        |                                      |
        | active recipient/project/session     | grant/review/expiry/revoke
        v                                      v
Shared Records UI -> read-only PersistenceService reconstruction
```

`ProjectRepository`, `ScreeningRepository` and `CandidateRepository` remain owner scoped.
`SharingRepository` is the only cross-user authorization boundary. It first validates an
active, unexpired assignment, then reconstructs the selected owner session through an
internal owner scope. The returned shared payload removes storage metadata and raw resume
text. Reviewer progress writes only to assignment metadata and never to screening evidence.

