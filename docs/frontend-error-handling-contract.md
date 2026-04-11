# Frontend Error Handling Contract

Last updated: 2026-04-11

This contract standardizes UI behavior for API failures in production.

## 1. Error Envelope Policy

1. Prefer field map rendering for 400 serializer validation errors.
2. Support detail-string responses for non-field errors.
3. Preserve original backend error body in logs for diagnostics.

## 2. Status Code Matrix

| Status | Meaning | Frontend Behavior | Retry Policy |
|---|---|---|---|
| 400 | Validation/business rule failure | Show inline field and top-level errors; keep user input | No auto-retry |
| 401 | Access token invalid/expired | Attempt refresh once, replay request once | Auto once |
| 403 | Permission denied | Show capability denied message; hide restricted action | No auto-retry |
| 404 | Entity missing/stale | Show stale-data message and navigate to safe list state | No auto-retry |
| 409 or 400 conflict-style detail | Domain conflict | Show conflict resolution UI | Manual decision |
| 423 | PIN temporarily locked | Show lockout timer and fallback to password login | Retry after timeout |
| 429 | Rate limited | Show cooldown toast/banner and disable rapid repeats | Retry with backoff |
| 500-599 | Server failure | Show non-blocking error; queue safe mutations if offline mode enabled | Limited retry |
| Network timeout/offline | Connectivity failure | Mark offline, queue mutation, continue local flow when possible | Background retry |

## 3. Domain-Specific Cases

1. Auth
- Login invalid credentials: concise message, no stack details.
- PIN lock: include unlock guidance.

2. Orders
- No pending items to fire: show info-level action feedback.
- Terminal order mutation attempts: disable action and refresh order.

3. Billing
- Duplicate bill creation attempt: redirect to existing bill if available.
- Payment below required constraints: stay on payment form.

4. Sync
- Unknown device_uuid or tenant mismatch: force device re-registration flow.
- Conflict results from /sync/push: queue to manual review panel.

## 4. UI Presentation Rules

1. Toast for transient action failures.
2. Inline message for form validation.
3. Blocking dialog only for irreversible failure cases.
4. Error copy must include next action guidance.

## 5. Logging and Audit

1. Capture:
- endpoint
- method
- status code
- request id/correlation id if available
- response body snippet

2. Redact:
- password
- pin
- token
- payment references with sensitive details

## 6. LLM Implementation Checklist

1. Central ErrorMapper with deterministic category output.
2. Shared UI components for field, banner, and modal errors.
3. One retry utility with exponential backoff and jitter.
4. Per-domain fallback handlers for auth, sync, billing.
