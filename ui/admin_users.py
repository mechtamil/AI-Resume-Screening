"""Role-gated RecruitOS user administration interface."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from models.security_context import SecurityContext
from services.authorization_service import (
    ROLE_LABELS,
    AuthorizationService,
)
from services.password_service import PasswordService
from services.user_management_service import UserManagementService
from ui.brand_components import page_header_html


def show_user_administration(context: SecurityContext) -> None:
    context.require_valid()
    st.markdown(
        page_header_html(
            title="User administration",
            eyebrow="Identity & access",
            description=(
                "Provision employees, assign role-based access, manage temporary "
                "credentials and monitor reset requests."
            ),
        ),
        unsafe_allow_html=True,
    )

    users_tab, add_tab, import_tab, credential_tab, request_tab = st.tabs(
        [
            "Users",
            "Add User",
            "Import Excel",
            "Credentials & Access",
            "Forgot Password Requests",
        ]
    )

    with users_tab:
        _show_users(context)
    with add_tab:
        _show_add_user(context)
    with import_tab:
        _show_import(context)
    with credential_tab:
        _show_credentials(context)
    with request_tab:
        _show_reset_requests(context)


def _show_users(context: SecurityContext) -> None:
    try:
        users = UserManagementService.list_users(context)
    except Exception as exc:
        st.error(f"User list could not be loaded: {exc}")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Visible users", len(users))
    col2.metric(
        "Active",
        sum(1 for item in users if item.get("account_status") == "ACTIVE"),
    )
    col3.metric(
        "First login pending",
        sum(1 for item in users if item.get("must_change_password")),
    )

    if users:
        dataframe = pd.DataFrame(
            [
                {
                    "Database ID": item["id"],
                    "User ID": item["employee_user_id"],
                    "Full Name": item["display_name"],
                    "Email": item["email"],
                    "Role": ROLE_LABELS.get(item["role_code"], item["role_code"]),
                    "Country or Location": item["country_location"],
                    "Status": item["account_status"],
                    "Reset Required": "Yes" if item["must_change_password"] else "No",
                    "Temporary Expiry": item["temporary_password_expires_at"],
                    "Last Login": item["last_login_at"],
                }
                for item in users
            ]
        )
        st.dataframe(dataframe, use_container_width=True, hide_index=True)
    else:
        st.info("No users are available in your administration scope.")

    try:
        master = UserManagementService.export_user_access_master(context)
        st.download_button(
            "Download User Access Master",
            data=master,
            file_name="RecruitOS_User_Access_Master.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )
        st.caption(
            "The master contains identity, role and account-status information. "
            "Passwords are never retrievable from RecruitOS."
        )
    except Exception as exc:
        st.warning(f"User Access Master is unavailable: {exc}")


def _show_add_user(context: SecurityContext) -> None:
    roles = AuthorizationService.assignable_roles(context)
    if not roles:
        st.warning("Your role cannot provision users.")
        return

    with st.form("add_single_user", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            user_id = st.text_input("User ID", placeholder="Example: 6276")
            full_name = st.text_input("Full Name")
            email = st.text_input("Corporate Email")
            role = st.selectbox(
                "Role",
                roles,
                format_func=lambda value: ROLE_LABELS.get(value, value),
            )
            country_location = st.text_input(
                "Country or Location",
                value=context.country_location if context.role == "TENANT_ADMIN" else "",
                disabled=context.role == "TENANT_ADMIN",
            )
            account_status = st.selectbox(
                "Initial Account Status",
                ["RESET_REQUIRED", "DISABLED"],
                help=(
                    "RESET_REQUIRED allows temporary sign-in and forces password change. "
                    "DISABLED creates the identity without allowing sign-in."
                ),
            )
        with col2:
            time_zone = st.text_input("Time Zone (Optional)")
            department = st.text_input("Department (Optional)")
            business_unit = st.text_input("Business Unit (Optional)")
            manager_user_id = st.text_input("Manager User ID (Optional)")
            password_mode = st.radio(
                "Temporary Password",
                ["Generate unique password", "Enter temporary password"],
                horizontal=True,
            )
            temporary_password = st.text_input(
                "Temporary Password",
                type="password",
                disabled=password_mode == "Generate unique password",
                help="This value is hashed immediately and shown only in the creation result.",
            )
        submitted = st.form_submit_button(
            "Create User",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            created = UserManagementService.create_user(
                context,
                employee_user_id=user_id,
                full_name=full_name,
                email=email,
                role=role,
                country_location=(context.country_location if context.role == "TENANT_ADMIN" else country_location),
                temporary_password=temporary_password,
                generate_password=password_mode == "Generate unique password",
                account_status=account_status,
                time_zone=time_zone,
                department=department,
                business_unit=business_unit,
                manager_user_id=manager_user_id,
            )
            credential = UserManagementService._credential_record(created)
            st.session_state["last_credentials"] = [credential]
            st.success("The user was created with mandatory first-login password reset.")
            _show_one_time_credentials([credential])
        except (ValueError, PermissionError, LookupError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("RecruitOS could not create the user.")


def _show_import(context: SecurityContext) -> None:
    template = UserManagementService.build_import_template()
    st.download_button(
        "Download User Import Template",
        data=template,
        file_name="RecruitOS_User_Import_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.caption(
        "Temporary Password is optional. A unique temporary password is generated "
        "when the column is blank. Time Zone is optional."
    )

    upload = st.file_uploader(
        "Upload completed user-import workbook",
        type=["xlsx"],
        key="admin_user_import",
    )
    if upload is not None and st.button("Validate Import", use_container_width=True):
        try:
            preview = UserManagementService.preview_import(context, upload.getvalue())
            st.session_state["user_import_preview"] = preview
            st.session_state["user_import_filename"] = upload.name
        except (ValueError, PermissionError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("The user-import workbook could not be validated.")

    preview = st.session_state.get("user_import_preview")
    if not preview:
        return

    summary = preview["summary"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", summary["total"])
    col2.metric("Valid", summary["valid"])
    col3.metric("Invalid", summary["invalid"])
    display = pd.DataFrame(
        [
            {
                "Row": row["row_number"],
                "User ID": row["user_id"],
                "Full Name": row["full_name"],
                "Role": row["role"],
                "Country or Location": row["country_location"],
                "Valid": "Yes" if row["valid"] else "No",
                "Errors": " | ".join(row["errors"]),
            }
            for row in preview["rows"]
        ]
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

    confirm = st.checkbox(
        "I reviewed the validation results and want to create all valid users.",
        key="confirm_user_import",
    )
    if st.button(
        "Import Valid Users",
        type="primary",
        disabled=not confirm or summary["valid"] == 0,
        use_container_width=True,
    ):
        try:
            result = UserManagementService.commit_import(
                context,
                preview,
                filename=str(st.session_state.get("user_import_filename") or "users.xlsx"),
            )
            st.success(f"Created {result['created']} users; {result['failed']} rows failed.")
            st.session_state["last_credentials"] = result["credentials"]
            _show_one_time_credentials(result["credentials"])
            st.session_state.pop("user_import_preview", None)
            st.session_state.pop("confirm_user_import", None)
        except Exception as exc:
            st.error(f"User import could not be completed: {exc}")


def _show_credentials(context: SecurityContext) -> None:
    try:
        users = UserManagementService.list_users(context)
    except Exception as exc:
        st.error(str(exc))
        return
    manageable = [item for item in users if item["role_code"] != "SYSTEM_OWNER"]
    if not manageable:
        st.info("No manageable user is available in your scope.")
        return

    options = {
        f"{item['employee_user_id']} — {item['display_name']} — {ROLE_LABELS.get(item['role_code'], item['role_code'])}": item
        for item in manageable
    }
    selected = options[st.selectbox("Select User", list(options))]

    action = st.radio(
        "Administrative Action",
        ["Reset Temporary Credential", "Change Role", "Change Account Status"],
        horizontal=True,
    )

    if action == "Reset Temporary Credential":
        mode = st.radio(
            "Temporary Password Method",
            ["Generate unique password", "Enter temporary password"],
            horizontal=True,
            key="reset_password_mode",
        )
        value = st.text_input(
            "Temporary Password",
            type="password",
            disabled=mode == "Generate unique password",
            key="admin_reset_password",
        )
        if st.button("Reset Credential", type="primary", use_container_width=True):
            try:
                credential = UserManagementService.reset_temporary_password(
                    context,
                    target_database_user_id=int(selected["id"]),
                    temporary_password=value,
                    generate_password=mode == "Generate unique password",
                )
                st.session_state["last_credentials"] = [credential]
                st.success("Temporary credential reset. Existing sessions were revoked.")
                _show_one_time_credentials([credential])
            except (ValueError, PermissionError, LookupError) as exc:
                st.error(str(exc))

    elif action == "Change Role":
        roles = AuthorizationService.assignable_roles(context)
        new_role = st.selectbox(
            "New Role",
            roles,
            format_func=lambda value: ROLE_LABELS.get(value, value),
        )
        if st.button("Update Role", type="primary", use_container_width=True):
            try:
                UserManagementService.change_role(
                    context,
                    target_database_user_id=int(selected["id"]),
                    new_role=new_role,
                )
                st.success("Role updated. Existing sessions were revoked.")
                st.rerun()
            except (ValueError, PermissionError, LookupError) as exc:
                st.error(str(exc))

    else:
        new_status = st.selectbox(
            "Account Status",
            ["ACTIVE", "DISABLED", "LOCKED", "EXPIRED"],
        )
        if st.button("Update Account Status", type="primary", use_container_width=True):
            try:
                UserManagementService.update_account_status(
                    context,
                    target_database_user_id=int(selected["id"]),
                    account_status=new_status,
                )
                st.success("Account status updated.")
                st.rerun()
            except (ValueError, PermissionError, LookupError) as exc:
                st.error(str(exc))


def _show_reset_requests(context: SecurityContext) -> None:
    try:
        requests = UserManagementService.pending_reset_requests(context)
    except Exception as exc:
        st.error(str(exc))
        return
    if not requests:
        st.info("No pending forgot-password request is available in your scope.")
        return
    st.dataframe(pd.DataFrame(requests), use_container_width=True, hide_index=True)
    st.caption(
        "Resolve a request by opening Credentials & Access and issuing a new "
        "temporary password for the selected user."
    )


def _show_one_time_credentials(credentials: list[dict]) -> None:
    if not credentials:
        return
    st.warning(
        "Download or distribute these temporary credentials now. RecruitOS stores "
        "only password hashes and cannot display the passwords again."
    )
    st.dataframe(pd.DataFrame(credentials), use_container_width=True, hide_index=True)
    st.download_button(
        "Download One-Time Temporary Credentials",
        data=UserManagementService.export_temporary_credentials(credentials),
        file_name="RecruitOS_Temporary_Credentials.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
