"""Central ALTEN-inspired visual system for RecruitOS Streamlit pages."""
from __future__ import annotations

from config.brand import (
    ALTEN_AMBER,
    ALTEN_BLACK,
    ALTEN_BLUE,
    ALTEN_BLUE_DEEP,
    ALTEN_BLUE_ICE,
    ALTEN_BLUE_MID,
    ALTEN_BLUE_SKY,
    ALTEN_DARK_GREY,
    ALTEN_GREY,
    ALTEN_LIGHT_BLUE,
    ALTEN_NAVY,
    ALTEN_PALE_GREY,
    ALTEN_RED,
    ALTEN_SILVER,
    ALTEN_WHITE,
    ALTEN_YELLOW,
)


def build_theme_css() -> str:
    """Return the complete RecruitOS visual theme.

    Animations are intentionally CSS-only, GPU-friendly, and disabled when a
    user has enabled reduced-motion accessibility preferences.
    """
    return f"""
<style>
:root {{
  --alten-navy: {ALTEN_NAVY};
  --alten-blue: {ALTEN_BLUE};
  --alten-blue-deep: {ALTEN_BLUE_DEEP};
  --alten-blue-mid: {ALTEN_BLUE_MID};
  --alten-blue-sky: {ALTEN_BLUE_SKY};
  --alten-blue-ice: {ALTEN_BLUE_ICE};
  --alten-light-blue: {ALTEN_LIGHT_BLUE};
  --alten-red: {ALTEN_RED};
  --alten-yellow: {ALTEN_YELLOW};
  --alten-amber: {ALTEN_AMBER};
  --alten-black: {ALTEN_BLACK};
  --alten-dark-grey: {ALTEN_DARK_GREY};
  --alten-grey: {ALTEN_GREY};
  --alten-silver: {ALTEN_SILVER};
  --alten-pale-grey: {ALTEN_PALE_GREY};
  --alten-white: {ALTEN_WHITE};
  --ros-bg: #f4f8fc;
  --ros-panel: rgba(255,255,255,.86);
  --ros-panel-strong: rgba(255,255,255,.96);
  --ros-line: rgba(4,57,98,.12);
  --ros-shadow: 0 24px 64px rgba(4,57,98,.14);
  --ros-shadow-hover: 0 30px 78px rgba(4,57,98,.22);
  --ros-radius-xl: 28px;
  --ros-radius-lg: 20px;
  --ros-radius-md: 14px;
}}

html, body, [class*="css"] {{
  font-family: Inter, "Segoe UI", Arial, sans-serif;
}}

.stApp {{
  background:
    radial-gradient(circle at 8% 4%, rgba(126,203,238,.30), transparent 28%),
    radial-gradient(circle at 90% 10%, rgba(0,139,210,.20), transparent 25%),
    linear-gradient(145deg, #f9fcff 0%, #eef6fc 48%, #f7f9fc 100%);
  color: var(--alten-navy);
}}

[data-testid="stHeader"] {{
  background: rgba(255,255,255,.58);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(4,57,98,.08);
}}

[data-testid="stAppViewContainer"] > .main {{
  background: transparent;
}}

.block-container {{
  max-width: 1480px;
  padding-top: 2rem;
  padding-bottom: 4rem;
}}

/* Animated ambient canvas */
.ros-ambient {{
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}}
.ros-orb {{
  position: absolute;
  border-radius: 999px;
  filter: blur(2px);
  opacity: .38;
  animation: ros-float 15s ease-in-out infinite;
}}
.ros-orb.one {{
  width: 340px; height: 340px; left: -110px; top: 12%;
  background: radial-gradient(circle at 30% 30%, rgba(126,203,238,.95), rgba(0,139,210,.08));
}}
.ros-orb.two {{
  width: 420px; height: 420px; right: -180px; top: 1%;
  background: radial-gradient(circle at 40% 35%, rgba(0,139,210,.60), rgba(4,57,98,.04));
  animation-delay: -4s;
}}
.ros-orb.three {{
  width: 300px; height: 300px; right: 18%; bottom: -180px;
  background: radial-gradient(circle at 35% 35%, rgba(255,237,0,.20), rgba(227,5,19,.03));
  animation-delay: -8s;
}}
.ros-grid {{
  position: absolute;
  inset: 0;
  opacity: .20;
  background-image:
    linear-gradient(rgba(4,57,98,.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(4,57,98,.055) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: linear-gradient(to bottom, rgba(0,0,0,.9), transparent 84%);
}}

/* Premium page hero */
.ros-page-hero {{
  position: relative;
  overflow: hidden;
  border-radius: var(--ros-radius-xl);
  padding: clamp(26px, 4vw, 54px);
  margin: 0 0 1.8rem;
  color: white;
  background:
    linear-gradient(120deg, rgba(4,57,98,.98), rgba(0,112,192,.94) 56%, rgba(0,139,210,.88)),
    radial-gradient(circle at 90% 15%, rgba(126,203,238,.6), transparent 35%);
  box-shadow: 0 32px 80px rgba(4,57,98,.26);
  isolation: isolate;
  animation: ros-rise .65s cubic-bezier(.2,.8,.2,1) both;
}}
.ros-page-hero::before {{
  content: "";
  position: absolute;
  width: 420px;
  height: 420px;
  right: -140px;
  top: -240px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,.20);
  box-shadow: 0 0 0 42px rgba(255,255,255,.045), 0 0 0 84px rgba(255,255,255,.025);
  animation: ros-orbit 18s linear infinite;
  z-index: -1;
}}
.ros-page-hero::after {{
  content: "";
  position: absolute;
  left: 0; right: 0; bottom: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--alten-red), var(--alten-yellow), var(--alten-light-blue), transparent 86%);
}}
.ros-eyebrow {{
  display: inline-flex;
  align-items: center;
  gap: .55rem;
  padding: .45rem .8rem;
  border-radius: 999px;
  background: rgba(255,255,255,.12);
  border: 1px solid rgba(255,255,255,.18);
  font-size: .78rem;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  backdrop-filter: blur(10px);
}}
.ros-page-hero h1 {{
  color: white !important;
  font-size: clamp(2.15rem, 5vw, 4.35rem) !important;
  line-height: .98 !important;
  letter-spacing: -.055em !important;
  margin: 1rem 0 .8rem !important;
  max-width: 980px;
}}
.ros-page-hero p {{
  color: rgba(255,255,255,.84) !important;
  font-size: clamp(1rem, 1.7vw, 1.2rem);
  max-width: 760px;
  margin: 0;
}}

/* Cards and metrics */
.ros-card, [data-testid="stMetric"] {{
  background: var(--ros-panel);
  border: 1px solid rgba(4,57,98,.10);
  box-shadow: var(--ros-shadow);
  border-radius: var(--ros-radius-lg);
  backdrop-filter: blur(18px);
  transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
}}
.ros-card {{ padding: 1.25rem; }}
.ros-card:hover, [data-testid="stMetric"]:hover {{
  transform: translateY(-4px);
  box-shadow: var(--ros-shadow-hover);
  border-color: rgba(0,139,210,.32);
}}
[data-testid="stMetric"] {{
  padding: 1.25rem 1.35rem;
  overflow: hidden;
  position: relative;
}}
[data-testid="stMetric"]::after {{
  content: "";
  position: absolute;
  left: 0; top: 0; bottom: 0; width: 4px;
  background: linear-gradient(var(--alten-blue), var(--alten-light-blue));
}}
[data-testid="stMetricValue"] {{ color: var(--alten-navy); font-weight: 800; }}
[data-testid="stMetricLabel"] {{ color: var(--alten-dark-grey); font-weight: 650; }}

/* Streamlit controls */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stDateInput input, [data-baseweb="select"] > div {{
  border-radius: var(--ros-radius-md) !important;
  border: 1px solid rgba(4,57,98,.18) !important;
  background: rgba(255,255,255,.92) !important;
  min-height: 48px;
  box-shadow: 0 8px 20px rgba(4,57,98,.05);
  transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease;
}}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {{
  border-color: var(--alten-blue) !important;
  box-shadow: 0 0 0 4px rgba(0,139,210,.14) !important;
}}
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
  border-radius: 14px !important;
  min-height: 48px;
  font-weight: 750 !important;
  letter-spacing: .01em;
  border: 1px solid rgba(4,57,98,.12) !important;
  transition: transform .18s ease, box-shadow .18s ease, filter .18s ease !important;
}}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
  border: 0 !important;
  color: white !important;
  background: linear-gradient(110deg, var(--alten-navy), var(--alten-blue-mid) 55%, var(--alten-blue)) !important;
  box-shadow: 0 14px 30px rgba(0,112,192,.28) !important;
  position: relative;
  overflow: hidden;
}}
.stButton > button[kind="primary"]::after,
.stFormSubmitButton > button[kind="primary"]::after {{
  content: "";
  position: absolute;
  inset: -2px auto -2px -42%;
  width: 34%;
  background: linear-gradient(100deg, transparent, rgba(255,255,255,.42), transparent);
  transform: skewX(-18deg);
  animation: ros-shimmer 3.8s ease-in-out infinite;
}}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {{
  transform: translateY(-2px);
  box-shadow: 0 18px 38px rgba(4,57,98,.22) !important;
  filter: saturate(1.08);
}}
.stButton > button:active, .stFormSubmitButton > button:active {{ transform: translateY(0) scale(.99); }}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {{
  border: 1.5px dashed rgba(0,139,210,.48) !important;
  background: linear-gradient(145deg, rgba(255,255,255,.94), rgba(213,230,253,.48)) !important;
  border-radius: var(--ros-radius-lg) !important;
  padding: 1.2rem !important;
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
  transform: translateY(-3px);
  border-color: var(--alten-blue) !important;
  box-shadow: 0 20px 44px rgba(0,139,210,.14);
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
  gap: .45rem;
  padding: .35rem;
  border-radius: 16px;
  background: rgba(4,57,98,.055);
}}
.stTabs [data-baseweb="tab"] {{
  border-radius: 12px;
  padding: .65rem 1rem;
  font-weight: 700;
}}
.stTabs [aria-selected="true"] {{
  background: white !important;
  color: var(--alten-navy) !important;
  box-shadow: 0 8px 22px rgba(4,57,98,.10);
}}

/* Dataframes and alerts */
[data-testid="stDataFrame"] {{
  border-radius: var(--ros-radius-lg);
  overflow: hidden;
  border: 1px solid rgba(4,57,98,.10);
  box-shadow: 0 18px 40px rgba(4,57,98,.08);
}}
[data-testid="stAlert"] {{ border-radius: 16px; border-width: 1px; }}
[data-testid="stExpander"] {{
  border-radius: 16px !important;
  border: 1px solid rgba(4,57,98,.10) !important;
  background: rgba(255,255,255,.72);
}}

/* Sidebar */
[data-testid="stSidebar"] {{
  background:
    radial-gradient(circle at 20% 2%, rgba(126,203,238,.16), transparent 30%),
    linear-gradient(180deg, #031f36 0%, var(--alten-navy) 54%, #07304f 100%);
  border-right: 1px solid rgba(255,255,255,.08);
}}
[data-testid="stSidebar"] * {{ color: rgba(255,255,255,.92); }}
[data-testid="stSidebar"] [data-testid="stRadio"] label {{
  border-radius: 12px;
  padding: .45rem .55rem;
}}
[data-testid="stSidebar"] .stButton > button {{
  background: rgba(255,255,255,.08) !important;
  border-color: rgba(255,255,255,.15) !important;
  color: white !important;
}}
.ros-sidebar-brand {{
  padding: .8rem .35rem 1.1rem;
  animation: ros-rise .55s ease both;
}}
.ros-sidebar-brand img {{
  width: 94px;
  max-height: 74px;
  object-fit: contain;
  object-position: left center;
  filter: drop-shadow(0 8px 18px rgba(0,0,0,.22));
}}
.ros-sidebar-product {{
  margin-top: .7rem;
  font-size: 1.45rem;
  font-weight: 850;
  letter-spacing: -.04em;
}}
.ros-sidebar-caption {{ color: rgba(255,255,255,.58); font-size: .78rem; }}

/* Login visual */
.ros-login-shell {{
  position: relative;
  min-height: 560px;
  overflow: hidden;
  border-radius: 32px;
  color: white;
  padding: clamp(30px, 5vw, 70px);
  background:
    linear-gradient(125deg, rgba(3,31,54,.98), rgba(4,57,98,.97) 48%, rgba(0,139,210,.88)),
    radial-gradient(circle at 80% 20%, rgba(126,203,238,.55), transparent 35%);
  box-shadow: 0 36px 100px rgba(4,57,98,.34);
  isolation: isolate;
  animation: ros-rise .75s cubic-bezier(.18,.86,.25,1) both;
}}
.ros-login-shell::before {{
  content: "";
  position: absolute;
  inset: -60%;
  background: conic-gradient(from 180deg, transparent, rgba(126,203,238,.18), transparent 34%, rgba(255,237,0,.07), transparent 62%);
  animation: ros-spin 22s linear infinite;
  z-index: -2;
}}
.ros-login-shell::after {{
  content: "";
  position: absolute;
  inset: 1px;
  border-radius: 31px;
  background: linear-gradient(120deg, rgba(3,31,54,.91), rgba(4,57,98,.88) 56%, rgba(0,112,192,.72));
  z-index: -1;
}}
.ros-login-logo img {{
  width: 132px;
  max-height: 112px;
  object-fit: contain;
  object-position: left center;
  filter: drop-shadow(0 15px 28px rgba(0,0,0,.28));
}}
.ros-login-kicker {{
  margin-top: 2.1rem;
  color: var(--alten-light-blue);
  font-size: .78rem;
  font-weight: 800;
  letter-spacing: .16em;
  text-transform: uppercase;
}}
.ros-login-title {{
  margin: .55rem 0 .65rem;
  font-size: clamp(3.1rem, 7vw, 6.8rem);
  line-height: .9;
  letter-spacing: -.075em;
  font-weight: 900;
}}
.ros-login-title span {{
  background: linear-gradient(90deg, white, var(--alten-light-blue));
  -webkit-background-clip: text;
  color: transparent;
}}
.ros-login-copy {{
  max-width: 620px;
  font-size: 1.05rem;
  color: rgba(255,255,255,.70);
}}
.ros-signal {{
  display: flex;
  gap: .55rem;
  margin-top: 2rem;
}}
.ros-signal i {{
  width: 42px;
  height: 4px;
  border-radius: 99px;
  background: rgba(255,255,255,.18);
  animation: ros-signal 2.4s ease-in-out infinite;
}}
.ros-signal i:nth-child(1) {{ background: var(--alten-red); }}
.ros-signal i:nth-child(2) {{ background: var(--alten-yellow); animation-delay: .14s; }}
.ros-signal i:nth-child(3) {{ background: var(--alten-light-blue); animation-delay: .28s; }}
.ros-signal i:nth-child(4) {{ animation-delay: .42s; }}
.ros-login-form-note {{
  display: flex;
  align-items: center;
  gap: .6rem;
  margin: .4rem 0 1rem;
  color: var(--alten-dark-grey);
  font-size: .88rem;
}}
.ros-login-form-note::before {{
  content: "";
  width: 8px; height: 8px; border-radius: 99px;
  background: #22c55e;
  box-shadow: 0 0 0 5px rgba(34,197,94,.13);
  animation: ros-pulse 2s ease-in-out infinite;
}}

/* Feature grid */
.ros-feature-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin: 1.2rem 0 1.8rem;
}}
.ros-feature {{
  position: relative;
  overflow: hidden;
  padding: 1.25rem;
  min-height: 150px;
  border-radius: 20px;
  background: rgba(255,255,255,.78);
  border: 1px solid rgba(4,57,98,.10);
  box-shadow: 0 18px 44px rgba(4,57,98,.09);
  backdrop-filter: blur(16px);
  transition: transform .25s ease, box-shadow .25s ease;
  animation: ros-rise .6s ease both;
}}
.ros-feature:nth-child(2) {{ animation-delay: .08s; }}
.ros-feature:nth-child(3) {{ animation-delay: .16s; }}
.ros-feature:hover {{ transform: translateY(-6px); box-shadow: var(--ros-shadow-hover); }}
.ros-feature strong {{ display:block; color: var(--alten-navy); font-size: 1.05rem; margin-bottom: .5rem; }}
.ros-feature p {{ margin:0; color: #526578; font-size: .9rem; line-height:1.55; }}
.ros-feature .num {{
  position: absolute; right: 1rem; top: .7rem;
  font-size: 2.6rem; font-weight: 900; color: rgba(0,139,210,.10);
}}

/* Animation definitions */
@keyframes ros-float {{
  0%,100% {{ transform: translate3d(0,0,0) scale(1); }}
  50% {{ transform: translate3d(30px,-24px,0) scale(1.06); }}
}}
@keyframes ros-spin {{ to {{ transform: rotate(360deg); }} }}
@keyframes ros-shimmer {{
  0%, 62% {{ left: -42%; opacity: 0; }}
  70% {{ opacity: 1; }}
  92%, 100% {{ left: 118%; opacity: 0; }}
}}
@keyframes ros-orbit {{ to {{ transform: rotate(360deg); }} }}
@keyframes ros-rise {{
  from {{ opacity: 0; transform: translateY(22px) scale(.985); }}
  to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
@keyframes ros-pulse {{
  0%,100% {{ box-shadow: 0 0 0 5px rgba(34,197,94,.12); }}
  50% {{ box-shadow: 0 0 0 9px rgba(34,197,94,.03); }}
}}
@keyframes ros-signal {{
  0%,100% {{ transform: scaleX(.65); opacity:.42; }}
  50% {{ transform: scaleX(1); opacity:1; }}
}}

@media (max-width: 900px) {{
  .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
  .ros-feature-grid {{ grid-template-columns: 1fr; }}
  .ros-login-shell {{ min-height: 430px; }}
}}

@media (max-width: 760px) {{
  .ros-page-hero {{ border-radius: 22px; padding: 24px 20px; }}
  .ros-login-shell {{ border-radius: 24px; padding: 30px 24px; min-height: 390px; }}
  .ros-login-title {{ font-size: clamp(3rem, 18vw, 5rem); }}
  .ros-login-copy {{ font-size: .98rem; }}
  .ros-signal i {{ width: 30px; }}
}}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration: .001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: .001ms !important;
  }}
}}
</style>
"""


def apply_alten_theme() -> None:
    """Inject the global theme into the current Streamlit page."""
    import streamlit as st

    st.markdown(build_theme_css(), unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ros-ambient" aria-hidden="true">
          <div class="ros-grid"></div>
          <div class="ros-orb one"></div>
          <div class="ros-orb two"></div>
          <div class="ros-orb three"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
