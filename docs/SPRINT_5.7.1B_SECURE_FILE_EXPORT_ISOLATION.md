# Sprint 5.7.1B — Secure File, Temporary Storage & Export Isolation

## Objective

Eliminate shared runtime file paths from the multi-user workflow. Every JD,
resume, skill list, temporary processing file and generated report is stored
under an authenticated tenant/user/screening workspace.

## Storage layout

```text
uploads/private/tenant_<tenant_id>/user_<user_id>/workspace_<session_key>/
  job_description/
  resumes/
  skill_lists/

temp/private/tenant_<tenant_id>/user_<user_id>/workspace_<session_key>/temp/

output/private/tenant_<tenant_id>/user_<user_id>/workspace_<session_key>/reports/
```

The database screening `session_key` and filesystem `workspace_id` are the same
server-generated 32-character identifier.

## Security rules

- No caller supplies a destination directory.
- Every protected operation requires `SecurityContext`.
- Every scope repeats tenant and user ownership validation.
- Arbitrary absolute-path reads and deletes are denied outside the current user root.
- Traversal components are removed from uploaded filenames.
- Stored names include random asset identifiers.
- Symbolic-link roots/chains are rejected.
- File content is SHA-256 hashed at write time.
- Temporary workspace cleanup cannot touch uploads, reports or another user.
- Failed screenings remove their incomplete private workspace.
- Deleting an owned project removes only its associated private session workspaces.
- Successful uploads remain private for reopening/retention lifecycle work.
- Excel exports are built in memory, persisted privately, then returned to the
  authenticated Streamlit session for download.

## Main modules

- `models/storage_asset.py`
- `services/secure_storage_service.py`
- `services/secure_export_service.py`
- `services/upload_service.py`
- `services/persistence_service.py`
- `ui/resume_screening.py`
- `ui/results.py`

## Validation

Targeted tests prove that User B cannot read, list, delete or overwrite User A's
files even when User B knows the absolute path or workspace identifier. The full
regression suite must pass before commit.
