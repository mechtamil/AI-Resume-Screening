# Sprint 5.7.1C — Tenant-Specific Configuration & AI-Ready Taxonomy Foundation

## Objective

Prevent one user's skills, aliases, qualifications, scoring weights or recommendation rules from affecting another user's screening result.

## Runtime model

```text
System default workbook
        |
        +--> private tenant version 1
        +--> private tenant version 2
        +--> private tenant version N
                    |
                    v
            active version resolver
                    |
                    v
         request-local ConfigurationContext
                    |
                    v
      parser -> matcher -> score -> recommendation
                    |
                    v
        immutable screening configuration snapshot
```

## Core controls

- validated `.xlsx` uploads only;
- 10 MB file limit;
- immutable version directories;
- SHA-256 duplicate and tamper detection;
- RBAC-controlled publication and activation;
- Tenant Admin country/location scope;
- context-local configuration selection;
- workbook cache partitioned by file identity;
- system-default fallback;
- activation and rollback audit events;
- screening session stores version, fingerprint and sheet summary.

## Database schema 5

Adds `tenant_configuration_versions` and the following screening-session fields:

- `configuration_version_id`
- `configuration_sha256`
- `configuration_snapshot_json`

## Acceptance commands

```powershell
python -m unittest `
    tests.test_configuration_context `
    tests.test_tenant_configuration_service `
    tests.test_configuration_screening_isolation `
    tests.test_configuration_snapshot_persistence `
    -v

python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q app.py config database JD models parser reports services tests tools ui utils
python -m tools.preflight
```

## Production boundary

The current Streamlit deployment still uses local SQLite and local runtime storage. Logical tenant isolation is implemented, but durable managed database/object storage remains a later production-hardening milestone.
