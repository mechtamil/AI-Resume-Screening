"""Guided page navigation helpers for RecruitOS Streamlit workflows."""
from __future__ import annotations

from collections.abc import Iterable

WORKFLOW_PAGES = (
    "Home",
    "Resume Screening",
    "Results",
    "Candidate Database",
)


def queue_page(page: str) -> None:
    """Request a page change on the next Streamlit rerun."""
    import streamlit as st

    st.session_state["requested_page"] = str(page)
    st.rerun()


def apply_queued_page(allowed_pages: Iterable[str]) -> str | None:
    """Apply a queued page only when it remains authorized."""
    import streamlit as st

    requested = str(st.session_state.pop("requested_page", "") or "")
    if requested and requested in set(allowed_pages):
        st.session_state["page"] = requested
        return requested
    return None


def workflow_neighbors(
    current_page: str,
    allowed_pages: Iterable[str],
    *,
    has_results: bool,
) -> tuple[str | None, str | None]:
    """Return authorized previous/next operational pages."""
    allowed = [page for page in WORKFLOW_PAGES if page in set(allowed_pages)]
    if current_page not in allowed:
        return None, "Home" if "Home" in allowed else None

    index = allowed.index(current_page)
    previous_page = allowed[index - 1] if index > 0 else None
    next_page = allowed[index + 1] if index < len(allowed) - 1 else None
    if next_page == "Results" and not has_results:
        next_page = None
    if current_page == "Results" and not has_results:
        next_page = None
    return previous_page, next_page


def render_workflow_navigation(
    current_page: str,
    allowed_pages: Iterable[str],
    *,
    has_results: bool,
) -> None:
    """Render a consistent previous/next action bar."""
    import streamlit as st

    previous_page, next_page = workflow_neighbors(
        current_page,
        allowed_pages,
        has_results=has_results,
    )
    if not previous_page and not next_page:
        return

    st.markdown('<div class="ros-flow-divider"></div>', unsafe_allow_html=True)
    left, center, right = st.columns([1, 2, 1])
    with left:
        if previous_page and st.button(
            f"← {previous_page}",
            key=f"workflow_previous_{current_page}",
            use_container_width=True,
        ):
            queue_page(previous_page)
    with center:
        st.caption("Guided RecruitOS workflow")
    with right:
        if next_page and st.button(
            f"{next_page} →",
            key=f"workflow_next_{current_page}",
            type="primary",
            use_container_width=True,
        ):
            queue_page(next_page)
