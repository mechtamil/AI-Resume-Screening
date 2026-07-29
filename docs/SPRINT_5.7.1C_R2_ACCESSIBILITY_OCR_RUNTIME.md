# Sprint 5.7.1C-R2 — Accessibility, Brand Governance & Portable OCR Runtime

## Release

- Application version: `0.7.6`
- Database schema: `5` (unchanged)
- Previous release: `0.7.5`
- Next planned sprint: `5.7.1D — Explicit Reader Sharing & Review Assignment`

## Scope

### Accessible Streamlit shell

- Correct low-contrast sidebar navigation text.
- Add explicit selected, hover and keyboard-focus states.
- Keep Dark mode and Sign Out readable.
- Anchor footer controls without overlaying navigation.
- Keep disabled primary actions readable.
- Explain the inputs required before candidate analysis can start.
- Add forced-colour and mobile safeguards.

### Portable OCR runtime

- Add optional `RECRUITOS_TESSERACT_CMD`.
- Resolve an explicit executable from deployment configuration.
- Fall back to `tesseract` on the operating-system PATH.
- Keep local user paths out of source code.
- Preserve Streamlit Cloud discovery through `packages.txt`.

### Brand governance

- Record the official ALTEN Brandbook 2025 as mandatory visual authority.
- Keep UI/UX Pro Max and 21st.dev as supporting references only.
- Add a repository-level accessibility and privacy checklist.

## Acceptance criteria

- Sidebar labels remain readable in light and dark workspace modes.
- Selected navigation is visually distinct.
- Dark mode and Sign Out remain visible at the bottom of the sidebar.
- Disabled analysis action uses readable contrast.
- Missing input guidance identifies the exact next action.
- Local Windows OCR works through `RECRUITOS_TESSERACT_CMD` or PATH.
- No user-specific Tesseract path exists in tracked source.
- Targeted tests, full regression, preflight and repository policy pass.
