# Sprint 5.7.1A-R1 — Admin-Provisioned Identity, RBAC & ALTEN Experience

## Objective

Replace self-registration with controlled enterprise provisioning, implement the approved five-role access model, enforce first-login credential lifecycle and create a premium ALTEN-aligned visual system.

## Approved login

The login page contains only User ID, Password, Sign In and Forgot Password. Organization, Country/Location and Region are intentionally absent.

## Provisioning

- Single user through Administration.
- Bulk users through downloadable Excel template.
- Required: User ID, Full Name, Email, Role, Country or Location.
- Optional: Time Zone, Department, Business Unit, Manager User ID, validity dates and Temporary Password.
- Blank Temporary Password generates a unique value.
- Plaintext temporary credentials are available only in the immediate result/export.

## Roles

- System Owner
- Global Admin
- Tenant Admin
- User
- Reader

RBAC controls actions; ownership controls records. Administrative users do not automatically see another User's private candidate content.

## Credential lifecycle

Default temporary expiry is seven days and is configurable through `RECRUITOS_TEMP_PASSWORD_EXPIRY_DAYS`. A value of zero disables expiry. Temporary login forces immediate password change before any application page becomes available.

## Visual system

- Official ALTEN palette centralized in `config/brand.py`.
- Reusable visual components in `ui/brand_components.py`.
- CSS-only ambient motion, glass panels, animated signals, button shimmer and responsive page heroes in `ui/theme.py`.
- Reduced-motion accessibility is respected.
- Local approved logo assets may be placed in `assets/brand`; official media-library URLs are fallback sources.

## Database migration

Schema version 4 adds employee User ID, RBAC, account lifecycle, audit, import and reset-request structures. The migration is idempotent and preserves existing data.

## Acceptance evidence

- complete unittest suite passes
- Python compileall passes
- preflight passes
- Streamlit browser experience requires local validation because Streamlit is not installed in the packaging runtime

## Deployment boundary

This sprint secures identity and database records. File/export isolation remains the next mandatory sprint.
