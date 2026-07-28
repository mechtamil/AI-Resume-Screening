# Git Remediation Instructions for Milestone 5.6.A

The stabilized source package intentionally does **not** contain the embedded `.git` directory. Keep your existing local repository history and overlay the stabilized source only after taking a backup.

## Recommended procedure in PowerShell

From `C:\AI`:

```powershell
Copy-Item "AI Recruitment Assistant" "AI Recruitment Assistant_BACKUP_2026-07-24" -Recurse
```

Extract the stabilized ZIP to a separate folder, review it, then copy its contents over your existing repository **without replacing `.git`**.

After the overlay, from `C:\AI\AI Recruitment Assistant`:

```powershell
git status
python -m tools.preflight
python -m unittest discover -s tests -p "test_*.py" -v
```

Remove obsolete/tracked runtime or legacy artifacts from the Git index/tree if they still exist in your repository:

```powershell
git rm --ignore-unmatch parser/extractors/skills_extractor.py
git rm --cached --ignore-unmatch database/recruitos.db
git rm --cached --ignore-unmatch logs/application.log
git rm --cached --ignore-unmatch Resume/*.pdf
git rm --cached --ignore-unmatch JD/*.pdf
git rm --cached --ignore-unmatch Master_Data/skills_master.xlsx
```

Remove tracked Python caches using Git pathspecs:

```powershell
git rm -r --cached --ignore-unmatch ':(glob)**/__pycache__/**'
git rm --cached --ignore-unmatch ':(glob)**/*.pyc'
```

The populated legacy separate workbooks (`*_master.xlsx`) are retired. Relevant populated skill/certification data was migrated into `Master_Data/RecruitOS_Configuration.xlsx` in the stabilized package.

Then review the full intended remediation:

```powershell
git status
git diff --stat
git diff
```

Once the preflight and all tests pass and the changes are reviewed:

```powershell
git add -A
git status
git diff --cached --stat
git commit -m "Milestone 5.6.A: Audit remediation and codebase stabilization"
git push
```

Do not use history-rewriting commands for sensitive files without first deciding whether the remote Git history itself must be purged. Removing a file in a new commit prevents future tracking but does not erase it from old commits.
