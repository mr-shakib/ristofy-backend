# Session Handoff (Low-Token Starter)

Last updated: 2026-04-09

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

## 2) New Migrations

- orders/migrations/0005_buffetplan_buffetsession_wastelog_buffetround.py

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

## 5) Where To Start Next (Phase 5 — Billing Engine)

### Step A: Bill model
- Fields: tenant, branch, order (FK), bill_no (sequential per branch), status (DRAFT/FINALIZED/PAID), subtotal, vat_total, coperto_total, service_charge_total, waste_total, discount_total, grand_total
- Auto-build bill lines from order items on creation
- POST /api/v1/bills/create-from-order  — body: `{"order": <id>}`
- GET /api/v1/bills/{id}

### Step B: BillLine model
- source_type (ORDER_ITEM / COPERTO / SERVICE / DISCOUNT / WASTE), source_id (nullable), description, quantity, unit_price, vat_rate, line_total

### Step C: Bill actions
- POST /api/v1/bills/{id}/apply-coperto  — body: `{"amount": "2.00", "covers": 4}`
- POST /api/v1/bills/{id}/apply-discount — body: `{"type": "PERCENT"|"FIXED", "value": "10.00"}`
- POST /api/v1/bills/{id}/finalize — transitions DRAFT → FINALIZED, locks lines

### Step D: Payment model + record payment
- Fields: bill, method (CASH/CARD/OTHER), amount, reference, paid_at
- POST /api/v1/bills/{id}/pay — body: `{"method": "CASH", "amount": "50.00"}`
- Transitions bill to PAID when amount_paid >= grand_total

### Step E: Tests and docs

## 6) Next Session Quick Commands

```bash
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py test
```

## 7) Copy-Paste Prompt For Next Session

"Continue from docs/session-handoff.md. Phase 4 is complete. Implement Phase 5: Bill model (create-from-order, bill lines, coperto, discount, finalize), Payment model, and pay endpoint. Keep tenant/branch isolation strict. Run check + makemigrations --check --dry-run + tests and report changed files and endpoint list."

## 8) Definition Of Done For Phase 5

- Bill created from order with correct VAT-safe line totals.
- Coperto and discount actions functional and tested.
- Finalize locks lines; pay records payment and marks bill PAID.
- No pending migrations. All tests passing. Docs updated.
