"""High-specificity cross-theme visibility corrections for RecruitOS.

The base ALTEN theme remains responsible for layout, branding, spacing,
backgrounds and animation. This module is injected after the base theme and
normalizes foreground/background contrast for Streamlit's nested control DOM.
"""
from __future__ import annotations


def build_accessibility_css() -> str:
    """Return mode-safe control, text, focus and interaction-state corrections."""
    return r"""
<style>
/*
 * RecruitOS final visibility layer.
 *
 * No page layout or hero geometry is changed here. The rules below only make
 * existing controls and text readable in both RecruitOS light and dark modes.
 */

/* -------------------------------------------------------------------------
   Keyboard focus
   ------------------------------------------------------------------------- */
.stApp button:focus-visible,
.stApp input:focus-visible,
.stApp textarea:focus-visible,
.stApp [role="radio"]:focus-visible,
.stApp [role="checkbox"]:focus-visible,
.stApp [role="tab"]:focus-visible,
.stApp [tabindex]:focus-visible {
  outline: 3px solid #7ECBEE !important;
  outline-offset: 3px !important;
  box-shadow: 0 0 0 2px #043962 !important;
}

/* -------------------------------------------------------------------------
   Login copy — preserve the approved Login design; correct text only
   ------------------------------------------------------------------------- */
.stApp .ros-login-shell p.ros-login-copy,
.stApp .ros-login-shell .ros-login-copy,
.stApp .ros-login-shell .ros-login-copy * {
  color: rgba(255, 255, 255, .90) !important;
  opacity: 1 !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, .24);
}

/* -------------------------------------------------------------------------
   Primary actions — blue surface always receives white nested label content
   ------------------------------------------------------------------------- */
.stApp .stButton > button[kind="primary"]:not(:disabled),
.stApp .stFormSubmitButton > button[kind="primary"]:not(:disabled),
.stApp button[data-testid="stBaseButton-primary"]:not(:disabled),
.stApp [data-testid="stBaseButton-primary"]:not(:disabled) {
  background: linear-gradient(
    110deg,
    var(--alten-navy),
    var(--alten-blue-mid) 58%,
    var(--alten-blue)
  ) !important;
  color: #FFFFFF !important;
  border-color: transparent !important;
  opacity: 1 !important;
}

.stApp .stButton > button[kind="primary"]:not(:disabled) *,
.stApp .stFormSubmitButton > button[kind="primary"]:not(:disabled) *,
.stApp button[data-testid="stBaseButton-primary"]:not(:disabled) *,
.stApp [data-testid="stBaseButton-primary"]:not(:disabled) * {
  color: #FFFFFF !important;
  fill: currentColor !important;
  opacity: 1 !important;
  font-weight: 750 !important;
}

/* -------------------------------------------------------------------------
   Secondary and download actions — light surface with ALTEN navy label
   ------------------------------------------------------------------------- */
.stApp .stButton > button:not([kind="primary"]):not(:disabled),
.stApp .stDownloadButton > button:not(:disabled),
.stApp [data-testid="stDownloadButton"] button:not(:disabled),
.stApp button[data-testid="stBaseButton-secondary"]:not(:disabled),
.stApp [data-testid="stBaseButton-secondary"]:not(:disabled) {
  background: linear-gradient(145deg, #FFFFFF, #EEF6FC) !important;
  color: #043962 !important;
  border: 1px solid rgba(4, 57, 98, .20) !important;
  opacity: 1 !important;
}

.stApp .stButton > button:not([kind="primary"]):not(:disabled) *,
.stApp .stDownloadButton > button:not(:disabled) *,
.stApp [data-testid="stDownloadButton"] button:not(:disabled) *,
.stApp button[data-testid="stBaseButton-secondary"]:not(:disabled) *,
.stApp [data-testid="stBaseButton-secondary"]:not(:disabled) * {
  color: #043962 !important;
  fill: currentColor !important;
  opacity: 1 !important;
  font-weight: 700 !important;
}

.stApp .stButton > button:not([kind="primary"]):not(:disabled):hover,
.stApp .stDownloadButton > button:not(:disabled):hover,
.stApp [data-testid="stDownloadButton"] button:not(:disabled):hover,
.stApp button[data-testid="stBaseButton-secondary"]:not(:disabled):hover,
.stApp [data-testid="stBaseButton-secondary"]:not(:disabled):hover {
  background: linear-gradient(145deg, #FFFFFF, #E0F2FC) !important;
  border-color: rgba(0, 139, 210, .48) !important;
}

/* -------------------------------------------------------------------------
   Disabled controls — readable inactive state in both modes
   ------------------------------------------------------------------------- */
.stApp .stButton > button:disabled,
.stApp .stFormSubmitButton > button:disabled,
.stApp .stDownloadButton > button:disabled,
.stApp [data-testid="stButton"] button:disabled,
.stApp button:disabled {
  background: linear-gradient(110deg, #D7E3EC, #EDF3F7) !important;
  color: #043962 !important;
  border: 1px solid rgba(4, 57, 98, .24) !important;
  opacity: 1 !important;
  box-shadow: none !important;
  cursor: not-allowed !important;
  filter: none !important;
  transform: none !important;
}

.stApp .stButton > button:disabled *,
.stApp .stFormSubmitButton > button:disabled *,
.stApp .stDownloadButton > button:disabled *,
.stApp [data-testid="stButton"] button:disabled *,
.stApp button:disabled * {
  color: #043962 !important;
  fill: currentColor !important;
  opacity: 1 !important;
  font-weight: 750 !important;
}

.stApp .stButton > button:disabled::after,
.stApp .stFormSubmitButton > button:disabled::after {
  display: none !important;
}

/* -------------------------------------------------------------------------
   Every file uploader — light drop zone, dark instructions, blue Upload button
   ------------------------------------------------------------------------- */
.stApp [data-testid="stFileUploaderDropzone"] {
  background: linear-gradient(145deg, #FFFFFF, #EEF6FC) !important;
  border-color: rgba(0, 139, 210, .48) !important;
}

.stApp [data-testid="stFileUploaderDropzone"] > div,
.stApp [data-testid="stFileUploaderDropzone"] p,
.stApp [data-testid="stFileUploaderDropzone"] span,
.stApp [data-testid="stFileUploaderDropzone"] small,
.stApp [data-testid="stFileUploaderDropzoneInstructions"],
.stApp [data-testid="stFileUploaderDropzoneInstructions"] * {
  color: #043962 !important;
  opacity: 1 !important;
}

.stApp [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"],
.stApp [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"],
.stApp [data-testid="stFileUploader"] button[kind="secondary"],
.stApp [data-testid="stFileUploaderDropzone"] button[kind="secondary"],
.stApp [data-testid="stFileUploaderDropzone"] button {
  min-height: 44px !important;
  padding: .55rem 1rem !important;
  border: 1px solid rgba(255, 255, 255, .18) !important;
  border-radius: 13px !important;
  background: linear-gradient(
    112deg,
    var(--alten-navy),
    var(--alten-blue-mid) 58%,
    var(--alten-blue)
  ) !important;
  color: #FFFFFF !important;
  box-shadow: 0 10px 24px rgba(0, 112, 192, .24) !important;
  opacity: 1 !important;
  font-weight: 750 !important;
  filter: none !important;
}

.stApp [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] *,
.stApp [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] *,
.stApp [data-testid="stFileUploader"] button[kind="secondary"] *,
.stApp [data-testid="stFileUploaderDropzone"] button[kind="secondary"] *,
.stApp [data-testid="stFileUploaderDropzone"] button * {
  color: #FFFFFF !important;
  fill: currentColor !important;
  opacity: 1 !important;
  font-weight: inherit !important;
}

/* Uploaded-file remove action.

   Streamlit versions differ here: some attach stFileUploaderDeleteBtn directly
   to the button, while others expose it on a wrapper around the button. The
   aria-label fallback is limited to file uploaders and preserves the accessible
   "Remove <filename>" name. */
.stApp [data-testid="stFileUploader"] button[data-testid="stFileUploaderDeleteBtn"],
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] > button,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] button,
.stApp [data-testid="stFileUploader"] button[aria-label^="Remove "] {
  position: relative !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 44px !important;
  min-width: 44px !important;
  max-width: 44px !important;
  height: 44px !important;
  min-height: 44px !important;
  max-height: 44px !important;
  padding: 0 !important;
  border: 2px solid #E30513 !important;
  border-radius: 12px !important;
  background: #FFFFFF !important;
  color: #E30513 !important;
  opacity: 1 !important;
  box-shadow: 0 8px 18px rgba(227, 5, 19, .18) !important;
  overflow: hidden !important;
}

/* Hide Streamlit's native icon but keep the button and aria-label intact. */
.stApp [data-testid="stFileUploader"] button[data-testid="stFileUploaderDeleteBtn"] > *,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] > button > *,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] button > *,
.stApp [data-testid="stFileUploader"] button[aria-label^="Remove "] > * {
  opacity: 0 !important;
  visibility: hidden !important;
}

/* Render a reliable red X on the actual clickable button. */
.stApp [data-testid="stFileUploader"] button[data-testid="stFileUploaderDeleteBtn"]::after,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] > button::after,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] button::after,
.stApp [data-testid="stFileUploader"] button[aria-label^="Remove "]::after {
  content: "X" !important;
  position: absolute !important;
  inset: 0 !important;
  display: grid !important;
  place-items: center !important;
  color: #E30513 !important;
  font-family: Arial, "Segoe UI", sans-serif !important;
  font-size: 1.15rem !important;
  line-height: 1 !important;
  font-weight: 900 !important;
  opacity: 1 !important;
  visibility: visible !important;
  pointer-events: none !important;
}

.stApp [data-testid="stFileUploader"] button[data-testid="stFileUploaderDeleteBtn"]:hover,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] > button:hover,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] button:hover,
.stApp [data-testid="stFileUploader"] button[aria-label^="Remove "]:hover {
  background: #FFF1F2 !important;
  border-color: #C90010 !important;
  color: #C90010 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 10px 22px rgba(227, 5, 19, .26) !important;
}

.stApp [data-testid="stFileUploader"] button[data-testid="stFileUploaderDeleteBtn"]:hover::after,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] > button:hover::after,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] button:hover::after,
.stApp [data-testid="stFileUploader"] button[aria-label^="Remove "]:hover::after {
  color: #C90010 !important;
}

.stApp [data-testid="stFileUploader"] button[data-testid="stFileUploaderDeleteBtn"]:focus-visible,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] > button:focus-visible,
.stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] button:focus-visible,
.stApp [data-testid="stFileUploader"] button[aria-label^="Remove "]:focus-visible {
  outline: 3px solid rgba(227, 5, 19, .34) !important;
  outline-offset: 3px !important;
  box-shadow: 0 0 0 2px #FFFFFF, 0 0 0 5px rgba(227, 5, 19, .30) !important;
}

/* -------------------------------------------------------------------------
   Expanders — mode-aware surface and readable header text/icons
   ------------------------------------------------------------------------- */
.stApp [data-testid="stExpander"] details,
.stApp [data-testid="stExpander"] summary,
.stApp details[data-testid="stExpander"] summary {
  background: var(--ros-panel-strong) !important;
  color: var(--ros-text) !important;
  border-color: var(--ros-line) !important;
}

.stApp [data-testid="stExpander"] summary *,
.stApp details[data-testid="stExpander"] summary * {
  color: var(--ros-text) !important;
  fill: currentColor !important;
  opacity: 1 !important;
}

/* -------------------------------------------------------------------------
   Tabs — rounded rail, readable inactive state and clear selected state
   ------------------------------------------------------------------------- */
.stApp .stTabs [data-baseweb="tab-list"],
.stApp .stTabs [role="tablist"],
.stApp [data-testid="stTabs"] [data-baseweb="tab-list"],
.stApp [data-testid="stTabs"] [role="tablist"] {
  display: flex !important;
  gap: .42rem !important;
  padding: .45rem !important;
  margin: .15rem 0 1rem !important;
  border: 1px solid var(--ros-line) !important;
  border-radius: 18px !important;
  background: var(--ros-panel-strong) !important;
  box-shadow: 0 14px 34px rgba(4, 57, 98, .10) !important;
  overflow-x: auto !important;
  scrollbar-width: thin;
}

.stApp .stTabs [data-baseweb="tab"],
.stApp .stTabs button[role="tab"],
.stApp [data-testid="stTabs"] [data-baseweb="tab"],
.stApp [data-testid="stTabs"] button[role="tab"] {
  min-height: 44px !important;
  padding: .62rem .95rem !important;
  border: 1px solid transparent !important;
  border-radius: 13px !important;
  background: rgba(0, 139, 210, .06) !important;
  color: var(--ros-text) !important;
  opacity: 1 !important;
  font-weight: 720 !important;
}

.stApp .stTabs [data-baseweb="tab"] *,
.stApp .stTabs button[role="tab"] *,
.stApp [data-testid="stTabs"] [data-baseweb="tab"] *,
.stApp [data-testid="stTabs"] button[role="tab"] * {
  color: inherit !important;
  opacity: 1 !important;
  font-weight: inherit !important;
}

.stApp .stTabs [data-baseweb="tab"]:hover,
.stApp .stTabs button[role="tab"]:hover,
.stApp [data-testid="stTabs"] [data-baseweb="tab"]:hover,
.stApp [data-testid="stTabs"] button[role="tab"]:hover {
  background: rgba(0, 139, 210, .14) !important;
  color: var(--ros-text) !important;
  border-color: rgba(0, 139, 210, .30) !important;
}

.stApp .stTabs [data-baseweb="tab"][aria-selected="true"],
.stApp .stTabs button[role="tab"][aria-selected="true"],
.stApp [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
.stApp [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background: linear-gradient(
    112deg,
    var(--alten-navy),
    var(--alten-blue-mid) 58%,
    var(--alten-blue)
  ) !important;
  color: #FFFFFF !important;
  border-color: transparent !important;
  opacity: 1 !important;
  box-shadow:
    0 10px 24px rgba(0, 112, 192, .26),
    inset 0 -3px 0 var(--alten-yellow) !important;
}

.stApp .stTabs [aria-selected="true"] *,
.stApp [data-testid="stTabs"] [aria-selected="true"] * {
  color: #FFFFFF !important;
  opacity: 1 !important;
}

/* Streamlit/BaseWeb compatibility: selected state can be rendered outside
   the historical .stTabs wrapper. Keep this selector broad but role-specific. */
.stApp [role="tab"][aria-selected="true"],
.stApp [data-baseweb="tab"][aria-selected="true"] {
  background-color: #0070C0 !important;
  background-image: linear-gradient(
    112deg,
    #043962,
    #0070C0 58%,
    #008BD2
  ) !important;
  color: #FFFFFF !important;
  border-color: transparent !important;
  opacity: 1 !important;
  box-shadow:
    0 10px 24px rgba(0, 112, 192, .26),
    inset 0 -3px 0 #FFED00 !important;
}

.stApp [role="tab"][aria-selected="true"] *,
.stApp [data-baseweb="tab"][aria-selected="true"] * {
  color: #FFFFFF !important;
  fill: currentColor !important;
  opacity: 1 !important;
  font-weight: 750 !important;
}

.stApp [role="tab"][aria-selected="false"],
.stApp [data-baseweb="tab"][aria-selected="false"] {
  color: var(--ros-text) !important;
  background-color: rgba(0, 139, 210, .06) !important;
  opacity: 1 !important;
}

.stApp [role="tab"][aria-selected="false"] *,
.stApp [data-baseweb="tab"][aria-selected="false"] * {
  color: var(--ros-text) !important;
  opacity: 1 !important;
}

.stApp .stTabs [data-baseweb="tab-highlight"],
.stApp .stTabs [data-baseweb="tab-border"],
.stApp [data-testid="stTabs"] [data-baseweb="tab-highlight"],
.stApp [data-testid="stTabs"] [data-baseweb="tab-border"] {
  display: none !important;
}

/* -------------------------------------------------------------------------
   Form fields, placeholders and select/list options
   ------------------------------------------------------------------------- */
.stApp input,
.stApp textarea,
.stApp [data-baseweb="select"] > div,
.stApp [data-baseweb="select"] input {
  color: var(--ros-text) !important;
}

.stApp input::placeholder,
.stApp textarea::placeholder {
  color: var(--ros-muted) !important;
  opacity: 1 !important;
}

[data-baseweb="popover"] [role="listbox"],
[data-baseweb="menu"] {
  background: var(--ros-panel-strong) !important;
  color: var(--ros-text) !important;
}

[data-baseweb="popover"] [role="option"],
[data-baseweb="menu"] [role="option"],
[data-baseweb="popover"] [role="option"] * {
  color: var(--ros-text) !important;
  opacity: 1 !important;
}

/* -------------------------------------------------------------------------
   Sidebar navigation, footer caption, Dark mode and Sign Out
   ------------------------------------------------------------------------- */
[data-testid="stSidebar"] [data-testid="stRadio"] label,
[data-testid="stSidebar"] [data-testid="stRadio"] label *,
[data-testid="stSidebar"] [role="radiogroup"] label,
[data-testid="stSidebar"] [role="radiogroup"] label *,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  color: rgba(255, 255, 255, .94) !important;
  opacity: 1 !important;
  text-shadow: 0 1px 1px rgba(0, 0, 0, .16);
}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .stCaption * {
  color: rgba(255, 255, 255, .76) !important;
  opacity: 1 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
  min-height: 44px;
  padding: .62rem .7rem !important;
  border-radius: 12px !important;
  border: 1px solid transparent !important;
  cursor: pointer;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background: rgba(255, 255, 255, .12) !important;
  border-color: rgba(255, 255, 255, .18) !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:focus-within {
  background: rgba(126, 203, 238, .16) !important;
  border-color: #7ECBEE !important;
  box-shadow: 0 0 0 3px rgba(126, 203, 238, .18);
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
  background: linear-gradient(
    105deg,
    rgba(0, 139, 210, .34),
    rgba(126, 203, 238, .13)
  ) !important;
  border-color: rgba(126, 203, 238, .62) !important;
  box-shadow: inset 4px 0 0 #7ECBEE, 0 10px 24px rgba(0, 0, 0, .12);
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked),
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) * {
  color: #FFFFFF !important;
  font-weight: 750 !important;
}

[data-testid="stSidebar"] .st-key-dark_mode label,
[data-testid="stSidebar"] .st-key-dark_mode label * {
  color: #FFFFFF !important;
  opacity: 1 !important;
}

section[data-testid="stSidebar"] .st-key-sidebar_sign_out button,
section[data-testid="stSidebar"] .st-key-sidebar_sign_out [data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] [class*="st-key-sidebar_sign_out"] button,
[data-testid="stSidebar"] [class*="st-key-sidebar_sign_out"] [data-testid="stBaseButton-secondary"] {
  min-height: 44px !important;
  background: linear-gradient(110deg, #043962, #0070C0 60%, #008BD2) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(255, 255, 255, .28) !important;
  opacity: 1 !important;
  box-shadow: 0 10px 22px rgba(0, 0, 0, .18) !important;
}

section[data-testid="stSidebar"] .st-key-sidebar_sign_out button *,
section[data-testid="stSidebar"] .st-key-sidebar_sign_out [data-testid="stBaseButton-secondary"] *,
[data-testid="stSidebar"] [class*="st-key-sidebar_sign_out"] button *,
[data-testid="stSidebar"] [class*="st-key-sidebar_sign_out"] [data-testid="stBaseButton-secondary"] * {
  color: #FFFFFF !important;
  fill: currentColor !important;
  opacity: 1 !important;
  font-weight: 750 !important;
}

/* Keep footer actions at the bottom without overlaying navigation. */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] >
[data-testid="stElementContainer"]:has(.ros-sidebar-footer-marker) {
  margin-top: auto !important;
}

.ros-sidebar-footer-marker { min-height: 1rem; }
.st-key-dark_mode { margin-top: 0 !important; }
.st-key-sidebar_sign_out {
  position: static !important;
  bottom: auto !important;
  padding-top: .35rem !important;
  padding-bottom: 1rem !important;
}

/* -------------------------------------------------------------------------
   Guidance
   ------------------------------------------------------------------------- */
.ros-action-guidance {
  margin: .8rem 0;
  padding: .9rem 1rem;
  border-radius: 14px;
  color: #043962 !important;
  background: rgba(126, 203, 238, .22);
  border: 1px solid rgba(0, 139, 210, .34);
  line-height: 1.45;
}

.ros-action-guidance,
.ros-action-guidance * {
  color: #043962 !important;
  opacity: 1 !important;
}

/* -------------------------------------------------------------------------
   Responsive and operating-system accessibility
   ------------------------------------------------------------------------- */
@media (forced-colors: active) {
  .stApp button,
  [data-testid="stSidebar"] [data-testid="stRadio"] label {
    border: 1px solid ButtonText !important;
  }

  .stApp button:focus-visible,
  [data-testid="stSidebar"] [data-testid="stRadio"] label:focus-within {
    outline: 2px solid Highlight !important;
  }
}

@media (max-width: 760px) {
  [data-testid="stSidebar"] [data-testid="stRadio"] label {
    min-height: 48px;
  }

  .stApp .stTabs [data-baseweb="tab-list"],
  .stApp .stTabs [role="tablist"],
  .stApp [data-testid="stTabs"] [data-baseweb="tab-list"],
  .stApp [data-testid="stTabs"] [role="tablist"] {
    padding: .35rem !important;
    gap: .3rem !important;
  }

  .stApp .stTabs [data-baseweb="tab"],
  .stApp .stTabs button[role="tab"],
  .stApp [data-testid="stTabs"] [data-baseweb="tab"],
  .stApp [data-testid="stTabs"] button[role="tab"] {
    min-height: 42px !important;
    padding: .55rem .78rem !important;
  }

  .ros-action-guidance { padding: .85rem; }
}
</style>
"""


def apply_accessibility_overrides() -> None:
    """Inject visibility corrections after the base ALTEN theme."""
    import streamlit as st

    st.markdown(build_accessibility_css(), unsafe_allow_html=True)
