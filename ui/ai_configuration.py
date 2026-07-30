"""AI provider gateway, model registry, prompt registry, and tenant-policy UI."""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from models.security_context import SecurityContext
from services.ai_registry_service import AIRegistryService
from services.authorization_service import (
    PERMISSION_AI_POLICY_MANAGE_GLOBAL,
    PERMISSION_AI_POLICY_MANAGE_TENANT,
    AuthorizationService,
)
from services.user_management_service import UserManagementService

_DEFAULT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "minLength": 1},
    },
    "required": ["summary"],
    "additionalProperties": False,
}


def show_ai_configuration(context: SecurityContext) -> None:
    """Show AI registry metadata without exposing deployment credentials."""
    context.require_valid()
    service = AIRegistryService()
    can_manage_global = AuthorizationService.has_permission(
        context,
        PERMISSION_AI_POLICY_MANAGE_GLOBAL,
    )
    can_manage_scope = can_manage_global or AuthorizationService.has_permission(
        context,
        PERMISSION_AI_POLICY_MANAGE_TENANT,
    )

    st.subheader("AI provider gateway")
    st.caption(
        "AI remains disabled until an authorized administrator activates a task "
        "policy. Provider keys are read only from deployment secrets and are never "
        "stored in RecruitOS records or telemetry."
    )

    readiness = service.provider_readiness()
    ready_columns = st.columns(len(readiness))
    for column, item in zip(ready_columns, readiness):
        with column:
            st.metric(
                f"{item['provider_code']} · {item['deployment_type']}",
                "Configured" if item["configured"] else "Not configured",
            )
            st.caption(f"Endpoint: {item['endpoint']} · Credential: {item['credential']}")

    target_user_id, target_label = _target_user(context, can_manage_scope)
    st.caption(f"AI policy target: {target_label}")

    models = service.list_models(context)
    prompts = service.list_prompt_versions(context)
    policies = service.list_policies(context, target_user_id=target_user_id)
    telemetry = service.telemetry(context, target_user_id=target_user_id, limit=100)

    overview_tab, model_tab, prompt_tab, policy_tab, telemetry_tab = st.tabs(
        [
            "Overview",
            "Model registry",
            "Prompt registry",
            "Tenant policy",
            "Telemetry",
        ]
    )

    with overview_tab:
        _show_overview(models, prompts, policies, telemetry)

    with model_tab:
        _show_models(
            context,
            service,
            models,
            can_manage_global=can_manage_global,
        )

    with prompt_tab:
        _show_prompts(
            context,
            service,
            prompts,
            can_manage_global=can_manage_global,
        )

    with policy_tab:
        _show_policies(
            context,
            service,
            target_user_id=target_user_id,
            policies=policies,
            models=models,
            prompts=prompts,
            can_manage_scope=can_manage_scope,
        )

    with telemetry_tab:
        _show_telemetry(telemetry)


def _show_overview(
    models: list[dict[str, Any]],
    prompts: list[dict[str, Any]],
    policies: list[dict[str, Any]],
    telemetry: dict[str, Any],
) -> None:
    active_models = sum(1 for item in models if item.get("status") == "ACTIVE")
    active_prompts = sum(1 for item in prompts if item.get("status") == "ACTIVE")
    enabled_policies = sum(1 for item in policies if item.get("enabled"))
    summary = dict(telemetry.get("summary") or {})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active models", active_models)
    col2.metric("Active prompts", active_prompts)
    col3.metric("Enabled tasks", enabled_policies)
    col4.metric("AI requests", int(summary.get("total_requests") or 0))

    st.info(
        "Sprint 5.7.2A establishes the provider, policy, schema-validation and "
        "telemetry boundary. Candidate screening does not call AI until a later "
        "feature sprint explicitly integrates an approved task."
    )


