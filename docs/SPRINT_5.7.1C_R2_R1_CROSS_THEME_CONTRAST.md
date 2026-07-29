# Sprint 5.7.1C-R2-R1 — Cross-Theme Control Contrast Acceptance Fix

## Baseline

- RecruitOS version remains `0.7.6`.
- This is a visual-acceptance correction inside Sprint `5.7.1C-R2`; it does not introduce a new database or product version.
- ALTEN Brandbook 2025 remains the mandatory visual authority.

## Corrected defects

- Primary action labels remain white on the ALTEN blue gradient in light and dark modes.
- Secondary action labels use theme-aware foreground and panel tokens.
- Streamlit nested `p` and `span` wrappers inherit the button foreground instead of global page text colours.
- Disabled actions remain visibly inactive while retaining readable ALTEN navy text.
- Sidebar navigation, Dark mode and Sign Out retain explicit high contrast.
- `VERSION` and compound `.example` files are explicitly normalized to LF in `.gitattributes`.

## Root cause

The base theme intentionally colours general page `p` and label elements. Streamlit renders button labels inside nested text elements, and those global selectors were overriding the button foreground. The correction establishes a control-level inheritance contract after the base theme.

## Acceptance

Validate both light and dark modes for:

- Start Resume Screening
- Open Candidate Database
- Open Results when disabled
- Guided next/previous workflow actions
- Dark mode label
- Sign Out

The Git LF/CRLF messages are repository normalization notices rather than application execution failures. After the updated `.gitattributes` is staged and the affected files are renormalized, those named example-file warnings should stop recurring.
