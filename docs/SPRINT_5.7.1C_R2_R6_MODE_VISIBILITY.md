# Sprint 5.7.1C-R2-R6 — Mode-Safe Control Visibility

## Scope

This corrective increment keeps the accepted RecruitOS page layouts and ALTEN
visual design. It changes only the final accessibility stylesheet so Streamlit
nested labels cannot become unreadable when switching between light and dark
modes.

## Corrected controls

- enabled primary buttons and nested labels
- secondary and download buttons
- disabled buttons
- file-uploader drop zones, instructions, icons and Upload buttons
- expander headers
- tabs and selected/inactive tab labels
- form placeholders and select-menu options
- sidebar version caption
- Dark mode control and Sign Out
- Login description text

## Root cause

Streamlit renders visible control labels inside nested `p`, `span`, `div` and SVG
elements. Broad page-level text rules and Streamlit's light component surfaces
could therefore create dark-on-blue or white-on-white combinations. The final
stylesheet now assigns foreground colours to both the control and all of its
nested label/icon nodes.

## Boundary

No business logic, page structure, Login layout, Home layout, navigation flow,
scoring, persistence, authentication or database schema is changed.