def _show_models(
    context: SecurityContext,
    service: AIRegistryService,
    models: list[dict[str, Any]],
    *,
    can_manage_global: bool,
) -> None:
    if models:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Model Key": item["model_key"],
                        "Provider": item["provider_code"],
                        "Deployment": item["deployment_type"],
                        "Provider Model": item["model_name"],
                        "Display Name": item["display_name"],
                        "Structured": "Yes" if item["supports_structured_output"] else "No",
                        "Input $/1M": float(item["input_cost_per_million_usd"] or 0),
                        "Output $/1M": float(item["output_cost_per_million_usd"] or 0),
                        "Context": int(item["context_window"] or 0),
                        "Max Output": int(item["max_output_tokens"] or 0),
                        "Status": item["status"],
                    }
                    for item in models
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No AI models are registered. No model name is assumed by RecruitOS.")

    if not can_manage_global:
        st.caption("Model registration is restricted to the System Owner or Global Admin.")
        return

    with st.expander("Register a structured-output model"):
        with st.form("register_ai_model", clear_on_submit=False):
            left, right = st.columns(2)
            with left:
                model_key = st.text_input(
                    "Model Key",
                    placeholder="example: openai.primary-extraction",
                )
                provider_code = st.selectbox("Provider", ["OPENAI", "OLLAMA"])
                model_name = st.text_input(
                    "Provider Model Name",
                    help="Enter the exact deployed model identifier approved by your organization.",
                )
                display_name = st.text_input("Display Name")
                status = st.selectbox("Initial Status", ["ACTIVE", "INACTIVE"])
            with right:
                input_cost = st.number_input(
                    "Input Cost per 1M Tokens (USD)",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.6f",
                )
                output_cost = st.number_input(
                    "Output Cost per 1M Tokens (USD)",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.6f",
                )
                context_window = st.number_input(
                    "Context Window",
                    min_value=0,
                    value=0,
                    step=1000,
                )
                max_output_tokens = st.number_input(
                    "Maximum Output Tokens",
                    min_value=0,
                    value=0,
                    step=100,
                )
            submitted = st.form_submit_button(
                "Register Model",
                type="primary",
                use_container_width=True,
            )
        if submitted:
            try:
                service.register_model(
                    context,
                    model_key=model_key,
                    provider_code=provider_code,
                    model_name=model_name,
                    display_name=display_name,
                    supports_structured_output=True,
                    input_cost_per_million_usd=float(input_cost),
                    output_cost_per_million_usd=float(output_cost),
                    context_window=int(context_window),
                    max_output_tokens=int(max_output_tokens),
                    status=status,
                )
                st.success("AI model registered without storing a provider credential.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if models:
        model_options = {
            f"{item['display_name']} · {item['provider_code']} · {item['status']}": int(item["id"])
            for item in models
        }
        selected_label = st.selectbox("Model status target", list(model_options))
        new_status = st.radio(
            "New model status",
            ["ACTIVE", "INACTIVE"],
            horizontal=True,
        )
        if st.button("Update Model Status", use_container_width=True):
            try:
                service.set_model_status(
                    context,
                    model_id=model_options[selected_label],
                    status=new_status,
                )
                st.success("AI model status updated.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _show_prompts(
    context: SecurityContext,
    service: AIRegistryService,
    prompts: list[dict[str, Any]],
    *,
    can_manage_global: bool,
) -> None:
    if prompts:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Prompt Key": item["prompt_key"],
                        "Task": item["task_code"],
                        "Version": int(item["version_number"]),
                        "Status": item["status"],
                        "Created": item["created_at"],
                        "Activated": item["activated_at"],
                    }
                    for item in prompts
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No immutable AI prompt version is registered.")

    if not can_manage_global:
        st.caption("Prompt registration is restricted to the System Owner or Global Admin.")
        return

    with st.expander("Publish an immutable prompt version"):
        with st.form("publish_ai_prompt", clear_on_submit=False):
            prompt_key = st.text_input(
                "Prompt Key",
                placeholder="example: resume.structured-extraction",
            )
            task_code = st.text_input(
                "Task Code",
                placeholder="example: STRUCTURED_EXTRACTION",
            )
            system_template = st.text_area(
                "System Template",
                height=140,
                help="Use $variable placeholders. Prompts are versioned and immutable.",
            )
            user_template = st.text_area(
                "User Template",
                height=180,
                placeholder="Analyze the following approved input:\n$document_text",
            )
            output_schema_text = st.text_area(
                "JSON Output Schema",
                value=json.dumps(_DEFAULT_SCHEMA, indent=2),
                height=280,
            )
            activate_now = st.checkbox("Activate this prompt version immediately")
            submitted = st.form_submit_button(
                "Publish Prompt Version",
                type="primary",
                use_container_width=True,
            )
        if submitted:
            try:
                service.create_prompt_version(
                    context,
                    prompt_key=prompt_key,
                    task_code=task_code,
                    system_template=system_template,
                    user_template=user_template,
                    output_schema=output_schema_text,
                    activate=activate_now,
                )
                st.success("Immutable AI prompt version published.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    inactive = [item for item in prompts if item.get("status") != "ACTIVE"]
    if inactive:
        options = {
            f"{item['prompt_key']} · v{item['version_number']} · {item['task_code']} · {item['status']}": int(item["id"])
            for item in inactive
        }
        selected = st.selectbox("Prompt version to activate", list(options))
        if st.button("Activate Prompt Version", use_container_width=True):
            try:
                service.activate_prompt_version(
                    context,
                    prompt_version_id=options[selected],
                )
                st.success("Prompt version activated; the previous active version was retired.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _show_policies(
    context: SecurityContext,
    service: AIRegistryService,
    *,
    target_user_id: int,
    policies: list[dict[str, Any]],
    models: list[dict[str, Any]],
    prompts: list[dict[str, Any]],
    can_manage_scope: bool,
) -> None:
    if policies:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Task": item["task_code"],
                        "Enabled": "Yes" if item["enabled"] else "No",
                        "Model": item["model_key"],
                        "Provider": item["provider_code"],
                        "Prompt": f"{item['prompt_key']} v{item['prompt_version_number']}",
                        "External Transfer": "Allowed" if item["allow_external_data"] else "Blocked",
                        "Max Input Chars": int(item["max_input_chars"]),
                        "Timeout": int(item["timeout_seconds"]),
                        "Daily Limit": int(item["daily_request_limit"]),
                    }
                    for item in policies
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No AI task policy is assigned. AI execution is denied by default.")

    if not can_manage_scope:
        st.caption("Your AI policy is read-only.")
        return

    active_models = [item for item in models if item.get("status") == "ACTIVE"]
    active_prompts = [item for item in prompts if item.get("status") == "ACTIVE"]
    if not active_models or not active_prompts:
        st.warning(
            "At least one active structured-output model and one active prompt "
            "version are required before assigning a task policy."
        )
        return

    model_options = {
        f"{item['display_name']} · {item['provider_code']} · {item['model_key']}": item
        for item in active_models
    }
    task_codes = sorted({str(item["task_code"]) for item in active_prompts})
    task_code = st.selectbox("AI Task", task_codes)
    task_prompts = [item for item in active_prompts if item["task_code"] == task_code]
    prompt_options = {
        f"{item['prompt_key']} · v{item['version_number']}": item
        for item in task_prompts
    }
    selected_model_label = st.selectbox("Approved Model", list(model_options))
    selected_prompt_label = st.selectbox("Active Prompt Version", list(prompt_options))
    selected_model = model_options[selected_model_label]

    enabled = st.checkbox("Enable this AI task", value=False)
    allow_external = st.checkbox(
        "Allow approved content to leave the local environment",
        value=False,
        disabled=selected_model["deployment_type"] != "HOSTED",
        help=(
            "Required for hosted providers. Keep disabled unless organizational "
            "privacy and data-transfer approval is documented."
        ),
    )
    col1, col2, col3 = st.columns(3)
    max_input_chars = col1.number_input(
        "Max Input Characters",
        min_value=1_000,
        max_value=2_000_000,
        value=120_000,
        step=1_000,
    )
    timeout_seconds = col2.number_input(
        "Timeout Seconds",
        min_value=5,
        max_value=600,
        value=60,
        step=5,
    )
    daily_request_limit = col3.number_input(
        "Daily Request Limit",
        min_value=1,
        max_value=100_000,
        value=100,
        step=10,
    )

    if st.button(
        "Save AI Task Policy",
        type="primary",
        use_container_width=True,
    ):
        try:
            service.set_policy(
                context,
                target_user_id=target_user_id,
                task_code=task_code,
                model_id=int(selected_model["id"]),
                prompt_version_id=int(prompt_options[selected_prompt_label]["id"]),
                enabled=enabled,
                allow_external_data=(
                    bool(allow_external)
                    if selected_model["deployment_type"] == "HOSTED"
                    else False
                ),
                max_input_chars=int(max_input_chars),
                timeout_seconds=int(timeout_seconds),
                daily_request_limit=int(daily_request_limit),
            )
            st.success("AI task policy saved. No credential was stored.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _show_telemetry(telemetry: dict[str, Any]) -> None:
    summary = dict(telemetry.get("summary") or {})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Requests", int(summary.get("total_requests") or 0))
    col2.metric("Failures", int(summary.get("failures") or 0))
    col3.metric(
        "Average Latency",
        f"{float(summary.get('average_latency_ms') or 0):.0f} ms",
    )
    col4.metric(
        "Estimated Cost",
        f"${float(summary.get('estimated_cost_usd') or 0):.6f}",
    )

    events = list(telemetry.get("events") or [])
    if not events:
        st.info("No AI inference telemetry exists for this workspace.")
        return
    st.dataframe(
        pd.DataFrame(events),
        use_container_width=True,
        hide_index=True,
        column_order=[
            "created_at",
            "task_code",
            "provider_code",
            "model_key",
            "outcome",
            "latency_ms",
            "input_tokens",
            "output_tokens",
            "estimated_cost_usd",
            "error_code",
            "error_message_redacted",
            "request_id",
        ],
    )
    st.caption(
        "Telemetry contains operational metadata only. Prompt text, candidate text, "
        "provider credentials and structured response content are not persisted."
    )


def _target_user(context: SecurityContext, can_manage_scope: bool) -> tuple[int, str]:
    if not can_manage_scope:
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
    selected = st.selectbox("AI policy workspace user", labels, index=index)
    return options[selected], selected
