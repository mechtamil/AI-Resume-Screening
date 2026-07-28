# RecruitOS Architecture

## 1. Runtime architecture

```text
Browser / Streamlit
        |
        v
Premium ALTEN UI
app.py + ui/* + ui/theme.py + ui/brand_components.py
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
DocumentManager / Parsers / Matchers          Project/Session/Candidate repos
        |                                                |
        v                                                v
Configuration repositories                         Private SQLite records
        |
        v
RecruitOS_Configuration.xlsx
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
  -> reads only records explicitly shared in a future sharing table
```

Administrative roles do not inherit unrestricted access to private candidate content.

## 5. Database schema lifecycle

Schema version `4` adds:

- employee User ID login fields
- account lifecycle and temporary-password fields
- roles, permissions and role-permission mappings
- user-role assignments
- password-reset requests
- user-import jobs
- audit events

Existing schema-3 accounts are migrated safely. The first active pre-R1 account becomes System Owner; other active accounts become Users; disabled legacy data remains protected.

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

`Master_Data/RecruitOS_Configuration.xlsx` is currently a system-wide workbook. Tenant-specific configuration and tenant-aware cache keys are planned for Sprint `5.7.1C`. Until then, admins cannot modify one user's scoring configuration independently.

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

Authentication, database ownership and filesystem ownership are implemented.
Tenant-specific configuration isolation, controlled Reader sharing, retention,
production database concurrency and deployment hardening remain required before
a global internet-facing v1.0 release.
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

