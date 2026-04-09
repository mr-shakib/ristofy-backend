# Session Handoff (Low-Token Starter)

Last updated: 2026-04-09

## 1) What Is Done

### Phase 0 (Completed)
- Environment-based configuration and security baseline in settings.
- CI checks and migration drift checks are active.
- Repo hygiene in place (.gitignore, docs flow, env template).

### Phase 1 (Completed)
- Tenant registration and branch creation.
- Role-aware user management.
- Password and PIN login.
- Token refresh/logout.
- Current-user profile endpoint.
- Session and activity logging.
- Test coverage for key auth/account flows.

### Phase 2 (Completed)
- Menu: Categories and items CRUD, allergen catalog, item-allergen mapping, schedule windows, filtering + pagination.
- Dining layout: Floor plans and tables CRUD, reservations CRUD + status actions (arrived/cancel), overlap protection, waitlist CRUD + status actions (call/seat/cancel), table state sync.

### Phase 3 (Slices 1–3 Complete)
- Order and OrderItem models with full status lifecycle (OPEN → SENT_TO_KITCHEN → PARTIALLY_SERVED → COMPLETED → CANCELED).
- order_no: auto-incremented per branch, unique constraint, exposed in all responses.
- POST /api/v1/orders — create with items (snapshot name/price/vat from MenuItem).
- GET /api/v1/orders — list with branch/status/channel filters + pagination.
- GET/PATCH /api/v1/orders/{id} — detail and update.
- POST /api/v1/orders/{id}/send-to-kitchen — transitions order + items, auto-creates KitchenTicket.
- POST /api/v1/orders/{id}/cancel — OWNER/MANAGER only.
- POST /api/v1/orders/{id}/complete — OWNER/MANAGER only.
- POST /api/v1/orders/{id}/items — add item to existing order.
- PATCH /api/v1/orders/{id}/items/{item_id} — update item qty/notes/status.
- DELETE /api/v1/orders/{id}/items/{item_id} — remove item.
- GET /api/v1/kitchen/tickets — list tickets with branch/status filters.
- POST /api/v1/kitchen/tickets/{id}/prepared — mark ticket prepared.
- IsWaiterOrAbove permission: WAITER/CASHIER/MANAGER/OWNER can create orders and manage items; cancel/complete restricted to OWNER/MANAGER.
- 46 tests passing.

## 2) New Migrations In This Session

- orders/migrations/0001_initial.py
- orders/migrations/0002_kitchenticket.py
- orders/migrations/0003_order_order_no_order_uniq_order_no_per_branch.py

## 3) Current API Surface Added Recently

- /api/v1/orders (GET, POST)
- /api/v1/orders/{id} (GET, PATCH)
- /api/v1/orders/{id}/send-to-kitchen (POST)
- /api/v1/orders/{id}/cancel (POST)
- /api/v1/orders/{id}/complete (POST)
- /api/v1/orders/{id}/items (POST)
- /api/v1/orders/{id}/items/{item_id} (PATCH, DELETE)
- /api/v1/kitchen/tickets (GET)
- /api/v1/kitchen/tickets/{id}/prepared (POST)

For payloads and responses, use docs/api-postman-guide.md §3.23–3.26.

## 4) Known Open Item

- JWT warning about short HMAC key can appear in tests when env key is too short.
- Recommendation: keep signing key >= 32 chars in local and CI env.

## 5) Where To Start Next (Phase 4 — Buffet)

Phase 3 is functionally complete for the core order lifecycle. Next is Phase 4: Buffet and hybrid mode.

### Step A: BuffetPlan model
- Fields: branch, name, base_price, kids_price, time_limit_minutes, waste_penalty_amount, round_limit_per_person, round_delay_seconds, active_from, active_to
- CRUD: GET/POST /api/v1/buffet/plans, PATCH /api/v1/buffet/plans/{id}

### Step B: BuffetSession model
- Fields: tenant, branch, table_session (nullable for now), buffet_plan, adults_count, kids_count, started_at, ends_at, status (ACTIVE/ENDED)
- POST /api/v1/buffet/sessions/start
- GET /api/v1/buffet/sessions/{id}
- POST /api/v1/buffet/sessions/{id}/end

### Step C: BuffetRound model
- Fields: buffet_session, round_number, opened_at, closed_at
- POST /api/v1/buffet/sessions/{id}/new-round
- POST /api/v1/buffet/sessions/{id}/close-round

### Step D: Tests and docs

## 6) Next Session Quick Commands

Run at session start:

```bash
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py test
```

## 7) Copy-Paste Prompt For Next Session

"Continue from docs/session-handoff.md. Implement Phase 4: BuffetPlan, BuffetSession, and BuffetRound models with CRUD and session lifecycle endpoints. Keep tenant/branch isolation strict. Run check + makemigrations --check --dry-run + tests and report changed files and endpoint list."

## 8) Definition Of Done For Next Session

- Buffet plan CRUD functional and tested.
- Buffet session start/end functional and tested.
- Buffet round new/close functional and tested.
- No pending migrations.
- All tests passing.
- Postman and roadmap docs updated in same change.
