# RecruitOS Codebase Map — Version 0.7.1

## Entry and UI

| File | Responsibility |
|---|---|
| `app.py` | Streamlit entry point, theme injection, authentication gate and RBAC navigation |
| `ui/authentication.py` | User ID login, Forgot Password, owner bootstrap and forced first-login password change |
| `ui/admin_users.py` | User list, single provisioning, Excel import, credential/reset/role/status administration |
| `ui/theme.py` | Central responsive CSS, motion, component styling and reduced-motion behavior |
| `ui/brand_components.py` | ALTEN login visual, page heroes, sidebar and feature-card HTML |
| `ui/home.py` | Role-aware premium home dashboard |
| `ui/resume_screening.py` | Authorized screening workflow |
| `ui/results.py` | Ranked result view and Excel export |
| `ui/candidate_database.py` | Private projects, sessions and candidates |

## Configuration

| File | Responsibility |
|---|---|
| `config/brand.py` | ALTEN palette and approved logo source selection |
| `config/settings.py` | Application/security environment settings and version |
| `config/paths.py` | Filesystem path authority |
| `config/sheet_names.py` | Central workbook sheet constants |
| `.streamlit/config.toml` | Base Streamlit theme and server security options |
| `Master_Data/RecruitOS_Configuration.xlsx` | Business/master-data source of truth |

## Identity, RBAC and administration

| File | Responsibility |
|---|---|
| `models/security_context.py` | Authenticated user/tenant/role contract |
| `services/password_service.py` | Temporary/permanent password validation, generation, hashing and verification |
| `services/auth_service.py` | Owner bootstrap, User ID authentication, session resolution, password reset/change and logout |
| `services/authorization_service.py` | Five-role permission policy and target-management boundaries |
| `services/user_management_service.py` | Single/bulk provisioning, access exports, credential reset, role/status operations |
| `database/user_repository.py` | Identity, role, session, audit, import and reset persistence |
| `database/database.py` | SQLite connection and schema migrations through version 4 |
| `tools/claim_legacy_data.py` | Explicit transfer of protected legacy records to a User ID |

## Screening and persistence

| File/group | Responsibility |
|---|---|
| `services/processing_service.py` | End-to-end JD/resume processing and ranking orchestration |
| `services/persistence_service.py` | Save/reopen/list/delete private screening sessions |
| `database/project_repository.py` | Owner-scoped projects |
| `database/screening_repository.py` | Owner-scoped sessions and match results |
| `database/candidate_repository.py` | Owner-scoped candidates |
| `reports/excel_report.py` | Ranked screening Excel report when present from Sprint 5.7.0 |

## Parsing and matching

| File/group | Responsibility |
|---|---|
| `JD/jd_model.py` | Authoritative JobDescription model |
| `JD/jd_parser.py` | Section-aware JD parsing |
| `parser/resume_parser.py` | Candidate resume parsing |
| `parser/extractors/*` | Personal, skill, education, certification and experience extraction |
| `services/matching/*` | Authoritative modular matchers, score calculator and orchestrator |
| `services/matching_engine.py` | Compatibility facade only |

## Tests

- `tests/test_auth_service.py`: bootstrap, login, forced reset, forgot password and no-public-registration contract.
- `tests/test_authorization_service.py`: role pages, assignment and location scope.
- `tests/test_user_management_service.py`: single/Excel provisioning and safe exports.
- `tests/test_tenant_isolation.py`: cross-user database isolation.
- `tests/test_visual_theme.py`: brand tokens, motion, responsiveness and simplified login contract.
- Remaining `tests/test_*.py` files cover configuration, parsing, matching, persistence, uploads and end-to-end behavior.

## Authoritative boundaries

- No other file may define independent role permissions.
- No page may create its own brand palette.
- No repository may expose unscoped project/session/candidate/match queries.
- No service may store or re-export existing plaintext passwords.
