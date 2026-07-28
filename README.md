# RecruitOS

RecruitOS is ALTEN's configuration-driven AI Resume Screening and Recruitment Platform under active development.

## Current version

`0.7.4` — Sprint `5.7.1C: Tenant-Specific Configuration & AI-Ready Taxonomy Foundation`

## Current capabilities

- premium responsive ALTEN-aligned Streamlit experience
- admin-provisioned User ID/password authentication
- five-role RBAC model
- mandatory first-login password reset
- single-user and Excel bulk user creation
- private project/session/candidate/result persistence
- system-default plus immutable tenant-specific configuration versions
- resume/JD parsing, matching, scoring, recommendations and ranking
- ranked Excel screening export
- tenant/user/workspace-isolated uploads, temporary files and reports
- configuration snapshot provenance for every screening
- repository policy, clean source-release builder and CI quality gate

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m tools.preflight
python -m unittest discover -s tests -p "test_*.py" -v
streamlit run app.py
```

A shared deployment must configure `RECRUITOS_INITIAL_SETUP_KEY` before the first System Owner can be created. Deployment values may be supplied through environment variables or Streamlit secrets; see `.streamlit/secrets.toml.example`. After the owner exists, there is no public account-creation page.

## Login contract

```text
User ID
Password
Sign In
Forgot Password?
```

Organization, Country/Location and Region are not login fields. Country/Location remains an administrative profile and Tenant Admin scope.

## Administration

System Owner, Global Admin and Tenant Admin users can access User Management according to their role. User accounts may be created individually or imported from the supplied Excel template. Existing passwords cannot be exported; only access metadata and immediate one-time temporary credentials can be downloaded.

## Configuration

The system default is `Master_Data/RecruitOS_Configuration.xlsx`. Authorized administrators can publish and activate validated immutable versions for a private workspace from the Configuration page. Every screening stores the exact configuration fingerprint used.

## Documentation

- `PROJECT_SPEC.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- `TODO.md`
- `docs/CODEBASE_MAP.md`
- `docs/SPRINT_5.7.1A_R1_ADMIN_RBAC_BRAND.md`
- `docs/SPRINT_5.7.1B_SECURE_FILE_EXPORT_ISOLATION.md`
- `docs/SPRINT_5.7.1B_R1_REPOSITORY_REBASELINE.md`
- `docs/SPRINT_5.7.1C_TENANT_CONFIGURATION.md`
- `docs/AI_REFERENCE_ADOPTION.md`

## Repository and release gate

Before every push or clean source release:

```powershell
python -m tools.repository_policy --tracked
python -m tools.preflight
python -m unittest discover -s tests -p "test_*.py" -v
```

Build a source-only package only after Git is clean:

```powershell
python -m tools.build_clean_release
```

RecruitOS still requires explicit Reader sharing and production database/object-storage hardening before a global v1.0 release.
