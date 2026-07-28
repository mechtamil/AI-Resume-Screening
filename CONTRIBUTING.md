# Contributing to RecruitOS

## Development gate

Before committing:

```powershell
python -m tools.preflight
python -m tools.repository_policy --tracked
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q app.py config database JD models parser reports services tests tools ui utils
```

## Commit scope

Each sprint commit must include:

- complete production files rather than partial fragments;
- automated tests for changed behavior;
- `VERSION`, `CHANGELOG.md`, `ROADMAP.md` and applicable architecture updates;
- no runtime, personal, secret or generated files.

## Clean source release

After the branch is committed and clean:

```powershell
python -m tools.build_clean_release
```

The generated ZIP is written below `dist/` and is intentionally ignored by Git.
