# Session Handoff (Low-Token Starter)

Last updated: 2026-04-10

## 1) What Is Done

### Phase 0–3 (Completed)
See docs/backend-roadmap.md for full detail. Summary:
- Platform foundation, auth, users, menu, dining layout, full order lifecycle with kitchen tickets, printer routing foundation, and event stubs.
- 66 tests from Phase 0–3.

### Phase 4 (Completed)
- **BuffetPlan**: branch-scoped CRUD; fields: name, base_price, kids_price, time_limit_minutes, waste_penalty_amount, round_limit_per_person, round_delay_seconds, active_from/to, is_active.
- **BuffetSession**: start (auto-computes ends_at from plan), detail with nested rounds + is_expired flag, end (auto-closes open round).
- **BuffetRound**: new-round (enforces limit + delay), close-round; round_number auto-increments.
- **WasteLog**: POST /waste-logs; penalty auto-calculated from buffet session plan; marked_by = caller.
- **Analytics**: GET /buffet/analytics — sessions, adults, kids, waste totals; filterable by branch + date.
- 98 tests passing (32 new).

### Phase 5 (Completed — core scope)
- **Bill model** implemented: tenant, branch, order, bill_no (sequential per branch), status, totals fields.
- **BillLine model** implemented: source_type, source_id, description, quantity, unit_price, vat_rate, line_total.
- **Create from order** implemented: POST `/api/v1/bills/create-from-order` (auto-builds ORDER_ITEM lines from non-canceled items).
- **Bill detail** implemented: GET `/api/v1/bills/{id}`.
- **Routing** implemented: billing URLs included in core API routing.
- **Tests added** for success flow, totals, duplicate bill rejection, permissions, and tenant isolation.
- **Step C/D implemented**: apply-coperto, apply-discount, finalize, and pay endpoints.
- **Payment model implemented**: method, amount, reference, paid_at; bill moves to `PAID` when cumulative payments cover `grand_total`.
- **Validation run complete**: `manage.py check`, `makemigrations --check --dry-run`, `manage.py test billing`, and full `manage.py test` passed (125 tests total).

### Phase 6 (Completed)
- **FiscalTransaction model** implemented with transaction type/status lifecycle and external_id tracking.
- **Receipt lifecycle** implemented:
	- POST `/api/v1/bills/{id}/send-to-fiscal`
	- GET `/api/v1/receipts/{id}`
	- POST `/api/v1/receipts/{id}/reprint`
	- POST `/api/v1/receipts/{id}/refund`
- **Z report endpoints** implemented:
	- GET `/api/v1/fiscal/z-report/status`
	- POST `/api/v1/fiscal/z-report/sync`
- **Bridge callback endpoint** implemented:
	- POST `/api/v1/integrations/bridge/fiscal-ack`
- Fiscal tests added for send/reprint/refund/z-report/ack + isolation + permissions.

## 2) New Migrations

- orders/migrations/0005_buffetplan_buffetsession_wastelog_buffetround.py
- billing/migrations/0001_initial.py
- billing/migrations/0002_payment.py
- billing/migrations/0003_receipt_fiscaltransaction_refund.py

## 3) Phase 4 API Surface

- GET/POST /api/v1/buffet/plans
- GET/PATCH /api/v1/buffet/plans/{id}
- POST /api/v1/buffet/sessions/start
- GET /api/v1/buffet/sessions/{id}
- POST /api/v1/buffet/sessions/{id}/end
- POST /api/v1/buffet/sessions/{id}/new-round
- POST /api/v1/buffet/sessions/{id}/close-round
- POST /api/v1/waste-logs
- GET /api/v1/buffet/analytics

For payloads, see docs/api-postman-guide.md §3.27–3.30.

## 4) Known Open Items

- JWT HMAC key warning in tests (env SECRET_KEY < 32 chars, not a code issue).
- publish_order_event() stubs to logs — wire to Redis when dispatcher is ready.
- PrintJob stays QUEUED — full bridge/device transport remains pending beyond current fiscal API completion.
- Fiscal integration currently uses simulated completion flow (no real device/bridge transport yet).
- Default project `.venv` is Python 3.11 (incompatible with pinned Django 6.0.4); local validation was executed using a Python 3.14 virtualenv.

## 5) Where To Start Next (Phase 7 — Inventory Integration)

### Phase 5 + 6: Completed
- Billing core and fiscal integration API surface implemented and tested.

### Next Priority (Phase 7)
- Ingredient and stock core models
- Stock movement ledger endpoints
- Low-stock report endpoint
- Tests for tenant/branch isolation on inventory writes

## 6) Next Session Quick Commands

```bash
# Linux/macOS
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py test

# Windows (PowerShell)
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

Note: for this repository's pinned Django 6.0.4, use Python 3.12+.

## 7) Copy-Paste Prompt For Next Session

"Continue from docs/session-handoff.md. Phase 6 fiscal integration is complete. Start Phase 7 inventory integration with Ingredient/stock movement core models, low-stock endpoint, strict tenant/branch isolation, and test coverage. Update docs and run check + makemigrations --check --dry-run + tests."

## 8) Definition Of Done For Phase 5

- Bill created from order with correct VAT-safe line totals.
- Coperto and discount actions functional and tested.
- Finalize locks lines; pay records payment and marks bill PAID.
- No pending migrations. All tests passing. Docs updated.

## 9) Audit Notes (2026-04-10)

- Verified in code: billing Step A-D endpoints and payment workflow are implemented.
- Verified in code: fiscal integration endpoints (send-to-fiscal, receipt actions, z-report sync/status, bridge ack) are implemented.
- Verified migrations added: billing/migrations/0001_initial.py, billing/migrations/0002_payment.py, billing/migrations/0003_receipt_fiscaltransaction_refund.py.
- Known local environment issue: Python 3.11 is incompatible with pinned Django 6.0.4.
- Next implementation priority: Phase 7 inventory integration.
