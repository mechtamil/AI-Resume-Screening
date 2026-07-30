# RecruitOS Codebase Map — Version 0.7.8

## Entry and UI

| File | Responsibility |
|---|---|
| `app.py` | Streamlit entry point, theme injection, authentication gate and RBAC navigation |
| `ui/authentication.py` | User ID login, Forgot Password, owner bootstrap and forced first-login password change |
| `ui/admin_users.py` | User list, single provisioning, Excel import, credential/reset/role/status administration |
| `ui/theme.py` | Central responsive CSS, motion, component styling and reduced-motion behavior |
| `ui/brand_components.py` | ALTEN login visual, page heroes, sidebar and feature-card HTML |
| `ui/home.py` | Private activity metrics and direct operational actions |
| `ui/resume_screening.py` | Multi-format intake, template downloads and authorized screening workflow |
| `ui/results.py` | Ranked result view and Excel export |
| `ui/candidate_database.py` | Private projects, sessions, candidates, reopen navigation and owned-project sharing controls |
| `ui/shared_records.py` | Recipient-only read-only evidence and Reviewer progress workspace |
| `ui/navigation.py` | Safe queued page transitions and guided workflow footer |

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
| `services/authorization_service.py` | Five-role permission policy, sharing permissions and target-management boundaries |
| `services/user_management_service.py` | Single/bulk provisioning, access exports, credential reset, role/status operations |
| `database/user_repository.py` | Identity, role, session, audit, import and reset persistence |
| `database/database.py` | SQLite connection and schema migrations through version 7 |
| `tools/claim_legacy_data.py` | Explicit transfer of protected legacy records to a User ID |

## Screening and persistence

| File/group | Responsibility |
|---|---|
| `services/processing_service.py` | End-to-end JD/resume processing and ranking orchestration |
| `services/persistence_service.py` | Save/reopen/list/delete private screening sessions |
| `services/sharing_service.py` | Grant/revoke/list shared access, reconstruct authorized read-only sessions and reviewer progress |
| `database/sharing_repository.py` | Schema-6 share assignments, expiry, recipient/session authorization and sharing audit |
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

## Sprint 5.7.1C additions

### `models/configuration_version.py`
Immutable resolved workbook metadata and persistence-safe configuration summary.

### `services/configuration_context.py`
Context-local active configuration using `ContextVar`; prevents concurrent users from sharing mutable workbook state.

### `database/tenant_configuration_repository.py`
Schema-5 persistence for immutable tenant configuration versions and activation history.

### `services/tenant_configuration_service.py`
RBAC, target-user scope, upload validation, immutable storage, SHA-256 integrity, activation, rollback, download and screening snapshot orchestration.

### `ui/configuration_management.py`
Active configuration health, sheet coverage, version history, authorized publication and activation UI.

### `tests/test_configuration_context.py`
Context restoration and cross-tenant cache isolation.

### `tests/test_tenant_configuration_service.py`
Version lifecycle, RBAC, duplicate prevention and tamper detection.

### `tests/test_configuration_screening_isolation.py`
End-to-end proof that different tenant taxonomies produce isolated extraction results.

### `tests/test_configuration_snapshot_persistence.py`
Reopen-time configuration provenance contract.


## Sprint 5.7.1C-R1 additions

| File | Responsibility |
|---|---|
| `parser/image_reader.py` | OCR extraction for PNG/JPEG/WEBP/TIFF input |
| `parser/spreadsheet_reader.py` | XLSX/XLS/CSV normalization into parser-ready text |
| `services/input_template_service.py` | In-memory JD and supplemental-skill Excel templates |
| `services/skill_list_service.py` | Mandatory/Preferred supplemental requirement parsing |
| `ui/navigation.py` | Authorized queued navigation and workflow neighbors |
| `tests/test_document_manager_multiformat.py` | Spreadsheet/image normalization contract |
| `tests/test_input_template_service.py` | Excel template structure and validation contract |
| `tests/test_skill_list_service_formats.py` | Mandatory/Preferred list behavior |
| `tests/test_guided_ui_contract.py` | Home/sidebar/template/next-action UI source contract |

## Sprint 5.7.1D additions

| File | Responsibility |
|---|---|
| `database/sharing_repository.py` | Owner grants, recipient authorization, expiry, revocation, review progress and audit persistence |
| `services/sharing_service.py` | RBAC, Country/Location recipient scope and safe shared-session reconstruction |
| `ui/shared_records.py` | Read-only Reader/Reviewer evidence workspace without export or deletion |
| `tests/test_sharing_service.py` | Private-default, explicit allowance, denial, expiry, revocation and session-boundary tests |
| `tests/test_shared_records_ui.py` | Static read-only UI and routing contracts |

## Sprint 5.7.2A additions

| File | Responsibility |
|---|---|
| `models/ai_contracts.py` | Immutable provider request/response, model, prompt and policy contracts |
| `database/ai_registry_repository.py` | Schema-7 model, prompt, tenant-policy and content-free telemetry persistence |
| `services/ai/schema_validator.py` | Dependency-free structured JSON validation |
| `services/ai/providers/base.py` | Provider protocol and bounded JSON HTTP transport |
| `services/ai/providers/openai_responses.py` | OpenAI Responses structured-output adapter with `store=false` |
| `services/ai/providers/ollama.py` | Local Ollama structured `/api/chat` adapter |
| `services/ai_registry_service.py` | RBAC, immutable registry administration, tenant policy and telemetry views |
| `services/ai/provider_gateway.py` | Policy resolution, prompt rendering, provider dispatch, validation, limits, cost and telemetry |
| `ui/ai_configuration.py` | Provider readiness, registry, tenant policy and telemetry workspace |
| `tests/test_ai_*.py` | Schema, provider, registry, policy, telemetry and UI contracts |

