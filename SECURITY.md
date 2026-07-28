# RecruitOS Security Policy

RecruitOS processes personal and recruitment data. Source control must never contain
real candidate CVs, runtime databases, authentication secrets, generated reports,
application logs, or plaintext credentials.

## Reporting a vulnerability

Report suspected vulnerabilities privately to the RecruitOS System Owner or the
ALTEN security contact designated for the deployment. Do not create a public GitHub
issue containing credentials, candidate data, exploit details, or confidential logs.

## Supported development line

Security fixes are applied to the current `main` branch. Development deployments must
be upgraded to the latest accepted sprint before testing with non-synthetic data.

## Repository rules

The following are prohibited from Git:

- `.env` and `.streamlit/secrets.toml`
- private keys, certificates and access tokens
- SQLite databases and database backups
- uploaded resumes and job descriptions
- generated Excel reports and temporary files
- application logs and Python cache files
- package-overlay helper files and release ZIPs

Run this before every release:

```powershell
python -m tools.repository_policy --tracked
```

## Initial System Owner setup

Shared or public deployments must define both:

```text
RECRUITOS_ENVIRONMENT=production
RECRUITOS_INITIAL_SETUP_KEY=<long-random-secret>
```

RecruitOS reads environment variables first and Streamlit secrets second. Use the Streamlit secrets editor for the hosted application; never commit `.streamlit/secrets.toml`. RecruitOS fails closed when the initial setup key is absent in a shared deployment.
The local insecure bootstrap option is only for isolated developer machines.
