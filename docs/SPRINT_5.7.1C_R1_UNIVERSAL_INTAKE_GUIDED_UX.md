# Sprint 5.7.1C-R1 — Universal Intake Templates & Guided Workspace UX

## Release

- Version: `0.7.5`
- Database schema: `5` unchanged
- Purpose: accept common recruiter document formats and turn the Streamlit workspace into a guided operational flow.

## Accepted formats

- PDF, DOCX, TXT
- XLSX, XLS, CSV
- PNG, JPG, JPEG, WEBP, TIF, TIFF

Images and scanned PDF pages use OCR. Linux/Streamlit Cloud installs `tesseract-ocr` from `packages.txt`.

## Templates

RecruitOS generates a structured JD workbook and a supplemental skill workbook. The skill workbook distinguishes Mandatory and Preferred requirements. Templates improve extraction completeness; they do not bypass configured scoring.

## UX

- real private workspace counts on Home
- direct Start Screening, Results and Candidate Database actions
- guided Prepare → Screen → Review → Export stepper
- previous/next workflow footer
- compact identity card without duplicate values
- light/dark appearance toggle
- bottom sidebar Sign Out

## Security

All new formats still pass through authenticated private storage, extension validation, size limits and tenant/user/workspace ownership checks. OCR and spreadsheet extraction occur only after private persistence.
