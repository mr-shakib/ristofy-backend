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

### Phase 5 (In Progress — Step A completed)
- **Bill model** implemented: tenant, branch, order, bill_no (sequential per branch), status, totals fields.
- **BillLine model** implemented: source_type, source_id, description, quantity, unit_price, vat_rate, line_total.
- **Create from order** implemented: POST `/api/v1/bills/create-from-order` (auto-builds ORDER_ITEM lines from non-canceled items).
- **Bill detail** implemented: GET `/api/v1/bills/{id}`.
- **Routing** implemented: billing URLs included in core API routing.
- **Tests added** for success flow, totals, duplicate bill rejection, permissions, and tenant isolation.
- **Validation run complete**: `manage.py check`, `makemigrations --check --dry-run`, `manage.py test billing`, and full `manage.py test` passed (106 tests total).

## 2) New Migrations

- orders/migrations/0005_buffetplan_buffetsession_wastelog_buffetround.py
- billing/migrations/0001_initial.py

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
- PrintJob stays QUEUED — Go bridge integration is Phase 6.
- Phase 5 Step C/D still pending: coperto, discount, finalize, payment.
- Default project `.venv` is Python 3.11 (incompatible with pinned Django 6.0.4); local validation was executed using a Python 3.14 virtualenv.

## 5) Where To Start Next (Phase 5 — Billing Engine)

### Step B: Completed
- BillLine model and ORDER_ITEM line creation are implemented.

### Step C: Bill actions (Next)
- POST /api/v1/bills/{id}/apply-coperto  — body: `{"amount": "2.00", "covers": 4}`
- POST /api/v1/bills/{id}/apply-discount — body: `{"type": "PERCENT"|"FIXED", "value": "10.00"}`
- POST /api/v1/bills/{id}/finalize — transitions DRAFT → FINALIZED, locks lines

### Step D: Payment model + record payment
- Fields: bill, method (CASH/CARD/OTHER), amount, reference, paid_at
- POST /api/v1/bills/{id}/pay — body: `{"method": "CASH", "amount": "50.00"}`
- Transitions bill to PAID when amount_paid >= grand_total

### Step E: Tests and docs
- Completed for Step A in this session:
	- docs/api-postman-guide.md updated with implemented billing Step A endpoints
	- docs/backend-roadmap.md updated with Phase 5 in-progress status
	- docs/session-handoff.md updated with this handoff
- Remaining tests/docs for Step C/D will be added when those endpoints are implemented.

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

"Continue from docs/session-handoff.md. Phase 5 Step A is complete (Bill/BillLine + create-from-order + bill detail). Implement Step C and D: apply-coperto, apply-discount, finalize, and pay endpoints with strict tenant/branch isolation. Add tests and docs updates. Run check + makemigrations --check --dry-run + tests and report changed files and endpoint list."

## 8) Definition Of Done For Phase 5

- Bill created from order with correct VAT-safe line totals.
- Coperto and discount actions functional and tested.
- Finalize locks lines; pay records payment and marks bill PAID.
- No pending migrations. All tests passing. Docs updated.

## 9) Audit Notes (2026-04-10)

- Verified in code: billing Step A endpoints are routed and implemented.
- Verified migration added: billing/migrations/0001_initial.py.
- Known local environment issue: Python 3.11 is incompatible with pinned Django 6.0.4.
- Next implementation priority: Phase 5 Step C and D.
