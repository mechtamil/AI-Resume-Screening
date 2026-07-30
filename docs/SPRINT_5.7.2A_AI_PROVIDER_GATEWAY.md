# Sprint 5.7.2A — AI Provider Gateway & Model Registry

## Objective

Create the governed AI transport boundary required before RecruitOS can add AI extraction, semantic retrieval or recruiter assistance. Deterministic screening remains authoritative and unchanged.

## Delivered architecture

### Provider abstraction

- `OpenAIResponsesProvider` sends structured requests through the Responses API.
- `OllamaProvider` sends structured requests to a configured local `/api/chat` endpoint.
- Both implement the same provider-neutral contract.
- Standard-library HTTP transport applies request timeouts and response-size limits.

### Secret boundary

Deployment credentials are read from:

1. environment variables;
2. Streamlit deployment secrets.

The database, telemetry, audit events, exports, UI and source-controlled examples never store a real credential.

### Registry and policy

Schema version 7 adds:

- `ai_model_registry`;
- `ai_prompt_versions`;
- `tenant_ai_policies`;
- `ai_inference_events`.

Models are registered with explicit provider identifiers, capabilities and optional cost metadata. Prompt versions are immutable. A user-workspace task policy selects one active model and one active prompt version and controls execution, hosted transfer, input limits, timeout and daily volume.

### Structured output

RecruitOS validates provider output against a controlled JSON Schema subset before returning it to a caller. Invalid JSON, missing required fields, unexpected properties and type/range violations fail closed.

### Telemetry

Telemetry contains only:

- task, provider, model and prompt identifiers;
- request identifier and outcome;
- latency and character/token counts;
- estimated cost;
- redacted error code/message;
- timestamp.

Prompt text, resume/JD text, candidate data, response payloads, credentials and raw provider envelopes are excluded.

## Environment settings

```text
RECRUITOS_OPENAI_API_KEY
RECRUITOS_OPENAI_BASE_URL
RECRUITOS_OLLAMA_BASE_URL
RECRUITOS_AI_HTTP_TIMEOUT_SECONDS
RECRUITOS_AI_MAX_RESPONSE_BYTES
RECRUITOS_AI_DEFAULT_MAX_INPUT_CHARS
RECRUITOS_AI_DEFAULT_DAILY_REQUEST_LIMIT
```

## Non-goals

- No AI call is made from Resume Screening.
- Deterministic scores and recommendations are unchanged.
- No default external model is assumed.
- No prompt or model is auto-activated.
- No candidate data is sent during provider configuration.

## Acceptance criteria

- Schema 6 migrates to schema 7 without data loss.
- Model and prompt registration requires global AI-policy permission.
- Tenant Admin policy changes remain Country/Location scoped.
- Users can view only their own effective policy and telemetry.
- Reader role has no AI execution or policy permission.
- AI tasks are denied until explicitly enabled.
- Hosted tasks are denied until external transfer is explicitly approved.
- Provider output must pass structured validation.
- Telemetry contains no prompt, candidate or output content.
- Provider secrets are never persisted or rendered.
- Existing deterministic screening tests remain green.
