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

### Phase 3 (In Progress — Slice 1 + 2 Complete)
- Order and OrderItem models with full status lifecycle.
- POST /api/v1/orders — create with items (snapshot name/price/vat from MenuItem).
- GET /api/v1/orders — list with branch/status/channel filters + pagination.
- GET/PATCH /api/v1/orders/{id} — detail and update.
- POST /api/v1/orders/{id}/send-to-kitchen — transitions order + items, auto-creates KitchenTicket.
- POST /api/v1/orders/{id}/items — add item to existing order.
- PATCH /api/v1/orders/{id}/items/{item_id} — update item qty/notes/status.
- DELETE /api/v1/orders/{id}/items/{item_id} — remove item.
- GET /api/v1/kitchen/tickets — list tickets with branch/status filters.
- POST /api/v1/kitchen/tickets/{id}/prepared — mark ticket prepared.
- 36 tests passing.

## 2) New Migrations In This Session

- orders/migrations/0001_initial.py
- orders/migrations/0002_kitchenticket.py

## 3) Current API Surface Added Recently

- /api/v1/orders
- /api/v1/orders/{id}
- /api/v1/orders/{id}/send-to-kitchen
- /api/v1/orders/{id}/items
- /api/v1/orders/{id}/items/{item_id}
- /api/v1/kitchen/tickets
- /api/v1/kitchen/tickets/{id}/prepared

For payloads and responses, use docs/api-postman-guide.md §3.23–3.25.

## 4) Known Open Item

- JWT warning about short HMAC key can appear in tests when env key is too short.
- Recommendation: keep signing key >= 32 chars in local and CI env.

## 5) Where To Start Next (Phase 3 — Slice 3)

Complete Phase 3 with order lifecycle actions and waiter-level access.

### Step A: Order Status Actions
- POST /api/v1/orders/{id}/cancel
- POST /api/v1/orders/{id}/complete

### Step B: Waiter Permission Class
- Add `IsWaiterOrAbove` permission in `users/permissions.py` (roles: WAITER, CASHIER, MANAGER, OWNER)
- Waiters can create orders and add/update items, but cannot cancel or view billing

### Step C: Order number (order_no)
- Add `order_no` auto-increment field per branch (unique per branch per day, or sequential)
- Expose in OrderSerializer

### Step D: Tests
- Cancel and complete order actions
- Waiter permission tests

### Step E: Docs
- Update docs/api-postman-guide.md, backend-roadmap.md, session-handoff.md

## 6) Next Session Quick Commands

Run at session start:

```bash
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py test
```

## 7) Copy-Paste Prompt For Next Session

"Continue from docs/session-handoff.md. Implement Phase 3 Slice 3: order cancel/complete status actions, IsWaiterOrAbove permission class, and order_no field. Keep tenant/branch isolation strict. Run check + makemigrations --check --dry-run + tests and report changed files and endpoint list."

## 8) Definition Of Done For Next Session

- Cancel and complete order actions functional and tested.
- Waiter permission class in place.
- No pending migrations.
- All tests passing.
- Postman and roadmap docs updated in same change.
