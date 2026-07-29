# ALTEN UI Governance for RecruitOS

## Mandatory authority

Every RecruitOS visual change must be reviewed against the official ALTEN Brandbook 2025:

`https://www.alten.com/wp-content/uploads/2026/02/Brandbook-ALTEN-2025-EN.pdf`

The official brandbook is the source of truth. Repository guidance, UI/UX reference material, Streamlit defaults, third-party component libraries and designer preference cannot override it.

## Decision order

1. ALTEN Brandbook 2025
2. RecruitOS security, privacy and accessibility requirements
3. Central RecruitOS brand tokens and reusable components
4. Streamlit-compatible implementation constraints
5. UI/UX Pro Max and 21st.dev as supporting references only

## Implementation rules

- Use only approved ALTEN logos and asset variants.
- Keep brand colours centralized in `config/brand.py`.
- Do not invent or approximate unverified logo, typography, spacing or colour rules.
- Preserve at least WCAG AA text contrast for normal text and interactive states.
- Keep keyboard focus visible.
- Provide readable hover, selected, disabled, error and success states.
- Respect `prefers-reduced-motion`.
- Validate responsive layouts at narrow mobile, tablet, desktop and wide-desktop widths.
- Never send candidate data, customer documents or private ALTEN material to third-party design services.

## Pre-delivery UI checklist

- [ ] Official ALTEN brandbook reviewed for the affected component.
- [ ] Logo usage and clear space preserved.
- [ ] Text is readable in light and dark modes.
- [ ] Sidebar navigation labels remain visible in default, hover, selected and focus states.
- [ ] Disabled actions remain readable and explain how to continue.
- [ ] Sign Out remains visible and reachable without covering navigation.
- [ ] Keyboard focus is visible.
- [ ] Motion is reduced when the browser requests reduced motion.
- [ ] No candidate or customer data is shared with external UI services.
