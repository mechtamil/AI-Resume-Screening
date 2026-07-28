"""Tenant-scoped RecruitOS configuration management page."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from models.security_context import SecurityContext
from services.authorization_service import (
    PERMISSION_CONFIGURATION_MANAGE_GLOBAL,
    PERMISSION_CONFIGURATION_MANAGE_TENANT,
    AuthorizationService,
)
from services.tenant_configuration_service import TenantConfigurationService
from services.user_management_service import UserManagementService
from ui.brand_components import page_header_html


def show_configuration_management(context: SecurityContext) -> None:
    context.require_valid()
    service = TenantConfigurationService()
    can_manage = (
        AuthorizationService.has_permission(
            context,
            PERMISSION_CONFIGURATION_MANAGE_GLOBAL,
        )
        or AuthorizationService.has_permission(
            context,
            PERMISSION_CONFIGURATION_MANAGE_TENANT,
        )
    )

    st.markdown(
        page_header_html(
            title="Configuration intelligence",
            eyebrow="Versioned and tenant-isolated",
            description=(
                "RecruitOS resolves one immutable workbook for every screening. "
                "Skills, education, certifications, scoring and recommendations "
                "remain isolated from other user workspaces."
            ),
        ),
        unsafe_allow_html=True,
    )

    target_user_id, target_label = _target_user(context, can_manage)
    st.caption(f"Configuration target: {target_label}")

    try:
        health = service.configuration_health(context, target_user_id)
    except Exception as exc:
        st.error(f"Configuration could not be resolved: {exc}")
        return

    selection = health["selection"]
    validation = health["validation"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Active source",
        "Tenant version" if selection["source"] == "tenant_version" else "System default",
    )
    col2.metric(
        "Version",
        selection.get("version_number") or "Default",
    )
    col3.metric(
        "Validation",
        "Ready" if validation["valid"] else "Blocked",
    )
    col4.metric(
        "Workbook fingerprint",
        str(selection.get("sha256") or "")[:12] or "Unavailable",
    )

    warnings = list(validation.get("warnings") or [])
    if warnings:
        with st.expander(f"Configuration warnings ({len(warnings)})"):
            for warning in warnings:
                st.warning(warning)

    if validation.get("errors"):
        for error in validation["errors"]:
            st.error(error)

    sheets = validation.get("sheets") or selection.get("sheet_summary") or {}
    if sheets:
        st.subheader("Workbook coverage")
        rows = [
            {
                "Sheet": name,
                "Rows": details.get("Rows", 0),
                "Columns": details.get("Columns", 0),
            }
            for name, details in sheets.items()
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    active_name, active_bytes = service.download_version(
        context,
        target_user_id=target_user_id,
    )
    st.download_button(
        "Download active configuration",
        data=active_bytes,
        file_name=active_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    versions = service.list_versions(context, target_user_id)
    st.subheader("Configuration history")
    if versions:
        history = pd.DataFrame(
            [
                {
                    "Version": item["version_number"],
                    "Status": item["status"],
                    "Source": item["source_name"],
                    "SHA-256": str(item["file_sha256"])[:16],
                    "Created": item["created_at"],
                    "Activated": item["activated_at"],
                }
                for item in versions
            ]
        )
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.info("This workspace currently inherits the validated system default.")

    if not can_manage:
        st.info(
            "Your active configuration is read-only. Contact an authorized "
            "RecruitOS administrator to upload or activate a new version."
        )
        return

    st.subheader("Publish a new immutable version")
    uploaded = st.file_uploader(
        "Upload RecruitOS configuration workbook",
        type=["xlsx"],
        key=f"tenant_configuration_{target_user_id}",
        help=(
            "The workbook is fully validated before storage. Existing versions "
            "are never modified in place."
        ),
    )
    activate_now = st.checkbox("Activate immediately after validation", value=True)
    if st.button(
        "Validate and publish configuration",
        disabled=uploaded is None,
        type="primary",
        use_container_width=True,
    ):
        try:
            created = service.upload_version(
                context,
                target_user_id=target_user_id,
                file_name=uploaded.name,
                content=uploaded.getvalue(),
                activate=activate_now,
            )
            st.success(
                f"Configuration version {created['version_number']} was "
                f"{'activated' if activate_now else 'published as draft'}."
            )
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    if versions:
        version_labels = {
            f"Version {item['version_number']} · {item['status']} · {item['source_name']}": int(item["id"])
            for item in versions
        }
        selected_label = st.selectbox(
            "Select an existing version",
            list(version_labels),
        )
        selected_id = version_labels[selected_label]
        action_col1, action_col2 = st.columns(2)
        if action_col1.button("Activate selected version", use_container_width=True):
            try:
                service.activate_version(
                    context,
                    target_user_id=target_user_id,
                    version_id=selected_id,
                )
                st.success("Selected configuration version activated.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        selected_name, selected_bytes = service.download_version(
            context,
            target_user_id=target_user_id,
            version_id=selected_id,
        )
        action_col2.download_button(
            "Download selected version",
            data=selected_bytes,
            file_name=selected_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if selection["source"] == "tenant_version":
        st.markdown("---")
        if st.button("Revert workspace to system default", use_container_width=True):
            try:
                service.use_system_default(
                    context,
                    target_user_id=target_user_id,
                )
                st.success("Workspace reverted to the validated system default.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _target_user(context: SecurityContext, can_manage: bool) -> tuple[int, str]:
    if not can_manage:
        return context.user_id, f"{context.login_id} · {context.display_name}"

    users = UserManagementService.list_users(context)
    options: dict[str, int] = {}
    for user in users:
        label = (
            f"{user['employee_user_id']} · {user['display_name']} · "
            f"{user['role_code']} · {user['country_location']}"
        )
        options[label] = int(user["id"])

    current_label = next(
        (label for label, value in options.items() if value == context.user_id),
        None,
    )
    labels = list(options)
    index = labels.index(current_label) if current_label in labels else 0
    selected = st.selectbox("Workspace user", labels, index=index)
    return options[selected], selected
