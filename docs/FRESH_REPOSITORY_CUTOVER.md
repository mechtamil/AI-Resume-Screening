# RecruitOS Fresh Repository Cutover

This procedure creates a new Git history from the policy-approved current source.
It does not copy the old `.git` directory.

## 1. Preserve the old repository locally

```powershell
cd "C:\AI\AI Recruitment Assistant"
git status
git bundle create "C:\AI\RecruitOS_Pre_Rebaseline_Backup.bundle" --all
```

Keep the bundle outside the project and do not upload it to the fresh repository.

## 2. Validate and build the clean source package

```powershell
python -m tools.repository_policy --tracked
python -m tools.preflight
python -m unittest discover -s tests -p "test_*.py" -v
python -m tools.build_clean_release
```

The package is created under `dist/` with a SHA-256 source manifest inside it.

## 3. Extract into a new folder

```powershell
Expand-Archive `
  ".\dist\RecruitOS-v0.7.3-source.zip" `
  -DestinationPath "C:\AI\RecruitOS_Fresh" `
  -Force
```

The extracted project root is normally:

```text
C:\AI\RecruitOS_Fresh\RecruitOS-v0.7.3
```

## 4. Validate the extracted source before Git initialization

```powershell
cd "C:\AI\RecruitOS_Fresh\RecruitOS-v0.7.3"
python -m tools.repository_policy
python -m tools.preflight
python -m unittest discover -s tests -p "test_*.py" -v
```

## 5. Initialize fresh Git history

```powershell
git init
git branch -M main
git add -A
git status
git commit -m "RecruitOS 0.7.3: Clean audited repository baseline"
```

## 6. Publish

### Recommended privacy method — new GitHub repository

Create an empty GitHub repository without README, license or `.gitignore`, then:

```powershell
git remote add origin <NEW-REPOSITORY-URL>
git push -u origin main
```

Reconnect the Streamlit deployment to the new repository after the clean source
passes online smoke testing. Archive or delete the old remote only after the new
application is accepted.

### Same repository URL — history replacement

Use only after confirming the local bundle backup and repository-policy result:

```powershell
git remote add origin https://github.com/mechtamil/AI-Resume-Screening.git
git push --force --set-upstream origin main
```

Delete obsolete remote branches and tags that still reference old history. A force
push removes old commits from normal navigation but may not immediately erase all
server-side cached objects. For previously published secrets or personal data,
rotate the secrets and use the hosting provider's sensitive-data removal process.

## 7. Streamlit deployment secrets

A shared deployment must configure:

```text
RECRUITOS_ENVIRONMENT=production
RECRUITOS_INITIAL_SETUP_KEY=<long-random-secret>
```

Do not commit these values. Copy the keys from `.streamlit/secrets.toml.example` into the Streamlit secrets editor or use deployment environment variables.
