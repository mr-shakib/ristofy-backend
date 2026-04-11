# Frontend Non-Functional Requirements and Release Gates

Last updated: 2026-04-11

## 1. Performance Requirements

1. Warm start to role dashboard <= 3 seconds.
2. Login API feedback <= 1 second p50 on local network.
3. Order item add interaction <= 300 ms perceived response.
4. Table live status refresh <= 2 seconds for visible updates.
5. Sync push batch <= 5 seconds for standard shift workload.

## 2. Reliability Requirements

1. Zero silent mutation loss.
2. Offline queue durability across app restarts.
3. Conflict visibility at all times.
4. Graceful degradation when health/db endpoint fails.

## 3. Security Requirements

1. Store tokens in secure storage only.
2. No plaintext PIN persistence.
3. Redact sensitive fields in logs.
4. Enforce route and action role guards.
5. Auto logout on refresh expiration.

## 4. Observability Requirements

1. Structured client logs with endpoint + status + latency.
2. Error analytics integration.
3. Screen-level performance traces for critical flows.
4. Diagnostic export bundle for support investigations.

## 5. Test Coverage Gates

1. Unit tests >= 80% for core services (auth, sync, API mapping).
2. Integration tests for full dine-in and billing flow.
3. Regression tests for permission-based UI guards.
4. Offline/online transition test scenarios.

## 6. UAT Gates

1. Dine-in peak simulation passes.
2. Takeaway burst simulation passes.
3. Kitchen throughput scenario passes.
4. Fiscal action scenario passes.
5. End-of-day closure checklist passes.

## 7. Release Checklist

1. All critical defects fixed.
2. Contract validation against backend endpoints completed.
3. Performance and reliability SLOs met.
4. Pilot branch signoff complete.
5. Rollback strategy documented.

## 8. Go-Live Readiness Decision

Ship only if all below are true:
1. No blocker severity bugs open.
2. No unresolved sync conflict handling defects.
3. Payment and fiscal flows verified by acceptance scripts.
4. Role-based unauthorized actions fully blocked.
