# Files to remove during Sprint 5.7.1B-R1

Remove these obsolete/local files from the existing working repository before the
sprint commit:

```powershell
git rm --ignore-unmatch ".github/workflows/tests.yml"
git rm --ignore-unmatch "README_APPLY.txt"
git rm --ignore-unmatch "PACKAGE_MANIFEST_SHA256.txt"
Remove-Item "README_APPLY.txt" -Force -ErrorAction SilentlyContinue
Remove-Item "PACKAGE_MANIFEST_SHA256.txt" -Force -ErrorAction SilentlyContinue
```

Remove tracked generated/runtime files from the Git index without deleting local
working data:

```powershell
$tracked = git ls-files
$forbidden = $tracked | Where-Object {
    $_ -match '(^|/)(__pycache__/|.*\.py[co]$)' -or
    $_ -match '^(uploads|output|temp|logs|Resume)/' -and $_ -notmatch '/\.gitkeep$' -or
    $_ -match '\.(db|sqlite|sqlite3)$' -or
    $_ -match '^JD/.*\.(pdf|docx)$' -or
    $_ -match '^Master_Data/.*_master\.xlsx$'
}
$forbidden | ForEach-Object { git rm --cached --ignore-unmatch -- "$_" }
```

Do not delete local CVs or databases until a separate retention/backup decision is
made. The commands above remove them from source-control tracking only.
