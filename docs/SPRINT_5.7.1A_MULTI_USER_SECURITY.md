# Sprint 5.7.1A — Multi-User Identity & Database Isolation

## Objective

Create a private-by-default identity and persistence foundation so one RecruitOS user cannot access another user's projects, sessions, candidates, or match results.

## Implemented controls

- private tenant/workspace per user
- password hashing and login lockout
- server-side session validation
- authenticated Streamlit gate
- repository-level ownership filters
- safe legacy-data migration
- cross-user isolation tests

## Database schema

Schema version: `3`

New tables:

- `tenants`
- `users`
- `tenant_memberships`
- `auth_sessions`

New ownership columns:

- `recruitment_projects.tenant_id`
- `recruitment_projects.owner_user_id`
- `screening_sessions.tenant_id`
- `screening_sessions.created_by_user_id`
- `candidates.tenant_id`
- `candidates.created_by_user_id`
- `resumes.tenant_id`
- `resumes.created_by_user_id`
- `match_results.tenant_id`
- `match_results.created_by_user_id`

## Authorization invariant

A protected business query must include the authenticated user's tenant and user IDs. No repository provides an unscoped “get all users' projects/candidates” API.

## Acceptance result

- targeted security/persistence tests: 14 passed
- full baseline regression: 56 passed
- syntax compilation: no errors

## Deployment restriction

This sprint isolates database records. Secure tenant/user/session-scoped upload and report storage is required in Sprint 5.7.1B before public production deployment.
