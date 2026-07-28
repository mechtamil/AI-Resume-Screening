"""Premium Streamlit authentication and password-lifecycle interface."""
from __future__ import annotations

import streamlit as st

from config.settings import (
    DEPLOYMENT_ENVIRONMENT,
    INITIAL_OWNER_SETUP_ENABLED,
    INITIAL_SETUP_KEY,
)
from models.security_context import SecurityContext
from services.auth_service import AuthService
from ui.brand_components import login_visual_html, page_header_html

AUTH_TOKEN_KEY = "auth_token"
AUTH_CONTEXT_KEY = "security_context"
LOGIN_FIELD_LABELS = ("User ID", "Password")
FORBIDDEN_LOGIN_FIELDS = ("Organization", "Country", "Location", "Region")


def get_authenticated_context() -> SecurityContext | None:
    """Resolve the browser token through the server-side session table."""
    token = str(st.session_state.get(AUTH_TOKEN_KEY) or "")
    if not token:
        st.session_state.pop(AUTH_CONTEXT_KEY, None)
        return None

    context = AuthService.resolve_session(token)
    if context is None:
        clear_authentication_state()
        return None

    st.session_state[AUTH_CONTEXT_KEY] = context
    return context


def show_authentication() -> None:
    """Render initial owner setup or the final User ID/password login."""
    if AuthService.owner_setup_required():
        _show_initial_owner_setup()
        return

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.markdown(login_visual_html(), unsafe_allow_html=True)

    with right:
        st.markdown(
            page_header_html(
                title="Welcome back",
                eyebrow="Secure access",
                description="Sign in to your private RecruitOS workspace.",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="ros-login-form-note">Identity verified through server-side sessions</div>',
            unsafe_allow_html=True,
        )

        with st.form("recruitos_login_form", clear_on_submit=False):
            user_id = st.text_input(
                "User ID",
                key="login_user_id",
                placeholder="Enter employee ID",
                autocomplete="username",
            )
            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
                placeholder="Enter password",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button(
                "Sign In",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            try:
                context, raw_token = AuthService.authenticate(
                    user_id=user_id,
                    password=password,
                )
                st.session_state[AUTH_TOKEN_KEY] = raw_token
                st.session_state[AUTH_CONTEXT_KEY] = context
                st.session_state["page"] = "Home"
                st.session_state.pop("login_password", None)
                st.rerun()
            except (ValueError, PermissionError) as exc:
                st.error(str(exc))
                st.session_state.pop("login_password", None)
            except Exception:
                st.error("RecruitOS could not complete the sign-in request.")

        if st.button(
            "Forgot Password?",
            key="forgot_password_toggle",
            use_container_width=True,
        ):
            st.session_state["show_forgot_password"] = not bool(
                st.session_state.get("show_forgot_password")
            )

        if st.session_state.get("show_forgot_password"):
            with st.form("forgot_password_form", clear_on_submit=True):
                requested_user_id = st.text_input(
                    "User ID",
                    key="forgot_user_id",
                    placeholder="Enter employee ID",
                )
                request_submitted = st.form_submit_button(
                    "Request Password Reset",
                    use_container_width=True,
                )
            if request_submitted:
                st.info(AuthService.request_password_reset(requested_user_id))

        st.caption("No public registration · Admin-provisioned access only")


def show_forced_password_change(context: SecurityContext) -> None:
    """Block all application pages until a temporary password is replaced."""
    context.require_valid()
    st.markdown(
        page_header_html(
            title="Create your new password",
            eyebrow="First sign-in security",
            description=(
                "Your temporary credential was accepted. Replace it now before "
                "opening RecruitOS."
            ),
        ),
        unsafe_allow_html=True,
    )
    st.info(
        "The new password must meet the configured permanent-password policy. "
        "Your temporary password becomes invalid immediately after this change."
    )
    with st.form("mandatory_password_change", clear_on_submit=False):
        current_password = st.text_input(
            "Temporary Password",
            type="password",
            autocomplete="current-password",
        )
        new_password = st.text_input(
            "New Password",
            type="password",
            autocomplete="new-password",
        )
        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            autocomplete="new-password",
        )
        submitted = st.form_submit_button(
            "Activate My RecruitOS Account",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if new_password != confirm_password:
            st.error("The new passwords do not match.")
            return
        try:
            refreshed, raw_token = AuthService.complete_password_change(
                raw_token=str(st.session_state.get(AUTH_TOKEN_KEY) or ""),
                current_password=current_password,
                new_password=new_password,
            )
            st.session_state[AUTH_TOKEN_KEY] = raw_token
            st.session_state[AUTH_CONTEXT_KEY] = refreshed
            st.success("Your RecruitOS account is active.")
            st.rerun()
        except (ValueError, PermissionError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("RecruitOS could not update the password.")


def show_authenticated_user(context: SecurityContext) -> None:
    """Display the signed-in employee and logout action in the sidebar."""
    st.sidebar.markdown(f"**{context.display_name}**")
    st.sidebar.caption(f"{context.login_id} · {context.role.replace('_', ' ').title()}")
    if context.country_location:
        st.sidebar.caption(context.country_location)
    if st.sidebar.button("Sign Out", use_container_width=True):
        raw_token = str(st.session_state.get(AUTH_TOKEN_KEY) or "")
        try:
            AuthService.logout(raw_token)
        finally:
            clear_authentication_state()
        st.rerun()


def clear_authentication_state() -> None:
    """Remove identity and user-specific UI state from this browser session."""
    for key in (
        AUTH_TOKEN_KEY,
        AUTH_CONTEXT_KEY,
        "analysis_result",
        "page",
        "jd_upload",
        "skill_upload",
        "resume_uploads",
        "last_credentials",
        "user_import_preview",
        "show_forgot_password",
    ):
        st.session_state.pop(key, None)


def _show_initial_owner_setup() -> None:
    st.markdown(
        page_header_html(
            title="Launch RecruitOS",
            eyebrow="One-time secure setup",
            description=(
                "Create the first System Owner. Public account creation is disabled "
                "after this step."
            ),
        ),
        unsafe_allow_html=True,
    )
    if not INITIAL_OWNER_SETUP_ENABLED:
        st.error(
            "Initial System Owner setup is securely disabled. Configure the "
            "deployment setup key before creating the first account."
        )
        st.code(
            "RECRUITOS_ENVIRONMENT=production\n"
            "RECRUITOS_INITIAL_SETUP_KEY=<long-random-secret>",
            language="text",
        )
        st.caption(f"Deployment environment: {DEPLOYMENT_ENVIRONMENT}")
        return

    if not INITIAL_SETUP_KEY:
        st.warning(
            "Insecure local bootstrap is enabled for this isolated development "
            "environment. Never enable it on a shared or public deployment."
        )

    with st.form("initial_owner_setup", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            user_id = st.text_input("System Owner User ID", placeholder="Employee ID")
            full_name = st.text_input("Full Name")
            email = st.text_input("Corporate Email")
        with col2:
            country_location = st.text_input(
                "Country or Location",
                help="Administrative profile only; it will not appear on the login page.",
            )
            password = st.text_input("New Owner Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            setup_key = (
                st.text_input("Deployment Setup Key", type="password")
                if INITIAL_SETUP_KEY
                else ""
            )
        submitted = st.form_submit_button(
            "Create System Owner",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if password != confirm_password:
            st.error("The passwords do not match.")
            return
        try:
            AuthService.bootstrap_system_owner(
                user_id=user_id,
                full_name=full_name,
                email=email,
                country_location=country_location,
                password=password,
                setup_key=setup_key,
            )
            st.success("System Owner created. Sign in with the new User ID.")
            st.rerun()
        except (ValueError, PermissionError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("RecruitOS could not complete the initial setup.")
