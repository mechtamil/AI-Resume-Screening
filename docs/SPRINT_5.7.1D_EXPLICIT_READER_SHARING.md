# Sprint 5.7.1D — Explicit Reader Sharing & Review Assignment

## Release baseline

- Application version: `0.7.7`
- Database schema: `6`
- Previous milestone: `5.7.1C-R2`
- Deployment target: Streamlit development environment

## Objective

Deliver controlled cross-user access without weakening RecruitOS private ownership. A project remains invisible to every other user until its authenticated owner grants an explicit Reader or Reviewer assignment.

## Functional scope

### Owner controls

The Candidate Database provides project-scoped sharing controls:

- select one active recipient;
- assign Reader or Reviewer access;
- set an optional expiry;
- add an owner note;
- inspect sharing history;
- revoke active access immediately.

A standard owner or Tenant Admin may share only within the same Country/Location. System Owner and Global Admin may select an active recipient globally, but may still grant access only to projects they personally own.

### Recipient workspace

The Shared Records page lists only active, unexpired assignments for the authenticated recipient. It supports:

- shared-project summary;
- owner and expiry metadata;
- saved screening-session selection;
- read-only Job Description and ranked candidate evidence;
- sharing audit history;
- Reviewer progress updates.

The shared view does not expose project deletion, re-screening, file storage paths, report export or raw resume text.

### Review assignments

Reader assignments are evidence-only. Reviewer assignments additionally store one of:

- `ASSIGNED`
- `IN_REVIEW`
- `COMPLETED`

Reviewer notes and status are assignment metadata. They do not modify Job Description, candidate, match-result, score or recommendation records.

## Security architecture

`ProjectRepository`, `ScreeningRepository` and `CandidateRepository` remain owner scoped. Shared access is implemented through a dedicated `SharingRepository` and `SharingService` boundary.

Before a shared session is reconstructed, RecruitOS verifies:

1. the current user is the recorded grantee;
2. the assignment status is active;
3. the assignment has not expired;
4. the project still belongs to the recorded owner and tenant;
5. the selected screening session belongs to that project and owner;
6. the owner account remains active.

Numeric project, session or share identifiers do not grant access independently.

## Database migration

Schema version `6` adds `record_shares` with:

- owner tenant/user scope;
- recipient user;
- project;
- Reader/Reviewer assignment;
- active/revoked/expired status;
- optional expiry and owner note;
- Reviewer progress and note;
- creation, update and revocation actors/timestamps.

A partial unique index prevents more than one active assignment for the same project and recipient. Historical revoked/expired assignments remain available to the owner.

## Audit events

The existing `audit_events` table records:

- `share.granted`
- `share.review_updated`
- `share.expired`
- `share.revoked`

Audit entries identify the share and include project/recipient or review-status metadata.

## Files

### Added

- `database/sharing_repository.py`
- `services/sharing_service.py`
- `ui/shared_records.py`
- `tests/test_sharing_service.py`
- `tests/test_shared_records_ui.py`
- `docs/SPRINT_5.7.1D_EXPLICIT_READER_SHARING.md`

### Changed

- `database/database.py`
- `services/authorization_service.py`
- `ui/candidate_database.py`
- `app.py`
- `tests/test_database.py`
- `tests/test_authorization_service.py`
- `VERSION`
- `ROADMAP.md`
- `PROJECT_SPEC.md`
- `ARCHITECTURE.md`
- `CHANGELOG.md`
- `README.md`
- `TODO.md`
- `docs/CODEBASE_MAP.md`

## Acceptance criteria

- Projects are private before a share exists.
- Only the owner can grant or revoke project access.
- An active Reader assignment permits read-only evidence access.
- An active Reviewer assignment permits read-only evidence plus review-progress metadata.
- Direct owner-only repository calls remain denied to recipients.
- A recipient cannot open a session from another project.
- Revocation blocks access immediately.
- Expiry blocks access and records an audit event.
- Reader assignments cannot update Reviewer progress.
- Shared Records contains no export or deletion control.
- Full regression, compilation, preflight and repository policy pass.
