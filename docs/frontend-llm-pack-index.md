# Frontend LLM Pack Index

Last updated: 2026-04-11

Use this as the single entry point when giving context to LLMs for desktop app implementation.

## 1. Core Product and Scope

1. Product blueprint:
- docs/frontend-desktop-final-blueprint.md

2. Planning context:
- docs/frontend-desktop-planning.md

3. Backend feature and API detail:
- docs/api-postman-guide.md
- docs/backend-roadmap.md
- docs/session-handoff.md

## 2. LLM Execution Contracts

1. Endpoint contracts:
- docs/frontend-api-contract-catalog.md

2. Role and permissions:
- docs/frontend-role-capability-matrix.md

3. State machines:
- docs/frontend-state-transition-spec.md

4. Error behavior:
- docs/frontend-error-handling-contract.md

5. Screen-level contracts:
- docs/frontend-screen-contracts.md

6. Offline sync contract:
- docs/frontend-sync-offline-spec.md

7. Non-functional and release gates:
- docs/frontend-nfr-release-gates.md

8. Swagger availability status:
- docs/swagger-status.md

## 3. LLM Instruction Order (Recommended)

Feed docs in this order:
1. frontend-desktop-final-blueprint
2. frontend-api-contract-catalog
3. frontend-role-capability-matrix
4. frontend-state-transition-spec
5. frontend-error-handling-contract
6. frontend-screen-contracts
7. frontend-sync-offline-spec
8. frontend-nfr-release-gates
9. api-postman-guide (examples)

## 4. Prompt Guardrails

1. Frontend code must be developed outside backend repository.
2. Follow role guards exactly as backend permissions define.
3. Implement offline queue and sync from day one.
4. Do not skip tests for auth, order lifecycle, billing, and sync.
5. Treat this pack as source of truth over ad-hoc assumptions.
