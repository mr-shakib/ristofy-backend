# Session Handoff (Low-Token Starter)

Last updated: 2026-04-11

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

### Phase 7 (Completed)
- **Ingredient model** implemented: tenant, branch, name, sku, unit, current_stock, min_stock_level, is_active.
- **StockMovement model** implemented: append-only movement ledger with `stock_before`/`stock_after` snapshots.
- **RecipeComponent model** implemented: menu item to ingredient quantity mapping per branch.
- **Inventory API implemented**:
	- GET/POST `/api/v1/inventory/ingredients`
	- GET/PATCH/DELETE `/api/v1/inventory/ingredients/{id}`
	- GET/POST `/api/v1/inventory/recipes`
	- GET/PATCH/DELETE `/api/v1/inventory/recipes/{id}`
	- GET/POST `/api/v1/inventory/movements`
	- POST `/api/v1/inventory/receivings`
	- GET `/api/v1/inventory/reports/low-stock`
	- GET `/api/v1/inventory/reports/usage`
- **Stock safety rule** implemented: stock movement writes are atomic and reject negative resulting stock.
- **Order integration implemented**: firing/sending orders to kitchen auto-deducts stock based on active recipe components.
- **Tests added** for role permissions, tenant isolation on writes/reads, low-stock filtering, movement constraints, recipe mapping, receiving flow, usage analytics, and fire-flow stock rollback safety.
- **Validation run complete**: `manage.py check`, `makemigrations --check --dry-run`, `manage.py test inventory`, `manage.py test orders`, and full `manage.py test` passed (140 tests total) using Python 3.14 with PostgreSQL.

### Phase 8 (Completed)
- **Customer model** implemented with tenant-scoped profile data (name/phone/email/preferences).
- **Loyalty models** implemented: CustomerVisit and LoyaltyRule.
- **TakeawayOrder model** implemented and linked to core orders.
- **Order model updated** with optional customer relation.
- **Takeaway API implemented**:
	- POST `/api/v1/takeaway/orders`
	- GET `/api/v1/takeaway/orders/{id}`
	- POST `/api/v1/takeaway/orders/{id}/ready`
- **Loyalty API implemented**:
	- GET `/api/v1/loyalty/customers/{phone}`
	- POST `/api/v1/loyalty/visits`
	- GET `/api/v1/loyalty/eligibility`
- **Packaging and extra fee rules** implemented as non-kitchen order lines on takeaway creation.
- **Role boundary enforcement** validated for waiter/cashier access and kitchen denial.
- **Validation run complete**: `manage.py check`, `makemigrations --check --dry-run`, `manage.py test orders`, and full `manage.py test` passed (146 tests total) using Python 3.14 with PostgreSQL.

## 2) New Migrations

- orders/migrations/0005_buffetplan_buffetsession_wastelog_buffetround.py
- billing/migrations/0001_initial.py
- billing/migrations/0002_payment.py
- billing/migrations/0003_receipt_fiscaltransaction_refund.py
- inventory/migrations/0001_initial.py
- inventory/migrations/0002_alter_stockmovement_movement_type_recipecomponent.py
- orders/migrations/0006_customer_order_customer_customervisit_loyaltyrule_and_more.py

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

## 5) Where To Start Next (Phase 9)

### Phase 8: Completed
- Takeaway and loyalty scope delivered in production-grade shape.

### Next Priority (Phase 9 — Reporting)
- Daily report snapshots
- Sales views by category/table/waiter/VAT
- Buffet and branch comparison reports
- Report cache + refresh strategy

## 6) Next Session Quick Commands

```bash
# Linux/macOS
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py test

# Windows (PowerShell)
.\.venv314\Scripts\python.exe manage.py check
.\.venv314\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv314\Scripts\python.exe manage.py test
```

Note: the default `.venv` is Python 3.11 and incompatible with pinned Django 6.0.4. Use `.venv314` (Python 3.14) or any Python 3.12+ environment.

## 7) Copy-Paste Prompt For Next Session

"Continue from docs/session-handoff.md. Phase 8 takeaway and loyalty is complete with production-grade endpoints and tests. Start Phase 9 reporting (daily snapshots, sales dimensions, VAT, buffet/branch views, caching) with strict tenant isolation, tests, and docs updates."

## 8) Definition Of Done For Phase 5

- Bill created from order with correct VAT-safe line totals.
- Coperto and discount actions functional and tested.
- Finalize locks lines; pay records payment and marks bill PAID.
- No pending migrations. All tests passing. Docs updated.

## 9) Audit Notes (2026-04-11)

- Verified in code: billing Step A-D endpoints and payment workflow are implemented.
- Verified in code: fiscal integration endpoints (send-to-fiscal, receipt actions, z-report sync/status, bridge ack) are implemented.
- Verified migrations added: billing/migrations/0001_initial.py, billing/migrations/0002_payment.py, billing/migrations/0003_receipt_fiscaltransaction_refund.py.
- Verified in code: inventory full phase endpoints implemented (ingredients, recipes, movements, receiving, low-stock, usage) with tenant isolation.
- Verified in code: order fire/send-to-kitchen flow auto-deducts stock from active recipe components with rollback safety on insufficiency.
- Verified migrations added: inventory/migrations/0001_initial.py and inventory/migrations/0002_alter_stockmovement_movement_type_recipecomponent.py.
- Verified in code: Phase 8 endpoints implemented (takeaway create/detail/ready, loyalty customer lookup, loyalty visits, loyalty eligibility).
- Verified migration added: orders/migrations/0006_customer_order_customer_customervisit_loyaltyrule_and_more.py.
- Validation rerun with PostgreSQL and Python 3.14: 146 tests passing.
- Known local environment issue: Python 3.11 is incompatible with pinned Django 6.0.4.
- Next implementation priority: Phase 9 reporting.
