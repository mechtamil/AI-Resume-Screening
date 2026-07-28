"""Reusable ALTEN-branded UI components for RecruitOS."""
from __future__ import annotations

import base64
import html
from pathlib import Path

from config.brand import (
    PRODUCT_NAME,
    PRODUCT_TAGLINE,
    preferred_logo_path,
    preferred_logo_url,
)


def logo_source(*, dark_background: bool) -> str:
    """Return a browser-ready approved logo source.

    A deployment-provided local asset takes priority. The official ALTEN media
    library URL is used as the public fallback.
    """
    local = preferred_logo_path(dark_background=dark_background)
    if local is None:
        return preferred_logo_url(dark_background=dark_background)
    return _path_to_data_uri(local)


def login_visual_html() -> str:
    """Return the animated premium visual used beside the login form."""
    logo = html.escape(logo_source(dark_background=True), quote=True)
    return f"""
    <section class="ros-login-shell ros-login-visual" aria-label="RecruitOS introduction">
      <div class="ros-login-logo">
        <img src="{logo}" alt="ALTEN" />
      </div>
      <div class="ros-login-kicker">AI-powered talent intelligence</div>
      <div class="ros-login-title"><span>{PRODUCT_NAME}</span></div>
      <p class="ros-login-copy">
        Transform complex candidate data into precise, explainable hiring
        decisions—securely, privately, and at global scale.
      </p>
      <div class="ros-signal" aria-hidden="true">
        <i></i><i></i><i></i><i></i>
      </div>
    </section>
    """


def page_header_html(
    *,
    title: str,
    description: str,
    eyebrow: str = "RecruitOS",
) -> str:
    """Build a branded animated page hero."""
    return f"""
    <section class="ros-page-hero">
      <div class="ros-eyebrow">{html.escape(eyebrow)}</div>
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(description)}</p>
    </section>
    """


def sidebar_brand_html() -> str:
    """Build the compact sidebar brand block."""
    logo = html.escape(logo_source(dark_background=True), quote=True)
    return f"""
    <div class="ros-sidebar-brand">
      <img src="{logo}" alt="ALTEN" />
      <div class="ros-sidebar-product">{PRODUCT_NAME}</div>
      <div class="ros-sidebar-caption">{html.escape(PRODUCT_TAGLINE)}</div>
    </div>
    """


def feature_grid_html() -> str:
    """Return the premium home-page capability grid."""
    return """
    <div class="ros-feature-grid">
      <article class="ros-feature">
        <span class="num">01</span>
        <strong>Intelligent extraction</strong>
        <p>Convert resumes and job descriptions into structured, auditable talent data.</p>
      </article>
      <article class="ros-feature">
        <span class="num">02</span>
        <strong>Explainable matching</strong>
        <p>Rank candidates through configurable skills, experience, education and keyword evidence.</p>
      </article>
      <article class="ros-feature">
        <span class="num">03</span>
        <strong>Private by design</strong>
        <p>Keep projects, candidates and results isolated to the authenticated user's workspace.</p>
      </article>
    </div>
    """


def sidebar_user_card_html(
    *,
    display_name: str,
    login_id: str,
    role: str,
    location: str = "",
) -> str:
    """Build a compact, non-duplicated signed-in user card."""
    normalized_location = str(location or "").strip()
    if normalized_location.casefold() == str(login_id or "").strip().casefold():
        normalized_location = ""
    location_html = (
        f'<div class="ros-user-location">{html.escape(normalized_location)}</div>'
        if normalized_location
        else ""
    )
    initials = "".join(
        part[:1].upper() for part in str(display_name or "User").split()[:2]
    ) or "U"
    return f"""
    <section class="ros-sidebar-user" aria-label="Signed-in user">
      <div class="ros-user-avatar">{html.escape(initials)}</div>
      <div class="ros-user-copy">
        <strong>{html.escape(display_name or 'User')}</strong>
        <span>{html.escape(login_id)} · {html.escape(role)}</span>
        {location_html}
      </div>
    </section>
    """


def workflow_stepper_html(*, active_step: int = 1) -> str:
    """Return a four-stage visual screening workflow indicator."""
    labels = ("Prepare", "Screen", "Review", "Export")
    items = []
    for index, label in enumerate(labels, start=1):
        state = "active" if index == active_step else "complete" if index < active_step else "pending"
        items.append(
            f'<div class="ros-step {state}"><span>{index:02d}</span><strong>{label}</strong></div>'
        )
    return '<div class="ros-stepper">' + ''.join(items) + '</div>'


def _path_to_data_uri(path: Path) -> str:
    suffix = path.suffix.casefold()
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
    }.get(suffix, "application/octet-stream")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"
