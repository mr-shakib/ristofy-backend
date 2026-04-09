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
- Menu:
  - Categories and items CRUD.
  - Allergen catalog CRUD.
  - Item-allergen mapping.
  - Menu schedule windows CRUD.
  - Filtering + pagination on list APIs.
- Dining layout:
  - Floor plans and tables CRUD.
  - Reservations CRUD.
  - Reservation status actions (arrived/cancel).
  - Overlap protection for active reservations.
  - Waitlist CRUD + status actions (call/seat/cancel).
  - Table state sync (reservation/waitlist aware).

### Phase 3 (In Progress — Slice 1 Complete)
- Order and OrderItem models with full status lifecycle.
- POST /api/v1/orders — create order with items (snapshot name/price/vat from MenuItem).
- GET /api/v1/orders — list with branch/status/channel filters + pagination.
- GET /api/v1/orders/{id} — detail with nested items.
- PATCH /api/v1/orders/{id} — update order fields.
- POST /api/v1/orders/{id}/send-to-kitchen — transitions order to SENT_TO_KITCHEN, items to SENT.
- Tenant isolation enforced on all endpoints.
- 26 tests passing (16 prior + 10 new orders tests).

## 2) New Migrations In This Session

- orders/migrations/0001_initial.py

## 3) Current API Surface Added Recently

- /api/v1/orders
- /api/v1/orders/{id}
- /api/v1/orders/{id}/send-to-kitchen

For payloads and responses, use docs/api-postman-guide.md §3.23.

## 4) Known Open Item

- JWT warning about short HMAC key can appear in tests when env key is too short.
- Recommendation: keep signing key >= 32 chars in local and CI env.

## 5) Where To Start Next (Phase 3 — Slice 2)

Continue Phase 3 with order item management endpoints and kitchen ticket view.

### Step A: Order Item CRUD Sub-endpoints
- POST /api/v1/orders/{id}/items — add item to existing order
- PATCH /api/v1/orders/{id}/items/{item_id} — update item qty/notes
- DELETE /api/v1/orders/{id}/items/{item_id} — remove item

### Step B: Kitchen Tickets (basic)
- KitchenTicket model in orders app (or a new kitchen app if preferred)
- GET /api/v1/kitchen/tickets — list open tickets for branch
- POST /api/v1/kitchen/tickets/{id}/prepared — mark ticket as prepared

### Step C: Tests
- add-item to existing order
- update/delete item
- kitchen ticket listing and status transition
- permission checks

### Step D: Docs
- Update docs/api-postman-guide.md with new endpoints.
- Update docs/backend-roadmap.md phase 3 status.

## 6) Next Session Quick Commands

Run at session start:

```bash
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py test
```

## 7) Copy-Paste Prompt For Next Session

"Continue from docs/session-handoff.md. Implement Phase 3 Slice 2: order item sub-endpoints (add/update/delete items on existing orders) and basic kitchen ticket model + endpoints. Keep tenant/branch isolation strict. Run check + makemigrations --check --dry-run + tests and report changed files and endpoint list."

## 8) Definition Of Done For Next Session

- Order item management sub-endpoints functional and tested.
- Kitchen ticket model and basic endpoints implemented.
- No pending migrations.
- All tests passing.
- Postman and roadmap docs updated in same change.
