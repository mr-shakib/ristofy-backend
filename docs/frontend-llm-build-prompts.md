# Frontend LLM Build Prompts

Last updated: 2026-04-11

This file provides ready-to-use prompts for coding agents/LLMs.

## Prompt 1: Project Bootstrap

Create a production desktop app repository outside backend repo using Flutter desktop with Riverpod, Dio, go_router, and SQLite-backed offline queue.

Requirements:
1. Implement modular folder structure by feature domain.
2. Add secure token storage and auth interceptor with refresh-once retry.
3. Add CI jobs for format, analyze, test, and desktop build.
4. Add unit test scaffolding for core services.

Use these documents as source of truth:
- docs/frontend-desktop-final-blueprint.md
- docs/frontend-api-contract-catalog.md
- docs/frontend-role-capability-matrix.md
- docs/frontend-sync-offline-spec.md

## Prompt 2: Vertical Slice (Dine-in)

Implement one complete dine-in flow:
1. Login and bootstrap.
2. Table live status and open-session.
3. Create order and add items.
4. Fire/send to kitchen.
5. Kitchen ticket prepared.
6. Request bill and complete payment flow.

Constraints:
1. Respect role capabilities and route guards.
2. Add integration tests for this flow.
3. Implement deterministic error mapping.
4. No hardcoded endpoint strings inside widgets.

## Prompt 3: Cashier and Fiscal

Implement cashier module:
1. Bill create, coperto, discount, split, finalize, pay.
2. Fiscal send and receipt reprint/refund.
3. Payment validation and status transitions.
4. Test scenarios for partial and complete payment.

Use state machine and error contract docs strictly.

## Prompt 4: Offline Sync

Implement local outbox and sync engine:
1. Queue mutating actions with idempotency keys.
2. Push queue to /sync/push.
3. Pull deltas using cursor via /sync/pull.
4. Conflict panel with manual resolution actions.

Include tests:
1. idempotency replay
2. conflict handling
3. network outage recovery

## Prompt 5: Release Hardening

Prepare app for production release:
1. Meet non-functional targets from frontend-nfr-release-gates.md.
2. Add observability instrumentation and error reporting hooks.
3. Build UAT scripts for peak-hour dine-in/takeaway.
4. Produce release checklist report.

## Prompt Usage Notes

1. Run prompts in sequence.
2. Keep output aligned to the document pack.
3. If agent assumptions conflict with docs, docs must win.
