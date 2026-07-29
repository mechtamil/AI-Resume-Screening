# Sprint 5.7.1C-R2-R7 — Interaction Clarity & Uploaded File Control Visibility

## Objective

Complete the remaining RecruitOS cross-theme interaction corrections without changing the approved page layouts, login composition, scoring behaviour, persistence flow or authorization model.

## Delivered corrections

### Selected tabs

The final accessibility layer now targets Streamlit/BaseWeb tab roles directly in addition to historical wrapper selectors. Selected tabs receive an explicit ALTEN blue background, white text and yellow lower accent. Inactive tabs inherit the current mode text token.

### Ranked-results navigation

The in-page `View Ranked Results →` button was removed from Resume Screening. It duplicated the persistent Results workflow action already rendered by `app.py`. After a successful screening, the page now tells the user to use the Results action below.

### Uploaded-file remove action

The file-uploader delete control keeps its accessible `aria-label`, while RecruitOS draws a visible high-contrast multiplication mark (`×`) over the button. This avoids blank or invisible remove icons in either theme and provides a 44 × 44 px interaction target.

## Files

- `ui/accessibility.py`
- `ui/resume_screening.py`
- `tests/test_accessibility_contract.py`
- `tests/test_guided_ui_contract.py`

## Version

The application version remains `0.7.6` because this is the final acceptance correction within Sprint `5.7.1C-R2`.

## Acceptance criteria

- Selected tab label is visible in light and dark modes.
- Selected tab surface is clearly blue.
- Inactive tab labels are readable.
- Uploaded-file remove action shows a visible `×` mark.
- Remove action retains its accessible button label.
- `View Ranked Results →` is absent from Resume Screening.
- The persistent workflow Results action remains available after successful analysis.
- Login, Home, scoring, persistence and authorization behaviour remain unchanged.
